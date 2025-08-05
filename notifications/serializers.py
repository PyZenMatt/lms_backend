from rest_framework import serializers
from courses.models import Lesson, Exercise, ExerciseSubmission, Course
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    related_object = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'message', 'notification_type', 'read', 'created_at', 'related_object', 'link']
        ordering = ['-created_at']

    def get_link(self, obj):
        """Generate appropriate navigation links based on notification type"""
        try:
            # Reviews e Exercises
            if obj.notification_type == 'review_assigned' and obj.related_object_id:
                return f'/review/{obj.related_object_id}'
            elif obj.notification_type == 'exercise_graded' and obj.related_object_id:
                return f'/submission-graded/{obj.related_object_id}'
            
            # Corsi e Lezioni
            elif obj.notification_type in ['lesson_purchased', 'lesson_sold', 'new_lesson_added'] and obj.related_object_id:
                return f'/lezioni/{obj.related_object_id}'
            elif obj.notification_type in ['course_approved', 'course_purchased', 'course_sold', 'course_completed', 'new_course_published', 'course_updated'] and obj.related_object_id:
                return f'/corsi/{obj.related_object_id}'
            
            # TeoCoins e Rewards - redirect al profilo
            elif obj.notification_type in ['teocoins_earned', 'teocoins_spent', 'reward_earned', 'bonus_received']:
                return '/profile'
            
            # Achievements e Sistema
            elif obj.notification_type in ['achievement_unlocked', 'level_up']:
                return '/profile'
            
            # Default per notifiche di sistema
            elif obj.notification_type in ['system_message', 'welcome_message']:
                return '/dashboard/student'
            
            return None
        except Exception:
            return None

    def get_related_object(self, obj):
        try:
            if obj.notification_type == 'exercise_graded':
                submission = ExerciseSubmission.objects.get(id=obj.related_object_id)
                return {
                    'id': submission.id,
                    'exercise_title': submission.exercise.title,
                    'lesson_title': submission.exercise.lesson.title,
                    'submitted_at': submission.submitted_at
                }
            elif obj.notification_type in ['lesson_purchased', 'lesson_sold', 'new_lesson_added']:
                lesson = Lesson.objects.get(id=obj.related_object_id)
                return {
                    'id': lesson.id,
                    'title': lesson.title,
                    'price': getattr(lesson, 'price', None)
                }
            elif obj.notification_type in ['course_approved', 'course_purchased', 'course_sold', 'course_completed', 'new_course_published', 'course_updated']:
                course = Course.objects.get(id=obj.related_object_id)
                return {
                    'id': course.id,
                    'title': course.title,
                    'price': getattr(course, 'price', None),
                    'category': getattr(course, 'category', None)
                }
            elif obj.notification_type in ['teocoins_earned', 'teocoins_spent', 'reward_earned', 'bonus_received']:
                # Per le notifiche TeoCoin, related_object_id potrebbe essere l'amount o transaction_id
                return {
                    'amount': obj.related_object_id,
                    'type': obj.notification_type
                }
        except Exception as e:
            return None
        
