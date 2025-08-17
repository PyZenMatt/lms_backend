from django.db import transaction
from django.core.exceptions import ValidationError
from users.models import User
from courses.models import Course
from rewards.models import BlockchainTransaction

# Import BlockchainService for new architecture
from services.blockchain_service import blockchain_service

class TransactionService:
    @classmethod
    @transaction.atomic
    def purchase_course(cls, user: User, course: Course):
        """
        Acquisto corso con gestione transazionale blockchain
        :raises: ValidationError
        """
        # Use BlockchainService for balance check
        try:
            balance = blockchain_service.get_user_balance(user)
            if balance < course.price:
                raise ValidationError("Saldo TeoCoin insufficiente")
        except Exception:
            # Fallback to user model balance if blockchain service fails
            if user.teo_coins < course.price:
                raise ValidationError("Saldo TeoCoin insufficiente")

        # Lock ottimistico sull'utente
        user = User.objects.select_for_update().get(pk=user.pk)
        
        # Use BlockchainService for transaction
        try:
            # Try blockchain-based purchase
            result = blockchain_service.transfer_tokens_between_users(
                from_user=user,
                to_user=course.teacher,  # Assuming course has teacher
                amount=course.price,
                reason=f"Course purchase: {course.title}"
            )
            
            if not result.get('success'):
                raise ValidationError(f"Blockchain transaction failed: {result.get('error')}")
                
        except Exception as e:
            # Fallback to traditional model-based transaction
            user.teo_coins -= course.price
            user.save(update_fields=['teo_coins'])
        
        course.students.add(user)
        
        # Registrazione transazione blockchain
        BlockchainTransaction.objects.create(
            user=user,
            amount=course.price,
            transaction_type='course_purchase',
            status='pending'
        )

        # Invia segnale per notifiche/aggiornamenti secondari
        from django.db.models.signals import post_save
        post_save.send(
            sender=Course,
            instance=course,
            created=False,
            update_fields=['students']
        )

    @classmethod
    @transaction.atomic
    def transfer_teocoins(cls, sender: User, receiver: User, amount: int):
        """Transfer con lock su entrambi gli utenti"""
        if amount <= 0:
            raise ValidationError("Importo non valido")

        # Lock sugli utenti coinvolti
        sender = User.objects.select_for_update().get(pk=sender.pk)
        receiver = User.objects.select_for_update().get(pk=receiver.pk)

        # Use BlockchainService for balance check and transaction
        try:
            result = blockchain_service.transfer_tokens_between_users(
                from_user=sender,
                to_user=receiver,
                amount=float(amount),
                reason="TeoCoin transfer between users"
            )
            
            if not result.get('success'):
                raise ValidationError(f"Transfer failed: {result.get('error')}")
                
        except Exception as e:
            # Fallback to traditional model-based transaction
            # Note: This assumes User model has teo_coins field
            # if sender.teo_coins < amount:
            #     raise ValidationError("Saldo insufficiente")
            # sender.teo_coins -= amount  
            # receiver.teo_coins += amount
            # sender.save(update_fields=['teo_coins'])
            # receiver.save(update_fields=['teo_coins'])
            raise ValidationError(f"Transfer service unavailable: {str(e)}")

        # Registrazione transazioni blockchain
        BlockchainTransaction.objects.bulk_create([
            BlockchainTransaction(
                user=sender,
                amount=amount,
                transaction_type='transfer_out',
                status='pending'
            ),
            BlockchainTransaction(
                user=receiver,
                amount=amount,
                transaction_type='transfer_in',
                status='pending'
            )
        ])