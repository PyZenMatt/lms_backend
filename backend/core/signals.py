"""
Core signal handlers for the TeoArt School Platform.

This module contains Django signal handlers that respond to model changes
and automatically trigger related actions like notifications, cache invalidation,
and business logic processing.

Signal Handlers:
    - handle_exercise_graded: Creates notifications when exercises are graded
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification
from courses.models import Exercise
import logging

logger = logging.getLogger('signals')


@receiver(post_save, sender=Exercise)
def handle_exercise_graded(sender, instance, created, **kwargs):
    """
    Create automatic notification when an exercise is graded.
    
    This signal handler is triggered whenever an Exercise model is saved,
    and creates a notification for the student when their exercise is reviewed.
    
    Args:
        sender: The model class (Exercise)
        instance: The actual Exercise instance that was saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    # Only create notification for reviewed exercises (not new ones)
    if not created and instance.status == 'reviewed' and instance.score is not None:
        try:
            Notification.objects.create(
                user=instance.student,
                message=f"Esercizio '{instance.lesson.title}' valutato: {instance.score}/100",
                notification_type='exercise_graded',
                related_object_id=instance.id
            )
            
            logger.info(
                f"Created exercise graded notification for user {instance.student.username}, "
                f"exercise {instance.id}, score: {instance.score}"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create exercise graded notification for exercise {instance.id}: {e}",
                exc_info=True
            )