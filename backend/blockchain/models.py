from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class UserWallet(models.Model):
    """
    User wallet model for managing blockchain wallet information.
    
    WARNING: This model stores private keys in plain text which is NOT secure
    for production use. Private keys should be encrypted or stored using a
    secure key management system (HSM, KMS, etc.).
    
    For production deployment, consider:
    - Using encrypted fields for private keys
    - Implementing HSM/KMS integration
    - Using deterministic wallet generation
    - Implementing proper key rotation
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='blockchain_wallet',
        help_text="User associated with this wallet"
    )
    address = models.CharField(
        max_length=42,
        unique=True,
        help_text="Public Ethereum/Polygon wallet address (0x...)"
    )
    private_key = models.CharField(
        max_length=66,
        help_text="Private key for wallet - SECURITY WARNING: stored in plain text!"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when wallet was created"
    )
    
    class Meta:
        verbose_name = "User Wallet"
        verbose_name_plural = "User Wallets"
        db_table = "blockchain_user_wallet"
    
    def __str__(self):
        return f"{self.user.username} - {self.address[:10]}..."
    
    def get_masked_private_key(self):
        """Return a masked version of the private key for display purposes."""
        if self.private_key:
            return f"{self.private_key[:6]}...{self.private_key[-4:]}"
        return "No private key"


class TeoCoinDiscountRequest(models.Model):
    """
    Model for tracking TeoCoin discount requests from students to teachers.
    
    Business Logic:
    1. Student requests discount by paying TEO tokens
    2. Teacher chooses between EUR commission or TEO staking
    3. System handles automatic expiration if teacher doesn't respond
    """
    
    STATUS_CHOICES = [
        (0, 'Pending'),      # Waiting for teacher decision
        (1, 'Approved'),     # Teacher accepted TEO tokens
        (2, 'Declined'),     # Teacher chose EUR commission
        (3, 'Expired'),      # Request expired, auto-EUR
    ]
    
    # Core identifiers
    student_address = models.CharField(
        max_length=42,
        help_text="Student's wallet address"
    )
    teacher_address = models.CharField(
        max_length=42,
        help_text="Teacher's wallet address"
    )
    course_id = models.PositiveIntegerField(
        help_text="ID of the course being purchased"
    )
    
    # Financial details (stored in smallest units for precision)
    course_price = models.PositiveIntegerField(
        help_text="Original course price in cents (EUR)"
    )
    discount_percent = models.PositiveIntegerField(
        help_text="Discount percentage in basis points (1000 = 10%)"
    )
    teo_cost = models.PositiveBigIntegerField(
        help_text="TEO tokens student pays (in wei, 18 decimals)"
    )
    teacher_bonus = models.PositiveBigIntegerField(
        help_text="Bonus TEO for teacher if accepted (in wei, 18 decimals)"
    )
    
    # Status and timing
    status = models.PositiveSmallIntegerField(
        choices=STATUS_CHOICES,
        default=0,
        help_text="Current status of the discount request"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the request was created"
    )
    expires_at = models.DateTimeField(
        help_text="When the request expires (auto-EUR)"
    )
    teacher_decision_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When teacher made their decision"
    )
    
    # Optional fields
    decline_reason = models.TextField(
        blank=True,
        help_text="Optional reason if teacher declined"
    )
    blockchain_tx_hash = models.CharField(
        max_length=66,
        blank=True,
        help_text="Transaction hash for blockchain operations"
    )
    
    class Meta:
        verbose_name = "TeoCoin Discount Request"
        verbose_name_plural = "TeoCoin Discount Requests"
        db_table = "blockchain_teocoin_discount_request"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_address', 'status']),
            models.Index(fields=['teacher_address', 'status']),
            models.Index(fields=['course_id']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Discount Request #{self.id} - Course {self.course_id} ({self.get_status_display()})"
    
    @property
    def is_expired(self):
        """Check if the request has expired"""
        return timezone.now() > self.expires_at
    
    @property
    def discount_amount_eur(self):
        """Calculate discount amount in EUR"""
        return (self.course_price * self.discount_percent) / (100 * 10000)  # cents to EUR, basis points to percent
    
    @property
    def final_price_eur(self):
        """Calculate final price student pays in EUR"""
        return (self.course_price / 100) - self.discount_amount_eur
    
    @property
    def teo_cost_formatted(self):
        """Format TEO cost for display"""
        return self.teo_cost / (10 ** 18)
    
    @property
    def teacher_bonus_formatted(self):
        """Format teacher bonus for display"""
        return self.teacher_bonus / (10 ** 18)
    
    def can_teacher_decide(self):
        """Check if teacher can still make a decision"""
        return self.status == 0 and not self.is_expired
    
    def mark_expired(self):
        """Mark request as expired"""
        if self.status == 0:  # Only if still pending
            self.status = 3
            self.teacher_decision_at = timezone.now()
            self.save()
            return True
        return False


# ===================================================================
# DB-BASED TEOCOIN SYSTEM - NEW MODELS
# ===================================================================

class DBTeoCoinBalance(models.Model):
    """
    Database-based TeoCoin balance for instant operations
    
    This replaces blockchain-based balances for internal platform operations.
    Users can still withdraw to MetaMask anytime via the withdrawal system.
    
    Note: Staking functionality is only available for teachers, not students.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='db_teocoin_balance'
    )
    
    # Balance tracking
    available_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="TEO available for spending (discounts for students, staking for teachers)"
    )
    
    staked_balance = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="TEO currently staked (Teachers only - affects commission rates)"
    )
    
    pending_withdrawal = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="TEO pending withdrawal to MetaMask"
    )
    
    # Metadata
    last_blockchain_sync = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "DB TeoCoin Balance"
        verbose_name_plural = "DB TeoCoin Balances"
        db_table = "blockchain_db_teocoin_balance"
    
    def __str__(self):
        return f"{self.user.email} - {self.total_balance} TEO"
    
    @property
    def total_balance(self):
        """Total TEO owned by user"""
        return self.available_balance + self.staked_balance + self.pending_withdrawal
    
    def can_stake(self):
        """Check if user can stake tokens (teachers only)"""
        return self.user.role == 'teacher'
    
    def stake_tokens(self, amount):
        """
        Move tokens from available to staked balance (teachers only)
        
        Args:
            amount (Decimal): Amount to stake
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If user is not a teacher or insufficient balance
        """
        if not self.can_stake():
            raise ValueError("Only teachers can stake TEO tokens")
        
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if self.available_balance < amount:
            raise ValueError(f"Insufficient balance. Available: {self.available_balance} TEO")
        
        self.available_balance -= amount
        self.staked_balance += amount
        return True
    
    def unstake_tokens(self, amount):
        """
        Move tokens from staked to available balance (teachers only)
        
        Args:
            amount (Decimal): Amount to unstake
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If user is not a teacher or insufficient staked balance
        """
        if not self.can_stake():
            raise ValueError("Only teachers can unstake TEO tokens")
        
        amount = Decimal(str(amount))
        
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        
        if self.staked_balance < amount:
            raise ValueError(f"Insufficient staked balance. Staked: {self.staked_balance} TEO")
        
        self.staked_balance -= amount
        self.available_balance += amount
        return True


class DBTeoCoinTransaction(models.Model):
    """
    Track all internal TeoCoin movements in the DB system
    """
    TRANSACTION_TYPES = [
        ('earned', 'Earned (Rewards/Teaching)'),
        ('spent_discount', 'Spent on Discount'),
        ('staked', 'Staked for Commission'),
        ('unstaked', 'Unstaked'),
        ('withdrawn', 'Withdrawn to MetaMask'),
        ('deposit', 'Deposited from MetaMask'),
        ('bonus', 'Platform Bonus'),
        ('migration', 'Migrated from Blockchain'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='db_teocoin_transactions'
    )
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField()
    
    # Related objects
    course = models.ForeignKey(
        'courses.Course', 
        null=True, blank=True, 
        on_delete=models.SET_NULL
    )
    related_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='related_teocoin_transactions',
        help_text="Other user involved (e.g., teacher in discount)"
    )
    
    # Blockchain integration
    blockchain_tx_hash = models.CharField(max_length=66, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "DB TeoCoin Transaction"
        verbose_name_plural = "DB TeoCoin Transactions"
        db_table = "blockchain_db_teocoin_transaction"
        indexes = [
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['blockchain_tx_hash']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount} TEO"


class TeoCoinWithdrawalRequest(models.Model):
    """
    Enhanced withdrawal request model for MetaMask integration
    Handles withdrawal from DB balance to blockchain via minting
    """
    WITHDRAWAL_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    metamask_address = models.CharField(max_length=42)
    status = models.CharField(max_length=20, choices=WITHDRAWAL_STATUS, default='pending')
    
    # Blockchain tracking
    transaction_hash = models.CharField(max_length=66, null=True, blank=True)
    gas_used = models.BigIntegerField(null=True, blank=True)
    gas_price_gwei = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    gas_cost_eur = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
    # Security and limits
    daily_withdrawal_count = models.IntegerField(default=1)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "TeoCoin Withdrawal Request"
        verbose_name_plural = "TeoCoin Withdrawal Requests"
        db_table = "blockchain_teocoin_withdrawal_request"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['metamask_address']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['daily_withdrawal_count']),
        ]
    
    def __str__(self):
        return f"Withdrawal #{self.id} - {self.user.email} - {self.amount} TEO - {self.status}"
    
    @property
    def is_processing_too_long(self):
        """Check if withdrawal has been processing for too long (>24h)"""
        if self.status == 'processing':
            return timezone.now() - self.created_at > timezone.timedelta(hours=24)
        return False
    
    @property
    def can_be_cancelled(self):
        """Check if withdrawal can be cancelled by user"""
        return self.status in ['pending', 'failed']
    
    @property
    def estimated_processing_time(self):
        """Estimated processing time for withdrawal"""
        if self.status == 'pending':
            return "5-10 minutes"
        elif self.status == 'processing':
            return "1-5 minutes"
        else:
            return "Completed"
