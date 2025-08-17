"""
Hybrid TeoCoin Service
Simplified wrapper around DB TeoCoin Service.
After cleanup, this just provides a clean interface to database operations.
"""

from services.db_teocoin_service import db_teocoin_service


class HybridTeoCoinService:
    """
    Simplified hybrid service that wraps the clean database TeoCoin service.
    All blockchain operations have been removed - this is now database-only.
    """
    
    def __init__(self):
        self.db_service = db_teocoin_service
    
    # ========== BALANCE OPERATIONS ==========
    
    def get_user_balance(self, user):
        """Get user's TeoCoin balance"""
        return self.db_service.get_user_balance(user)
    
    def get_available_balance(self, user):
        """Get user's available balance"""
        return self.db_service.get_available_balance(user)
    
    def get_staked_balance(self, user):
        """Get user's staked balance"""
        return self.db_service.get_staked_balance(user)
    
    def add_balance(self, user, amount, transaction_type, description="", course_id=None):
        """Add TeoCoin to user's balance"""
        return self.db_service.add_balance(
            user, amount, transaction_type, description, course_id
        )
    
    def deduct_balance(self, user, amount, transaction_type, description="", course_id=None):
        """Deduct TeoCoin from user's balance"""
        return self.db_service.deduct_balance(
            user, amount, transaction_type, description, course_id
        )
    
    # ========== STAKING OPERATIONS ==========
    
    def stake_tokens(self, user, amount):
        """Stake TeoCoin tokens"""
        return self.db_service.stake_tokens(user, amount)
    
    def unstake_tokens(self, user, amount):
        """Unstake TeoCoin tokens"""
        return self.db_service.unstake_tokens(user, amount)
    
    # ========== DISCOUNT SYSTEM ==========
    
    def calculate_discount(self, user, course_price):
        """Calculate TeoCoin discount for course"""
        return self.db_service.calculate_discount(user, course_price)
    
    def apply_course_discount(self, user, course_price, course_id, course_title=""):
        """Apply TeoCoin discount to course purchase"""
        return self.db_service.apply_course_discount(
            user, course_price, course_id, course_title
        )
    
    # ========== TEACHER REWARDS ==========
    
    def reward_teacher_lesson_completion(self, teacher, student, lesson_reward=None):
        """Reward teacher for lesson completion"""
        from decimal import Decimal
        if lesson_reward is None:
            lesson_reward = Decimal('1.0')
        return self.db_service.reward_teacher_lesson_completion(
            teacher, student, lesson_reward
        )
    
    # ========== WITHDRAWAL SYSTEM ==========
    
    def request_withdrawal(self, user, amount, metamask_address):
        """Request withdrawal to MetaMask"""
        return self.db_service.request_withdrawal(user, amount, metamask_address)
    
    def get_pending_withdrawals(self, user=None):
        """Get pending withdrawal requests"""
        return self.db_service.get_pending_withdrawals(user)
    
    # ========== TRANSACTION HISTORY ==========
    
    def get_user_transactions(self, user, limit=50):
        """Get user's transaction history"""
        return self.db_service.get_user_transactions(user, limit)
    
    # ========== PLATFORM STATISTICS ==========
    
    def get_platform_statistics(self):
        """Get platform-wide TeoCoin statistics"""
        return self.db_service.get_platform_statistics()


# Singleton instance
hybrid_teocoin_service = HybridTeoCoinService()
