from django.db import models
from users.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        # Acquisti e Vendite
        ('lesson_purchased', 'Acquisto Lezione'),
        ('course_purchased', 'Acquisto Corso'),
        ('course_sold', 'Corso Venduto'),
        ('lesson_sold', 'Lezione Venduta'),
        
        # Esercizi e Reviews
        ('exercise_graded', 'Esercizio Valutato'),
        ('review_assigned', 'Esercizio da valutare'),
        ('review_completed', 'Review Completata'),
        ('review_expired', 'Review scaduta'),
        ('review_replaced', 'Reviewer rimpiazzato'),
        
        # Corsi e Approvazioni
        ('course_completed', 'Corso Completato'),
        ('teacher_approved', 'Teacher approvato'),
        ('teacher_rejected', 'Teacher rifiutato'),
        ('course_approved', 'Corso approvato'),
        ('course_rejected', 'Corso rifiutato'),
        
        # TeoCoins e Rewards
        ('teocoins_earned', 'TeoCoins Guadagnati'),
        ('teocoins_spent', 'TeoCoins Spesi'),
        ('reward_earned', 'Premio Ottenuto'),
        ('bonus_received', 'Bonus Ricevuto'),
        
        # TeoCoin Escrow System
        ('teocoin_discount_pending', 'TeoCoin Discount - Teacher Decision Required'),
        ('teocoin_discount_accepted', 'TeoCoin Discount - Accepted by Teacher'),
        ('teocoin_discount_rejected', 'TeoCoin Discount - Rejected by Teacher'),
        ('teocoin_discount_expired', 'TeoCoin Discount - Expired (Auto-Rejected)'),
        
        # Nuovi Contenuti
        ('new_course_published', 'Nuovo Corso Pubblicato'),
        ('new_lesson_added', 'Nuova Lezione Aggiunta'),
        ('course_updated', 'Corso Aggiornato'),
        
        # Sistema e Achievement
        ('achievement_unlocked', 'Achievement Sbloccato'),
        ('level_up', 'Livello Aumentato'),
        ('system_message', 'Messaggio di Sistema'),
        ('welcome_message', 'Messaggio di Benvenuto'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notifica"
        verbose_name_plural = "Notifiche"