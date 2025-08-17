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
        🚨 SISTEMA SEMPLIFICATO: Reward fisso dal database (NO reward pool)
        """
        try:
            from services.db_teocoin_service import DBTeoCoinService
            db_service = DBTeoCoinService()
            
            # Verifica che non sia già stato premiato nel database TeoCoin
            from blockchain.models import DBTeoCoinTransaction
            existing_transaction = DBTeoCoinTransaction.objects.filter(
                user=submission.student,
                transaction_type='exercise_completion',
                related_object_id=str(submission.id)
            ).first()
            
            if existing_transaction:
                logger.info(f"Exercise {submission.id} già premiato per utente {submission.student.email}")
                return True  # Considera successo
            
            # REWARD FISSO: 2 TEO per ogni esercizio completato
            reward_amount = Decimal('2.0')
            
            # Accredita TeoCoin nel database
            success = db_service.add_balance(
                user=submission.student,
                amount=reward_amount,
                transaction_type='exercise_completion',
                description=f"Exercise completion reward: {submission.exercise.title}",
                related_object_id=str(submission.id)
            )
            
            if success:
                logger.info(
                    f"✅ Exercise reward awarded (DB): {reward_amount} TEO to {submission.student.email} "
                    f"for exercise {submission.exercise.title}"
                )
                return True
            else:
                logger.error(f"❌ Failed to credit exercise reward to {submission.student.email}")
                return False
            
        except Exception as e:
            logger.error(f"Error awarding exercise completion reward: {str(e)}")
            return False
    
    @classmethod
    @transaction.atomic
    def award_review_completion(cls, review):
        """
        🚨 SISTEMA SEMPLIFICATO: Reward fisso dal database per review (NO calcoli complessi)
        """
        try:
            from services.db_teocoin_service import DBTeoCoinService
            db_service = DBTeoCoinService()
            
            # Verifica che non sia già stato premiato nel database TeoCoin
            from blockchain.models import DBTeoCoinTransaction
            existing_transaction = DBTeoCoinTransaction.objects.filter(
                user=review.reviewer,
                transaction_type='review_completion',
                related_object_id=str(review.id)
            ).first()
            
            if existing_transaction:
                logger.info(f"Review {review.id} già premiata per reviewer {review.reviewer.email}")
                return True  # Considera successo
            
            # REWARD FISSO: 1 TEO per ogni review completata
            reviewer_reward = Decimal('1.0')
            
            # Accredita TeoCoin nel database
            success = db_service.add_balance(
                user=review.reviewer,
                amount=reviewer_reward,
                transaction_type='review_completion',
                description=f"Review completion reward for submission {review.submission.id}",
                related_object_id=str(review.id)
            )
            
            if success:
                logger.info(
                    f"✅ Review reward awarded (DB): {reviewer_reward} TEO to {review.reviewer.email} "
                    f"for reviewing submission {review.submission.id}"
                )
                return True
            else:
                logger.error(f"❌ Failed to credit review reward to {review.reviewer.email}")
                return False
            
        except Exception as e:
            logger.error(f"Error awarding review completion reward: {str(e)}")
            return False
    
    @classmethod
    def _transfer_from_reward_pool(cls, user, amount, teocoin_transaction, reason):
        """
        DEPRECATED: This method is no longer used as we moved to DB-based TeoCoin system.
        All reward distributions now happen via DBTeoCoinService directly.
        
        Kept for compatibility but will always use DB-based transactions.
        """
        logger.warning(f"_transfer_from_reward_pool called but using DB-based system instead: {reason}")
        
        # Simply create a transaction record for historical tracking
        try:
            blockchain_transaction = BlockchainTransaction.objects.create(
                user=user,
                transaction_type='db_transfer',  # Mark as DB-based
                amount=amount,
                to_address=getattr(user, 'wallet_address', None) or 'db_balance',
                related_teocoin_transaction=teocoin_transaction,
                status='completed',  # Always completed for DB transactions
                tx_hash=f"db_reward_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
                confirmed_at=timezone.now()
            )
            
            logger.info(f"Reward recorded in DB for user {user.email}: {amount} TEO")
            return blockchain_transaction
            
        except Exception as e:
            logger.error(f"Error recording DB-based reward: {str(e)}")
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


# Alias per compatibilità con codice esistente
class BlockchainRewards:
    """
    Alias per BlockchainRewardManager per compatibilità con codice esistente
    🚨 FORZA sempre l'uso del database per tutti i reward
    """
    
    @classmethod
    def calculate_exercise_reward(cls, submission):
        """Calcola il reward per un esercizio"""
        try:
            course = submission.exercise.lesson.course
            if not course:
                return Decimal('0')
            
            # Conta tutti gli esercizi del corso
            total_exercises = 0
            for lesson in course.lessons_in_course.all():
                total_exercises += lesson.exercises.count()
            
            if total_exercises == 0:
                return Decimal('0')
            
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
            
            return exercise_rewards[current_exercise_index]
            
        except Exception as e:
            logger.error(f"Error calculating exercise reward: {str(e)}")
            return Decimal('0')
    
    @classmethod
    def award_exercise_completion(cls, submission):
        """Alias per BlockchainRewardManager.award_exercise_completion"""
        return BlockchainRewardManager.award_exercise_completion(submission)
    
    @classmethod
    def award_review_completion(cls, review):
        """Alias per BlockchainRewardManager.award_review_completion"""
        return BlockchainRewardManager.award_review_completion(review)
