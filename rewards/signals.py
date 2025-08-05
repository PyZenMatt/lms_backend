from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache
from django.utils import timezone
from .models import BlockchainTransaction
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=BlockchainTransaction)
def invalidate_user_balance_cache(sender, instance, **kwargs):
    """
    Svuota la cache del saldo TeoCoin di un utente ogni volta che
    una transazione blockchain viene creata, modificata o eliminata.
    """
    cache_key = f"user_balance_{instance.user_id}"
    cache.delete(cache_key)

@receiver(post_save, sender=BlockchainTransaction)
def create_blockchain_notification(sender, instance, created, **kwargs):
    """
    Crea notifiche automatiche per tutte le transazioni blockchain completate
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
        # Converti l'amount in un intero positivo per related_object_id
        # Se l'amount è negativo, usa il valore assoluto
        related_id = None
        if instance.amount is not None:
            try:
                # Converti a intero e usa valore assoluto per rispettare PositiveIntegerField
                related_id = int(abs(float(instance.amount)))
            except (ValueError, TypeError):
                # Se la conversione fallisce, lascia None
                related_id = None
        
        Notification.objects.create(
            user=instance.user,
            message=message,
            notification_type=notification_type,
            related_object_id=related_id
        )

# ========== AUTOMATIC REWARD PROCESSING ==========

@receiver(post_save, sender=BlockchainTransaction)
def auto_process_reward_transaction(sender, instance, created, **kwargs):
    """
    Automatically process reward transactions when they are created
    """
    if not created:
        return
    
    # Only process reward transactions
    if instance.transaction_type not in ['exercise_reward', 'review_reward']:
        return
    
    # Only process pending transactions
    if instance.status != 'pending':
        return
    
    logger.info(f"Auto-processing reward transaction {instance.id} for {instance.user.username}")
    
    try:
        # Import here to avoid circular imports
        from blockchain.blockchain import TeoCoinService
        
        # Check if user has wallet address
        if not instance.user.wallet_address:
            logger.warning(f"User {instance.user.username} has no wallet address for transaction {instance.id}")
            instance.status = 'failed'
            instance.error_message = 'User has no wallet address'
            instance.save(update_fields=['status', 'error_message'])
            return
        
        # Mint tokens to user's wallet
        description = f"{instance.transaction_type.replace('_', ' ').title()} - {instance.notes}"
        
        try:
            teocoin_service = TeoCoinService()
            tx_hash = teocoin_service.mint_tokens(
                instance.user.wallet_address,
                instance.amount
            )
            
            if tx_hash:
                # Update transaction with success
                instance.status = 'completed'
                instance.tx_hash = tx_hash
                instance.transaction_hash = tx_hash
                instance.confirmed_at = timezone.now()
                instance.save(update_fields=['status', 'tx_hash', 'transaction_hash', 'confirmed_at'])
                
                logger.info(f"✅ Auto-processed reward transaction {instance.id} - TX Hash: {tx_hash}")
            else:
                # Mark as failed
                instance.status = 'failed'
                instance.error_message = 'Blockchain transaction failed - no tx hash returned'
                instance.save(update_fields=['status', 'error_message'])
                
                logger.error(f"❌ Failed to auto-process reward transaction {instance.id} - no tx hash returned")
                
        except Exception as blockchain_error:
            # Mark as failed with error
            instance.status = 'failed'
            instance.error_message = f'Blockchain error: {str(blockchain_error)}'
            instance.save(update_fields=['status', 'error_message'])
            
            logger.error(f"❌ Blockchain error processing transaction {instance.id}: {blockchain_error}")
            # Don't re-raise the exception - let the review complete successfully
            
    except Exception as e:
        logger.error(f"❌ Unexpected error auto-processing transaction {instance.id}: {e}")
        instance.status = 'failed'
        instance.error_message = f'Processing error: {str(e)}'
        instance.save(update_fields=['status', 'error_message'])
        # Don't re-raise the exception - let the review complete successfully


# ========== BLOCKCHAIN REWARD SIGNALS ==========

from .blockchain_rewards import BlockchainRewardManager
from courses.models import ExerciseSubmission, ExerciseReview


@receiver(post_save, sender=ExerciseSubmission)
def handle_exercise_submission_approval(sender, instance, created, **kwargs):
    """
    DEPRECATO: Sistema di reward legacy disabilitato.
    I reward vengono ora gestiti direttamente in courses/views/exercises.py
    quando tutte le review sono completate.
    """
    # Sistema disabilitato per evitare duplicazioni
    # I reward sono ora gestiti nella ReviewExerciseView
    pass


@receiver(post_save, sender=ExerciseReview)
def handle_review_completion(sender, instance, created, **kwargs):
    """
    Quando una review viene completata, assegna automaticamente i reward al reviewer
    """
    # Solo per review completate con score
    if instance.score is not None and instance.reviewed_at:
        try:
            # Verifica che non sia già stata processata
            existing_transaction = BlockchainTransaction.objects.filter(
                user=instance.reviewer,
                transaction_type='review_reward',
                related_object_id=str(instance.id)
            ).exists()
            
            if not existing_transaction:
                logger.info(f"Processing blockchain reward for completed review {instance.id}")
                BlockchainRewardManager.award_review_completion(instance)
            else:
                logger.debug(f"Review {instance.id} already has reward transaction")
                
        except Exception as e:
            logger.error(f"Error processing review completion reward: {str(e)}")


@receiver(pre_save, sender=ExerciseReview)
def update_review_timestamp(sender, instance, **kwargs):
    """
    Aggiorna il timestamp reviewed_at quando viene assegnato un score
    """
    if instance.score is not None and not instance.reviewed_at:
        instance.reviewed_at = timezone.now()


# Signal per debug e monitoring
@receiver(post_save, sender=BlockchainTransaction)
def log_blockchain_transaction(sender, instance, created, **kwargs):
    """
    Log delle transazioni blockchain per monitoring
    """
    if created:
        logger.info(
            f"New blockchain transaction created: {instance.transaction_type} - "
            f"{instance.amount} TEO for user {instance.user.email}"
        )
    
    elif instance.status == 'confirmed':
        logger.info(
            f"Blockchain transaction confirmed: {instance.tx_hash} - "
            f"{instance.amount} TEO for user {instance.user.email}"
        )
    
    elif instance.status == 'failed':
        logger.error(
            f"Blockchain transaction failed: {instance.error_message} - "
            f"{instance.amount} TEO for user {instance.user.email}"
        )
