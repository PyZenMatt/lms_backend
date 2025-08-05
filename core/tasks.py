# ✅ OTTIMIZZATO - Celery background tasks for heavy operations
from celery import shared_task
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_user_progress_report(self, user_id):
    """
    Generate detailed progress report for a user - run in background
    """
    try:
        from users.models import User, UserProgress
        from courses.models import CourseEnrollment, LessonCompletion
        
        user = User.objects.get(id=user_id)
        user_progress, created = UserProgress.objects.get_or_create(user=user)
        
        # Calculate detailed statistics
        enrollments = CourseEnrollment.objects.filter(student=user).select_related('course')
        
        total_courses = enrollments.count()
        completed_courses = enrollments.filter(completed=True).count()
        
        # Calculate total lessons and completed lessons
        total_lessons = 0
        completed_lessons = 0
        
        for enrollment in enrollments:
            course_lessons = enrollment.course.lessons.count()
            total_lessons += course_lessons
            
            completed_course_lessons = LessonCompletion.objects.filter(
                student=user,
                lesson__course=enrollment.course
            ).count()
            completed_lessons += completed_course_lessons
        
        # Update user progress
        user_progress.total_courses_enrolled = total_courses
        user_progress.total_courses_completed = completed_courses
        user_progress.total_lessons_completed = completed_lessons
        user_progress.last_activity_date = timezone.now()
        user_progress.save()
        
        # Clear related cache
        cache.delete(f'student_dashboard_{user_id}')
        cache.delete(f'student_batch_data_{user_id}')
        
        logger.info(f"Progress report generated for user {user_id}")
        
        return {
            'user_id': user_id,
            'total_courses': total_courses,
            'completed_courses': completed_courses,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons
        }
        
    except Exception as exc:
        logger.error(f"Error generating progress report for user {user_id}: {exc}")
        raise self.retry(countdown=60, exc=exc)


@shared_task(bind=True, max_retries=3)
def calculate_teacher_statistics(self, teacher_id):
    """
    Calculate detailed statistics for a teacher - run in background
    """
    try:
        from users.models import User
        from courses.models import Course, CourseEnrollment
        from rewards.models import TeoCoinTransaction
        
        teacher = User.objects.get(id=teacher_id, role='teacher')
        
        # Get teacher's courses with student counts
        courses = Course.objects.filter(teacher=teacher).annotate(
            student_count=Count('enrollments')
        )
        
        # Calculate totals
        total_courses = courses.count()
        total_students = CourseEnrollment.objects.filter(
            course__teacher=teacher
        ).values('student').distinct().count()
        
        # Calculate earnings
        from django.db import models
        total_earnings = TeoCoinTransaction.objects.filter(
            user=teacher,
            transaction_type='course_earned'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Monthly earnings
        start_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_earnings = TeoCoinTransaction.objects.filter(
            user=teacher,
            transaction_type='course_earned',
            created_at__gte=start_of_month
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or 0
        
        # Clear teacher dashboard cache
        cache.delete(f'teacher_dashboard_{teacher_id}')
        
        logger.info(f"Statistics calculated for teacher {teacher_id}")
        
        return {
            'teacher_id': teacher_id,
            'total_courses': total_courses,
            'total_students': total_students,
            'total_earnings': float(total_earnings),
            'monthly_earnings': float(monthly_earnings)
        }
        
    except Exception as exc:
        logger.error(f"Error calculating teacher statistics for {teacher_id}: {exc}")
        raise self.retry(countdown=60, exc=exc)


@shared_task(bind=True)
def warm_cache_for_popular_courses(self):
    """
    Pre-warm cache for the most popular courses
    """
    try:
        from courses.models import Course
        from django.db.models import Count
        
        # Get top 10 most popular courses
        popular_courses = Course.objects.filter(
            is_approved=True
        ).annotate(
            enrollment_count=Count('enrollments')
        ).order_by('-enrollment_count')[:10]
        
        warmed_count = 0
        
        for course in popular_courses:
            # Pre-generate course batch data for cache
            cache_key = f'course_popular_data_{course.pk}'
            
            if not cache.get(cache_key):
                course_data = {
                    'id': course.pk,
                    'title': course.title,
                    'description': course.description,
                    'enrollment_count': getattr(course, 'enrollment_count', 0),
                    'lessons_count': course.lessons.count()
                }
                
                # Cache for 1 hour
                cache.set(cache_key, course_data, 3600)
                warmed_count += 1
        
        logger.info(f"Cache warmed for {warmed_count} popular courses")
        return {'warmed_courses': warmed_count}
        
    except Exception as exc:
        logger.error(f"Error warming cache for popular courses: {exc}")
        raise exc


@shared_task(bind=True)
def cleanup_old_cache_keys(self):
    """
    Clean up old/unused cache keys (if using Redis)
    """
    try:
        from django.core.cache import cache
        from django.conf import settings
        
        if hasattr(settings, 'CACHES') and 'redis' in str(settings.CACHES.get('default', {})):
            # If using Redis, we can clean up expired keys
            # This is a placeholder - actual implementation depends on Redis setup
            logger.info("Cache cleanup task executed")
            return {'status': 'completed'}
        else:
            logger.info("Cache cleanup skipped - not using Redis")
            return {'status': 'skipped'}
            
    except Exception as exc:
        logger.error(f"Error during cache cleanup: {exc}")
        raise exc


@shared_task(bind=True, max_retries=2)
def send_progress_notification(self, user_id, achievement_type, details):
    """
    Send progress notification to user - run in background
    """
    try:
        from users.models import User
        from notifications.models import Notification
        
        user = User.objects.get(id=user_id)
        
        # Create notification based on achievement type
        messages = {
            'course_completed': f"🎓 Congratulazioni! Hai completato il corso '{details.get('course_title', '')}'",
            'lesson_completed': f"✅ Hai completato la lezione '{details.get('lesson_title', '')}'",
            'milestone_reached': f"🏆 Hai raggiunto il traguardo: {details.get('milestone', '')}"
        }
        
        message = messages.get(achievement_type, "🎉 Hai fatto dei progressi!")
        
        Notification.objects.create(
            user=user,
            message=message,
            notification_type=achievement_type,
            related_object_id=details.get('object_id')
        )
        
        # Clear notification cache
        cache.delete(f'student_dashboard_{user_id}')
        cache.delete(f'student_batch_data_{user_id}')
        
        logger.info(f"Progress notification sent to user {user_id}")
        return {'user_id': user_id, 'notification_type': achievement_type}
        
    except Exception as exc:
        logger.error(f"Error sending notification to user {user_id}: {exc}")
        raise self.retry(countdown=30, exc=exc)
