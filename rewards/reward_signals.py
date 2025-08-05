# rewards/signals.py - Enhanced with automated rewards
"""
Enhanced signal handlers for automated reward system
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification
from rewards.models import BlockchainTransaction
from courses.models import LessonCompletion, CourseEnrollment
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=LessonCompletion)
def handle_lesson_completion_reward(sender, instance, created, **kwargs):
    """
    Automatically reward student when they complete a lesson
    """
    if not created:
        return
        
    try:
        from rewards.automation import reward_system
        
        lesson = instance.lesson
        student = instance.student
        course = lesson.course
        
        if course:
            # Award lesson completion reward
            reward_system.reward_lesson_completion(student, lesson, course)
            
            # Check if this completion triggers course completion
            reward_system.check_and_reward_course_completion(student, course)
            
            # Check for achievements
            completed_courses = CourseEnrollment.objects.filter(
                student=student, 
                completed=True
            ).count()
            
            if completed_courses == 1:
                # First course completed achievement
                reward_system.award_achievement(student, 'first_course_completed', course)
                
    except Exception as e:
        logger.error(f"Error in lesson completion reward handler: {e}")


@receiver(post_save, sender=CourseEnrollment)
def handle_course_enrollment_update(sender, instance, created, **kwargs):
    """
    Handle course enrollment status changes
    """
    if not created and instance.completed:
        try:
            from rewards.automation import reward_system
            
            # This is triggered when enrollment.completed is set to True
            # The completion bonus is already handled in the automation system
            # This is just for additional tracking/notifications
            
            logger.info(f"Course enrollment completed: {instance.student.username} -> {instance.course.title}")
            
        except Exception as e:
            logger.error(f"Error in course enrollment handler: {e}")


@receiver(post_save, sender=BlockchainTransaction)
def create_teocoin_notification(sender, instance, created, **kwargs):
    """
    Crea notifiche automatiche per tutte le transazioni TeoCoin
    """
    if not created:
        return
    
    notification_type = None
    message = ""
    
    # Determina il tipo di notifica e il messaggio in base al tipo di transazione
    if instance.transaction_type in ['earned', 'exercise_reward', 'review_reward', 'achievement_reward', 'bonus'] and instance.amount > 0:
        notification_type = 'teocoins_earned'
        if instance.transaction_type == 'exercise_reward':
            message = f"🎉 Hai guadagnato {instance.amount} TeoCoins per la valutazione del tuo esercizio!"
        elif instance.transaction_type == 'review_reward':
            message = f"⭐ Hai guadagnato {instance.amount} TeoCoins per aver completato una review!"
        elif instance.transaction_type == 'achievement_reward':
            message = f"🏆 Hai guadagnato {instance.amount} TeoCoins per un achievement sbloccato!"
        elif instance.transaction_type == 'lesson_completion_reward':
            message = f"📚 Hai guadagnato {instance.amount} TeoCoins per aver completato una lezione!"
        elif instance.transaction_type == 'course_completion_bonus':
            message = f"🎓 Hai guadagnato {instance.amount} TeoCoins per aver completato un corso!"
        elif instance.transaction_type == 'bonus':
            message = f"🎁 Hai ricevuto un bonus di {instance.amount} TeoCoins!"
        else:
            message = f"💰 Hai guadagnato {instance.amount} TeoCoins!"
            
    elif instance.transaction_type in ['course_earned', 'lesson_earned'] and instance.amount > 0:
        notification_type = 'teocoins_earned'
        if instance.transaction_type == 'course_earned':
            message = f"📚 Hai guadagnato {instance.amount} TeoCoins dalla vendita di un corso!"
        else:
            message = f"📖 Hai guadagnato {instance.amount} TeoCoins dalla vendita di una lezione!"
            
    elif instance.transaction_type in ['spent', 'course_purchase', 'lesson_purchase'] and instance.amount < 0:
        notification_type = 'teocoins_spent'
        if instance.transaction_type == 'course_purchase':
            message = f"🛒 Hai speso {abs(instance.amount)} TeoCoins per acquistare un corso!"
        elif instance.transaction_type == 'lesson_purchase':
            message = f"🛒 Hai speso {abs(instance.amount)} TeoCoins per acquistare una lezione!"
        else:
            message = f"💸 Hai speso {abs(instance.amount)} TeoCoins!"
            
    elif instance.transaction_type == 'refund' and instance.amount > 0:
        notification_type = 'bonus_received'
        message = f"↩️ Hai ricevuto un rimborso di {instance.amount} TeoCoins!"
        
    elif instance.transaction_type == 'penalty' and instance.amount < 0:
        notification_type = 'teocoins_spent'
        message = f"⚠️ Ti sono stati detratti {abs(instance.amount)} TeoCoins per una penalità!"
    
    # Crea la notifica se abbiamo un tipo valido
    if notification_type and message:
        Notification.objects.create(
            user=instance.user,
            message=message,
            notification_type=notification_type,
            related_object_id=instance.amount  # Usiamo l'amount come related_object_id per le notifiche TeoCoin
        )
