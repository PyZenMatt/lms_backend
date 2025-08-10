# ✅ OTTIMIZZATO - Batch API endpoints to reduce multiple frontend calls
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Prefetch
from django.core.cache import cache
from courses.models import Course, Lesson, CourseEnrollment, LessonCompletion
from courses.serializers import CourseSerializer, LessonSerializer
from users.models import UserProgress
from users.serializers import UserProgressSerializer
from notifications.models import Notification
from notifications.serializers import NotificationSerializer


class StudentBatchDataAPI(APIView):
    """
    ✅ OPTIMIZED - Single endpoint to get all student data instead of multiple API calls
    Combines: courses, progress, notifications, recent activity
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Cache key for this user's batch data
        cache_key = f'student_batch_data_{user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        # ✅ OPTIMIZED - Single query for enrolled courses with progress
        enrolled_courses = Course.objects.filter(
            enrollments__student=user, is_approved=True
        ).select_related('teacher').prefetch_related(
            'lessons',
            Prefetch(
                'lessons__completions',
                queryset=LessonCompletion.objects.filter(student=user),
                to_attr='user_completions'
            )
        ).annotate(
            total_lessons=Count('lessons'),
            completed_lessons=Count('lessons__completions', filter=Q(lessons__completions__student=user))
        )

        # Serialize courses data
        courses_data = []
        for course in enrolled_courses:
            course_data = CourseSerializer(course, context={'request': request}).data
            course_data['progress'] = {
                'total_lessons': course.total_lessons,
                'completed_lessons': course.completed_lessons,
                'percentage': round((course.completed_lessons / course.total_lessons * 100) if course.total_lessons > 0 else 0, 2)
            }
            courses_data.append(course_data)

        # ✅ OPTIMIZED - User progress data
        user_progress, created = UserProgress.objects.get_or_create(user=user)
        progress_data = UserProgressSerializer(user_progress, context={'request': request}).data

        # ✅ OPTIMIZED - Recent notifications
        notifications = Notification.objects.filter(
            user=user, read=False
        ).order_by('-created_at')[:10]
        notifications_data = NotificationSerializer(notifications, many=True).data

        # ✅ OPTIMIZED - Recent activity summary
        recent_completions = LessonCompletion.objects.filter(
            student=user
        ).select_related('lesson', 'lesson__course').order_by('-completed_at')[:5]

        recent_activity = []
        for completion in recent_completions:
            recent_activity.append({
                'id': completion.pk,
                'type': 'lesson_completed',
                'title': completion.lesson.title,
                'course_title': completion.lesson.course.title if completion.lesson.course else None,
                'date': completion.completed_at
            })

        data = {
            'courses': courses_data,
            'progress': progress_data,
            'notifications': notifications_data,
            'recent_activity': recent_activity,
            'summary': {
                'total_courses': len(courses_data),
                'unread_notifications': len(notifications_data),
                'recent_completions': len(recent_activity)
            }
        }

        # Cache for 3 minutes
        cache.set(cache_key, data, 180)
        
        return Response(data)


class CourseBatchDataAPI(APIView):
    """
    ✅ OPTIMIZED - Single endpoint to get course data with lessons and user progress
    Combines: course details, lessons list, user progress, completion status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        cache_key = f'course_batch_data_{course_id}_{request.user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        try:
            # ✅ OPTIMIZED - Single query with all related data
            course = Course.objects.select_related('teacher').prefetch_related(
                'lessons',
                'lessons__exercises',
                Prefetch(
                    'lessons__completions',
                    queryset=LessonCompletion.objects.filter(student=request.user),
                    to_attr='user_completions'
                )
            ).get(id=course_id, is_approved=True)
            
            # Check if user is enrolled
            is_enrolled = CourseEnrollment.objects.filter(
                student=request.user, course=course
            ).exists()
            
            if not is_enrolled:
                return Response({'error': 'Not enrolled in this course'}, status=403)

        except Course.DoesNotExist:
            return Response({'error': 'Course not found'}, status=404)

        # Serialize course data
        course_data = CourseSerializer(course, context={'request': request}).data

        # ✅ OPTIMIZED - Lessons with completion status
        lessons_data = []
        total_lessons = course.lessons.count()
        completed_count = 0

        for lesson in course.lessons.all():
            lesson_data = LessonSerializer(lesson, context={'request': request}).data
            
            # Check if user completed this lesson
            is_completed = bool(lesson.user_completions)
            if is_completed:
                completed_count += 1
            
            lesson_data['completed'] = is_completed
            lesson_data['exercises_count'] = lesson.exercises.count()
            lessons_data.append(lesson_data)

        # Calculate progress
        progress_percentage = round((completed_count / total_lessons * 100) if total_lessons > 0 else 0, 2)

        data = {
            'course': course_data,
            'lessons': lessons_data,
            'progress': {
                'total_lessons': total_lessons,
                'completed_lessons': completed_count,
                'percentage': progress_percentage,
                'is_completed': completed_count == total_lessons and total_lessons > 0
            },
            'enrollment': {
                'is_enrolled': is_enrolled,
                'can_access': True
            }
        }

        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        
        return Response(data)


class LessonBatchDataAPI(APIView):
    """
    ✅ OPTIMIZED - Single endpoint to get lesson data with exercises and completion status
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        cache_key = f'lesson_batch_data_{lesson_id}_{request.user.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)

        try:
            # ✅ OPTIMIZED - Single query with related data
            lesson = Lesson.objects.select_related('course', 'course__teacher').prefetch_related(
                'exercises'
            ).get(id=lesson_id)
            
            # Check course access
            if lesson.course and not lesson.course.is_approved:
                if not (request.user.is_staff or request.user.is_superuser or lesson.course.teacher == request.user):
                    return Response({'error': 'Course not approved'}, status=403)
            
            # Check enrollment if course exists
            if lesson.course:
                is_enrolled = CourseEnrollment.objects.filter(
                    student=request.user, course=lesson.course
                ).exists()
                
                if not is_enrolled and lesson.course.teacher != request.user:
                    return Response({'error': 'Not enrolled in this course'}, status=403)

        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=404)

        # Serialize lesson data
        lesson_data = LessonSerializer(lesson, context={'request': request}).data

        # Check completion status
        is_completed = LessonCompletion.objects.filter(
            student=request.user, lesson=lesson
        ).exists()

        # ✅ OPTIMIZED - Exercises data
        exercises_data = []
        for exercise in lesson.exercises.all():
            exercises_data.append({
                'id': exercise.id,
                'title': exercise.title,
                'description': exercise.description,
                'exercise_type': exercise.exercise_type if hasattr(exercise, 'exercise_type') else None,
                'difficulty': exercise.difficulty if hasattr(exercise, 'difficulty') else None
            })

        data = {
            'lesson': lesson_data,
            'exercises': exercises_data,
            'completion': {
                'is_completed': is_completed,
                'exercises_count': len(exercises_data)
            },
            'navigation': {
                'course_id': lesson.course.id if lesson.course else None,
                'course_title': lesson.course.title if lesson.course else None
            }
        }

        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        
        return Response(data)
