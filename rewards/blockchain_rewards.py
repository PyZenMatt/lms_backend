"""
Blockchain Reward System
Gestisce il minting automatico di TeoCoin per premi ed esercizi
"""

import random
import logging
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone

from .models import BlockchainTransaction
from courses.models import Course, Exercise, ExerciseSubmission, ExerciseReview

# Import BlockchainService for new architecture
from services.blockchain_service import blockchain_service


logger = logging.getLogger(__name__)


class BlockchainRewardCalculator:
    """
    Calcola e distribuisce premi in TeoCoin usando la blockchain
    
    Logica:
    - Ogni corso può premiare fino a un massimo del 10% del suo prezzo (configurabile)
    - I premi vengono distribuiti tra tutti gli esercizi del corso
    - La distribuzione è casuale ma bilanciata (ogni esercizio riceve almeno qualcosa)
    - I reviewer ricevono il 5% del premio dell'esercizio che hanno valutato
    """
    
    # Configurazione percentuali (modificabili per corso)
    DEFAULT_MAX_EXERCISE_REWARD_PERCENTAGE = 0.10  # Max 10% del costo corso
    DEFAULT_MIN_EXERCISE_REWARD_PERCENTAGE = 0.03  # Min 3% del costo corso  
    DEFAULT_REVIEWER_REWARD_PERCENTAGE = 0.05      # 5% del premio dell'esercizio
    
    @classmethod
    def get_course_reward_config(cls, course):
        """
        Ottiene la configurazione reward per un corso specifico
        (in futuro può essere personalizzata per corso)
        """
        return {
            'max_percentage': getattr(course, 'max_exercise_reward_percentage', cls.DEFAULT_MAX_EXERCISE_REWARD_PERCENTAGE),
            'min_percentage': getattr(course, 'min_exercise_reward_percentage', cls.DEFAULT_MIN_EXERCISE_REWARD_PERCENTAGE),
            'reviewer_percentage': getattr(course, 'reviewer_reward_percentage', cls.DEFAULT_REVIEWER_REWARD_PERCENTAGE)
        }
    
    @classmethod
    def calculate_course_reward_pool(cls, course):
        """
        Calcola il pool totale di reward per un corso
        
        Esempio: Corso da 30€
        - Min 3% = 0.9€ 
        - Max 10% = 3€
        - Percentuale casuale tra 3% e 10%
        """
        config = cls.get_course_reward_config(course)
        
        # Percentuale casuale tra min e max
        percentage = random.uniform(
            config['min_percentage'], 
            config['max_percentage']
        )
        
        total_pool = Decimal(course.price) * Decimal(str(percentage))
        return total_pool.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)  # Precisione a 3 decimali
    
    @classmethod
    def distribute_exercise_rewards(cls, course, exercise_count):
        """
        Distribuisce i reward tra gli esercizi di un corso
        
        Assicura che:
        1. Ogni esercizio riceva almeno 0.001 TEO (mai 0)
        2. La distribuzione sia casuale ma bilanciata
        3. La somma corrisponda al pool totale
        
        Esempio: Corso 30€ con 3 esercizi, pool 3€
        - Possibili distribuzioni: [1.5, 1.0, 0.5], [2.0, 0.7, 0.3], [0.8, 1.8, 0.4] etc.
        - Mai: [3.0, 0, 0] perché ogni esercizio deve avere almeno qualcosa
        """
        if exercise_count == 0:
            return []
        
        total_pool = cls.calculate_course_reward_pool(course)
        
        if exercise_count == 1:
            return [total_pool]
        
        # Minimo garantito per esercizio
        min_per_exercise = Decimal('0.001')
        guaranteed_minimum = min_per_exercise * exercise_count
        
        if total_pool <= guaranteed_minimum:
            # Se il pool è troppo piccolo, distribuisci equamente
            per_exercise = total_pool / exercise_count
            return [per_exercise.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)] * exercise_count
        
        # Pool disponibile dopo aver garantito il minimo
        distributable_pool = total_pool - guaranteed_minimum
        
        # Genera pesi casuali per la distribuzione
        weights = [random.uniform(0.1, 1.0) for _ in range(exercise_count)]
        total_weight = sum(weights)
        
        # Distribuisce il pool rimanente in base ai pesi
        rewards = []
        distributed = Decimal('0')
        
        for i, weight in enumerate(weights):
            if i == len(weights) - 1:  # Ultimo esercizio prende il resto per garantire somma esatta
                remaining = total_pool - distributed
                rewards.append(remaining.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))
            else:
                # Minimo garantito + quota proporzionale del distributable
                proportional_share = (distributable_pool * Decimal(str(weight / total_weight)))
                exercise_reward = min_per_exercise + proportional_share
                exercise_reward = exercise_reward.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                rewards.append(exercise_reward)
                distributed += exercise_reward
        
        # Verifica che la somma sia corretta (aggiusta eventuali errori di arrotondamento)
        total_distributed = sum(rewards)
        if total_distributed != total_pool:
            # Aggiusta l'ultimo reward per correggere errori di arrotondamento
            difference = total_pool - total_distributed
            rewards[-1] += difference
            rewards[-1] = rewards[-1].quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        
        return rewards
    
    @classmethod
    def calculate_reviewer_reward(cls, exercise_reward_amount, course=None):
        """
        Calcola il premio per il reviewer (5% del premio dell'esercizio)
        
        Args:
            exercise_reward_amount: Importo del premio dell'esercizio
            course: Corso di riferimento (per future personalizzazioni)
        """
        # Usa la configurazione del corso o il default
        reviewer_percentage = cls.DEFAULT_REVIEWER_REWARD_PERCENTAGE
        if course:
            config = cls.get_course_reward_config(course)
            reviewer_percentage = config['reviewer_percentage']
        
        reviewer_reward = Decimal(str(exercise_reward_amount)) * Decimal(str(reviewer_percentage))
        return reviewer_reward.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)


class BlockchainRewardManager:
    """
    Gestisce l'assegnazione effettiva dei premi blockchain
    """
    
    @classmethod
    @transaction.atomic
    def award_exercise_completion(cls, submission):
        """
        Assegna premio per completamento esercizio con minting blockchain
        """
        try:
            # Verifica che non sia già stato premiato
            existing_transaction = BlockchainTransaction.objects.filter(
                user=submission.student,
                transaction_type='exercise_reward',
                related_object_id=str(submission.id)
            ).first()
            
            if existing_transaction:
                logger.info(f"Exercise {submission.id} già premiato per utente {submission.student.email}")
                return None
            
            # Calcola il premio per questo esercizio specifico
            course = submission.exercise.lesson.course
            if not course:
                logger.error(f"Corso non trovato per esercizio {submission.exercise.id}")
                return None
            
            # Conta tutti gli esercizi del corso
            total_exercises = 0
            for lesson in course.lessons_in_course.all():
                total_exercises += lesson.exercises.count()
            
            if total_exercises == 0:
                logger.error(f"Nessun esercizio trovato per corso {course.id}")
                return None
            
            # Distribuisce i reward tra tutti gli esercizi
            exercise_rewards = BlockchainRewardCalculator.distribute_exercise_rewards(
                course, total_exercises
            )
            
            # Trova l'indice dell'esercizio corrente
            exercise_index = 0
            current_exercise_index = 0
            for lesson in course.lessons_in_course.all():
                for exercise in lesson.exercises.all():
                    if exercise.id == submission.exercise.id:
                        current_exercise_index = exercise_index
                        break
                    exercise_index += 1
            
            reward_amount = exercise_rewards[current_exercise_index]
            
            # Crea la transazione blockchain
            blockchain_transaction = BlockchainTransaction.objects.create(
                user=submission.student,
                amount=reward_amount,
                transaction_type='exercise_reward',
                status='pending',
                related_object_id=str(submission.id),
                notes=f"Exercise reward for: {submission.exercise.title}"
            )
            
            # Aggiorna il reward_amount nella submission
            submission.reward_amount = int(reward_amount * 1000)  # Supporta 3 decimali
            submission.save()
            
            # Use BlockchainService for token transfer
            try:
                result = blockchain_service.mint_tokens_to_user(
                    user=submission.student,
                    amount=reward_amount,
                    reason=f"Exercise reward for: {submission.exercise.title}"
                )
                
                if result.get('success'):
                    logger.info(f"Exercise reward transferred successfully: {reward_amount} TeoCoin to {submission.student.username}")
                    return blockchain_transaction
                else:
                    logger.error(f"Exercise reward transfer failed: {result.get('error')}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error transferring exercise reward: {str(e)}")
                return None
            
            # # Effettua il trasferimento dalla reward pool
            # blockchain_tx = cls._transfer_from_reward_pool(
            #     user=submission.student,
            #     amount=reward_amount,
            #     blockchain_transaction=blockchain_transaction,
            #     reason=f"Exercise completion reward: {submission.exercise.title}"
            # )
            
            logger.info(
                f"Exercise reward awarded: {reward_amount} TEO to {submission.student.email} "
                f"for exercise {submission.exercise.title}"
            )
            
            return blockchain_tx
            
        except Exception as e:
            logger.error(f"Error awarding exercise completion reward: {str(e)}")
            raise
    
    @classmethod
    @transaction.atomic
    def award_review_completion(cls, review):
        """
        Assegna premio per completamento review con minting blockchain
        """
        try:
            # Verifica che non sia già stato premiato
            existing_transaction = BlockchainTransaction.objects.filter(
                user=review.reviewer,
                transaction_type='review_reward',
                related_object_id=str(review.id)
            ).first()
            
            if existing_transaction:
                logger.info(f"Review {review.id} già premiata per reviewer {review.reviewer.email}")
                return None
            
            # Ottiene il premio dell'esercizio originale
            submission = review.submission
            if not submission.reward_amount:
                logger.error(f"Submission {submission.id} non ha reward_amount impostato")
                return None
            
            # Calcola il 5% del premio dell'esercizio
            exercise_reward = Decimal(submission.reward_amount) / Decimal('1000')  # Riconverte da millesimi
            course = submission.exercise.lesson.course
            reviewer_reward = BlockchainRewardCalculator.calculate_reviewer_reward(exercise_reward, course)
            
            # Crea la transazione blockchain
            blockchain_transaction = BlockchainTransaction.objects.create(
                user=review.reviewer,
                amount=reviewer_reward,
                transaction_type='review_reward',
                status='pending',
                related_object_id=str(review.id),
                notes=f"Review reward for submission {submission.id}"
            )
            
            # Use BlockchainService for reviewer reward transfer
            try:
                result = blockchain_service.mint_tokens_to_user(
                    user=review.reviewer,
                    amount=reviewer_reward,
                    reason=f"Review reward for exercise: {submission.exercise.title}"
                )
                
                if result.get('success'):
                    logger.info(f"Review reward transferred successfully: {reviewer_reward} TeoCoin to {review.reviewer.username}")
                    return blockchain_transaction
                else:
                    logger.error(f"Review reward transfer failed: {result.get('error')}")
                    return None
                    
            except Exception as e:
                logger.error(f"Error transferring review reward: {str(e)}")
                return None
            
            # # Effettua il trasferimento dalla reward pool
            # blockchain_tx = cls._transfer_from_reward_pool(
            #     user=review.reviewer,
            #     amount=reviewer_reward,
            #     blockchain_transaction=blockchain_transaction,
            #     reason=f"Review reward for exercise: {submission.exercise.title}"
            # )
            
            logger.info(
                f"Review reward awarded: {reviewer_reward} TEO to {review.reviewer.email} "
                f"for reviewing exercise {submission.exercise.title}"
            )
            
            return blockchain_tx
            
        except Exception as e:
            logger.error(f"Error awarding review completion reward: {str(e)}")
            raise
    
    @classmethod
    def _transfer_from_reward_pool(cls, user, amount, teocoin_transaction, reason):
        """
        Effettua il trasferimento dalla reward pool per un utente specifico
        """
        try:
            # Importa il servizio blockchain
            from blockchain.blockchain import teocoin_service
            
            # Ottiene l'indirizzo wallet dell'utente
            wallet_address = getattr(user, 'wallet_address', None)
            if not wallet_address:
                logger.error(f"User {user.email} non ha wallet address configurato")
                return None
            
            # Crea la transazione blockchain
            blockchain_transaction = BlockchainTransaction.objects.create(
                user=user,
                transaction_type='transfer',
                amount=amount,
                to_address=wallet_address,
                related_teocoin_transaction=teocoin_transaction,
                status='pending'
            )
            
            # Effettua il trasferimento dalla reward pool
            try:
                # OBSOLETE: Old blockchain transfer from reward pool
                # tx_hash = teocoin_service.transfer_from_reward_pool(wallet_address, amount)
                # Using DB-based system instead
                tx_hash = f"db_transfer_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                
                if tx_hash:
                    blockchain_transaction.tx_hash = tx_hash
                    blockchain_transaction.status = 'confirmed'
                    blockchain_transaction.confirmed_at = timezone.now()
                    blockchain_transaction.save()
                    
                    logger.info(f"Blockchain transfer from reward pool successful: {tx_hash}")
                else:
                    raise Exception("Transfer failed - no transaction hash returned")
                
            except Exception as blockchain_error:
                blockchain_transaction.status = 'failed'
                blockchain_transaction.error_message = str(blockchain_error)
                blockchain_transaction.save()
                
                logger.error(f"Blockchain transfer from reward pool failed: {str(blockchain_error)}")
                raise
            
            return blockchain_transaction
            
        except Exception as e:
            logger.error(f"Error in _transfer_from_reward_pool: {str(e)}")
            raise


def setup_course_reward_system(course):
    """
    Utility function per configurare il sistema di reward per un nuovo corso
    """
    try:
        # Conta tutti gli esercizi del corso
        total_exercises = 0
        for lesson in course.lessons_in_course.all():
            total_exercises += lesson.exercises.count()
        
        if total_exercises == 0:
            logger.warning(f"Corso {course.title} non ha esercizi configurati")
            return
        
        # Calcola e logga la distribuzione dei reward
        reward_pool = BlockchainRewardCalculator.calculate_course_reward_pool(course)
        exercise_rewards = BlockchainRewardCalculator.distribute_exercise_rewards(
            course, total_exercises
        )
        
        logger.info(
            f"Course {course.title} reward system configured:\n"
            f"- Total reward pool: {reward_pool} TEO\n"
            f"- Exercise rewards: {exercise_rewards}\n"
            f"- Total exercises: {total_exercises}"
        )
        
        return {
            'total_pool': reward_pool,
            'exercise_rewards': exercise_rewards,
            'total_exercises': total_exercises
        }
        
    except Exception as e:
        logger.error(f"Error setting up course reward system: {str(e)}")
        raise
