# ✅ OTTIMIZZATO - Cache invalidation signals to maintain data consistency
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.core.cache import cache
from courses.models import Course, Lesson, LessonCompletion, CourseEnrollment
from rewards.models import BlockchainTransaction
from notifications.models import Notification
from users.models import UserProgress


@receiver([post_save, post_delete], sender=LessonCompletion)
def invalidate_student_cache_on_lesson_completion(sender, instance, **kwargs):
    """Invalidate student cache when lesson completion changes"""
    user_id = instance.student.id
    
    # Clear student dashboard cache
    cache.delete(f'student_dashboard_{user_id}')
    cache.delete(f'student_batch_data_{user_id}')
    
    # Clear course batch data cache
    if instance.lesson.course:
        cache.delete(f'course_batch_data_{instance.lesson.course.id}_{user_id}')
    
    # Clear lesson batch data cache
    cache.delete(f'lesson_batch_data_{instance.lesson.id}_{user_id}')


@receiver([post_save, post_delete], sender=CourseEnrollment)
def invalidate_student_cache_on_enrollment(sender, instance, **kwargs):
    """Invalidate student cache when course enrollment changes"""
    user_id = instance.student.id
    course_id = instance.course.id
    
    # Clear student dashboard and batch data cache
    cache.delete(f'student_dashboard_{user_id}')
    cache.delete(f'student_batch_data_{user_id}')
    cache.delete(f'course_batch_data_{course_id}_{user_id}')
    
    # Clear teacher dashboard cache (affects student count)
    if instance.course.teacher:
        cache.delete(f'teacher_dashboard_{instance.course.teacher.id}')


@receiver([post_save, post_delete], sender=BlockchainTransaction)
def invalidate_dashboard_cache_on_transaction(sender, instance, **kwargs):
    """Invalidate dashboard cache when blockchain transactions change"""
    user_id = instance.user.id
    
    # Clear user dashboard cache
    cache.delete(f'student_dashboard_{user_id}')
    cache.delete(f'teacher_dashboard_{user_id}')
    cache.delete(f'student_batch_data_{user_id}')


@receiver([post_save, post_delete], sender=Notification)
def invalidate_cache_on_notification(sender, instance, **kwargs):
    """Invalidate cache when notifications change"""
    user_id = instance.user.id
    
    # Clear dashboard cache that includes notifications
    cache.delete(f'student_dashboard_{user_id}')
    cache.delete(f'student_batch_data_{user_id}')


@receiver([post_save, post_delete], sender=Course)
def invalidate_cache_on_course_change(sender, instance, **kwargs):
    """Invalidate cache when course data changes"""
    # Clear teacher dashboard cache
    if instance.teacher:
        cache.delete(f'teacher_dashboard_{instance.teacher.id}')
    
    # Clear course-specific cache for all enrolled students
    enrollments = CourseEnrollment.objects.filter(course=instance)
    for enrollment in enrollments:
        cache.delete(f'student_dashboard_{enrollment.student.id}')
        cache.delete(f'student_batch_data_{enrollment.student.id}')
        cache.delete(f'course_batch_data_{instance.id}_{enrollment.student.id}')


@receiver([post_save, post_delete], sender=Lesson)
def invalidate_cache_on_lesson_change(sender, instance, **kwargs):
    """Invalidate cache when lesson data changes"""
    # Clear lesson-specific cache
    lesson_id = instance.id
    
    # Clear for all students who might access this lesson
    if instance.course:
        enrollments = CourseEnrollment.objects.filter(course=instance.course)
        for enrollment in enrollments:
            cache.delete(f'lesson_batch_data_{lesson_id}_{enrollment.student.id}')
            cache.delete(f'course_batch_data_{instance.course.id}_{enrollment.student.id}')


@receiver(m2m_changed, sender=Course.students.through)
def invalidate_cache_on_course_students_change(sender, instance, action, pk_set, **kwargs):
    """Invalidate cache when course students change (many-to-many)"""
    if action in ['post_add', 'post_remove', 'post_clear']:
        # Clear teacher dashboard cache
        cache.delete(f'teacher_dashboard_{instance.teacher.id}')
        
        # Clear student cache for affected students
        if pk_set:
            for student_id in pk_set:
                cache.delete(f'student_dashboard_{student_id}')
                cache.delete(f'student_batch_data_{student_id}')
                cache.delete(f'course_batch_data_{instance.id}_{student_id}')


@receiver([post_save, post_delete], sender=UserProgress)
def invalidate_cache_on_user_progress_change(sender, instance, **kwargs):
    """Invalidate cache when user progress changes"""
    user_id = instance.user.id
    
    # Clear student cache
    cache.delete(f'student_dashboard_{user_id}')
    cache.delete(f'student_batch_data_{user_id}')
