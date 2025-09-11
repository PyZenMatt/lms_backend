from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.db.models import Q
from users.models import User


class BlockchainTransaction(models.Model):
    """
    Modello per tracciare transazioni blockchain (mint, transfer, burn)
    """

    TRANSACTION_TYPES = (
        ("mint", "Mint - Crea nuovi token"),
        ("transfer", "Transfer - Trasferimento tra wallet"),
        ("burn", "Burn - Distruzione token"),
        ("course_purchase", "Course Purchase - Acquisto corso"),
        ("course_earned", "Course Earned - Guadagno insegnante"),
        ("reward", "Reward - Premio per attività"),
        ("exercise_reward", "Exercise Reward - Premio per esercizio completato"),
        ("review_reward", "Review Reward - Premio per review completata"),
    ("discount_applied", "Discount Applied - Sconto TeoCoin applicato"),
    ("discount_accept", "Discount Accept - Teacher accepted TEO"),
    )

    STATUS_CHOICES = (
        ("pending", "In Attesa"),
        ("confirmed", "Confermata"),
        ("completed", "Completata"),
        ("failed", "Fallita"),
    )

    # Dati transazione
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blockchain_transactions"
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    # Supporta decimali come blockchain
    amount = models.DecimalField(max_digits=18, decimal_places=8)

    # Dati blockchain
    from_address = models.CharField(max_length=42, blank=True, null=True)
    to_address = models.CharField(max_length=42, blank=True, null=True)
    tx_hash = models.CharField(max_length=66, unique=True, blank=True, null=True)
    # Additional transaction identifier
    transaction_hash = models.CharField(max_length=100, blank=True, null=True)
    block_number = models.PositiveIntegerField(blank=True, null=True)
    gas_used = models.PositiveIntegerField(blank=True, null=True)

    # Additional metadata for transactions
    related_object_id = models.CharField(
        max_length=100, blank=True, null=True
    )  # Course ID or other object ID
    notes = models.TextField(blank=True, null=True)  # Additional notes

    # Status e metadata
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    error_message = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} TEO - {self.status}"

    @property
    def explorer_url(self):
        """Link all'explorer Polygon per visualizzare la transazione"""
        if self.tx_hash:
            return f"https://amoy.polygonscan.com/tx/{self.tx_hash}"
        return None

    class Meta:
        verbose_name = "Transazione Blockchain"
        verbose_name_plural = "Transazioni Blockchain"
        ordering = ["-created_at"]


class TokenBalance(models.Model):
    """
    Cache del balance blockchain per performance
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="token_balance"
    )
    balance = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.balance} TEO"

    def is_stale(self, minutes=5):
        """Controlla se il balance è scaduto (default 5 minuti)"""
        return timezone.now() - self.last_updated > timedelta(minutes=minutes)

    class Meta:
        verbose_name = "Balance Token"
        verbose_name_plural = "Balance Token"





class TeacherDiscountAbsorption(models.Model):
    """
    Tracks opportunities for teachers to absorb student discounts in exchange for TEO
    Teachers have 24 hours to decide per transaction
    Database-based system - simpler than blockchain escrow
    """

    CHOICE_STATUS = [
        ("pending", "Pending Decision"),
        ("absorbed", "TEO Absorbed"),
        ("refused", "EUR Preferred"),
        ("expired", "Expired (Auto-EUR)"),
    ]

    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="discount_absorptions"
    )
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="generated_absorptions"
    )

    # Transaction details
    course_price_eur = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField()  # 5, 10, 15
    teo_used_by_student = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount_eur = models.DecimalField(max_digits=10, decimal_places=2)

    # Teacher commission calculation
    teacher_tier = models.IntegerField(default=0)  # 0=Bronze, 1=Silver, etc.
    # 50.00, 55.00, etc.
    teacher_commission_rate = models.DecimalField(max_digits=5, decimal_places=2)

    # Option A (Default EUR)
    option_a_teacher_eur = models.DecimalField(max_digits=10, decimal_places=2)
    option_a_platform_eur = models.DecimalField(max_digits=10, decimal_places=2)

    # Option B (Absorb Discount for TEO)
    option_b_teacher_eur = models.DecimalField(max_digits=10, decimal_places=2)
    option_b_teacher_teo = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # includes 25% bonus
    option_b_platform_eur = models.DecimalField(max_digits=10, decimal_places=2)

    # Decision tracking
    status = models.CharField(max_length=20, choices=CHOICE_STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 24 hours from creation
    decided_at = models.DateTimeField(null=True, blank=True)

    # Final payout (after decision or expiration)
    final_teacher_eur = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    final_teacher_teo = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    final_platform_eur = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    class Meta:
        db_table = "rewards_teacher_discount_absorption"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["teacher", "status"]),
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def time_remaining(self):
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - timezone.now()

    @property
    def hours_remaining(self):
        remaining = self.time_remaining
        if remaining.total_seconds() <= 0:
            return 0
        return round(remaining.total_seconds() / 3600, 1)

    def calculate_options(self):
        """Calculate both options for teacher choice"""
        # Option A: Standard commission, platform absorbs discount
        self.option_a_teacher_eur = (
            self.course_price_eur * self.teacher_commission_rate / 100
        )
        self.option_a_platform_eur = self.course_price_eur - self.option_a_teacher_eur

        # Option B: Teacher absorbs discount, gets TEO + 25% bonus
        self.option_b_teacher_eur = self.option_a_teacher_eur - self.discount_amount_eur
        self.option_b_teacher_teo = self.teo_used_by_student * Decimal(
            "1.25"
        )  # 25% bonus
        self.option_b_platform_eur = (
            self.option_a_platform_eur + self.discount_amount_eur
        )

    def make_choice(self, choice):
        """Process teacher's choice"""
        if self.status != "pending":
            raise ValueError("Choice already made or expired")

        if self.is_expired:
            self.auto_expire()
            return

        self.decided_at = timezone.now()

        if choice == "absorb":
            self.status = "absorbed"
            self.final_teacher_eur = self.option_b_teacher_eur
            self.final_teacher_teo = self.option_b_teacher_teo
            self.final_platform_eur = self.option_b_platform_eur
        else:  # refuse
            self.status = "refused"
            self.final_teacher_eur = self.option_a_teacher_eur
            self.final_teacher_teo = 0
            self.final_platform_eur = self.option_a_platform_eur

        self.save()

    def auto_expire(self):
        """Automatically expire to Option A after 24 hours"""
        self.status = "expired"
        self.decided_at = timezone.now()
        self.final_teacher_eur = self.option_a_teacher_eur
        self.final_teacher_teo = 0
        self.final_platform_eur = self.option_a_platform_eur
        self.save()

    def __str__(self):
        return f"Absorption {self.pk}: {self.teacher.username} - {self.course.title} ({self.status})"


class TeacherPayoutSummary(models.Model):
    """
    Monthly/Weekly payout summaries for admin dashboard
    """

    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    period_type = models.CharField(
        max_length=10, choices=[("weekly", "Weekly"), ("monthly", "Monthly")]
    )

    # Summary totals
    total_eur_earned = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    total_teo_earned = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    total_discounts_absorbed = models.IntegerField(default=0)
    total_transactions = models.IntegerField(default=0)

    # Breakdown
    eur_from_standard_sales = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    eur_from_absorbed_discounts = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    teo_from_absorbed_discounts = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rewards_teacher_payout_summary"
        unique_together = ["teacher", "period_start", "period_end", "period_type"]
        ordering = ["-period_start"]

    def __str__(self):
        return f"{self.teacher.username} - {self.period_type} {self.period_start} to {self.period_end}"


class Tier(models.Model):
    """
    Staking tier configuration used for discount calculations and teacher splits.
    Stored here to allow auditing of snapshot tier values per transaction.
    """

    name = models.CharField(max_length=50, unique=True)
    min_stake_teo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    # Percent values (0..100). Teacher gets teacher_split_percent% of gross price.
    teacher_split_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("50.00")
    )
    platform_split_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("50.00")
    )
    max_accept_discount_ratio = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal("1.00"))
    teo_bonus_multiplier = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1.25"))
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rewards_tier"
        ordering = ["-min_stake_teo"]

    def __str__(self):
        return f"{self.name} (min {self.min_stake_teo} TEO)"


class PaymentDiscountSnapshot(models.Model):
    """
    Snapshot of discount breakdown for a single payment/order.
    This is an immutable audit record created at Confirm time.
    """

    # Stable identifiers for idempotency: external payment provider id (eg. Stripe PI)
    # and an optional platform order id. At least one should be present for stable
    # deduplication. Keep order_id for backwards compatibility but not strictly
    # unique at DB level here to allow older rows; uniqueness is enforced via
    # conditional UniqueConstraint below.
    external_txn_id = models.CharField(max_length=120, db_index=True, null=True, blank=True)
    order_id = models.CharField(max_length=120, db_index=True, null=True, blank=True)
    
    # Idempotency key for discount application (prevents double TEO deduction)
    # Format: "{user_id}_{course_id}_{checkout_session_id}"
    idempotency_key = models.CharField(max_length=200, db_index=True, null=True, blank=True)
    
    # Checkout session identifier - persists across multiple attempts within same session
    checkout_session_id = models.CharField(max_length=120, db_index=True, null=True, blank=True)
    
    # Stripe correlation fields for webhook capture
    stripe_checkout_session_id = models.CharField(max_length=200, db_index=True, null=True, blank=True, help_text="Stripe Checkout Session ID for webhook correlation")
    stripe_payment_intent_id = models.CharField(max_length=200, db_index=True, null=True, blank=True, help_text="Stripe Payment Intent ID for webhook correlation")
    
    source = models.CharField(max_length=16, default="local")  # 'local' | 'stripe'
    course = models.ForeignKey("courses.Course", on_delete=models.SET_NULL, null=True)
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="payment_snapshots")
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="teacher_payment_snapshots")

    # Inputs
    price_eur = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.IntegerField()
    # Flat discount amount (5/10/15 EUR) - authoritative source for opportunities
    discount_amount_eur = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    # Outputs (EUR)
    student_pay_eur = models.DecimalField(max_digits=10, decimal_places=2)
    teacher_eur = models.DecimalField(max_digits=10, decimal_places=2)
    platform_eur = models.DecimalField(max_digits=10, decimal_places=2)

    # Outputs (TEO)
    teacher_teo = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    platform_teo = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))

    absorption_policy = models.CharField(max_length=32, default="none")
    teacher_accepted_teo = models.DecimalField(max_digits=18, decimal_places=8, default=Decimal("0"))
    
    # Link to opportunity/decision (if applicable)
    decision = models.OneToOneField(
        "courses.TeacherDiscountDecision",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_snapshot"
    )

    # Finalization fields updated when teacher makes a decision
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("applied", "Applied (Pending Payment)"),
        ("confirmed", "Confirmed"),
        ("failed", "Failed"),
        ("expired", "Expired"),
        ("superseded", "Superseded"),
        ("pending", "Pending"),  # Legacy status for backward compatibility
        ("closed", "Closed"),   # Legacy status for backward compatibility
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    
    # Wallet transaction tracking for TEO holds/captures
    wallet_hold_id = models.CharField(max_length=100, null=True, blank=True, help_text="TEO wallet hold transaction ID")
    wallet_capture_id = models.CharField(max_length=100, null=True, blank=True, help_text="TEO wallet capture transaction ID")
    
    # Timestamps for state transitions
    applied_at = models.DateTimeField(null=True, blank=True, help_text="When discount was applied (hold created)")
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text="When payment confirmed (hold captured)")
    failed_at = models.DateTimeField(null=True, blank=True, help_text="When payment failed (hold released)")
    
    closed_at = models.DateTimeField(null=True, blank=True)
    # Final teacher teo recorded at decision time (quantized to 8 decimals)
    final_teacher_teo = models.DecimalField(max_digits=18, decimal_places=8, null=True, blank=True, default=Decimal("0"))

    # Snapshot of tier at time of transaction
    tier_name = models.CharField(max_length=50, null=True, blank=True)
    tier_teacher_split_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tier_platform_split_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tier_max_accept_discount_ratio = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    tier_teo_bonus_multiplier = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rewards_payment_discount_snapshot"
        ordering = ["-created_at"]
        constraints = [
            # If external_txn_id is present, it must be unique
            models.UniqueConstraint(
                fields=["external_txn_id"],
                name="uniq_snapshot_by_external_txn",
                condition=~models.Q(external_txn_id=None),
            ),
            # If order_id is present, it must be unique
            models.UniqueConstraint(
                fields=["order_id"],
                name="uniq_snapshot_by_order_id",
                condition=~models.Q(order_id=None),
            ),
            # IDEMPOTENCY CONSTRAINT: Prevent duplicate discount applications for same session
            # Key: user + course + checkout_session_id must be unique for active statuses
            models.UniqueConstraint(
                fields=["student", "course", "checkout_session_id"],
                name="uniq_discount_per_checkout_session",
                condition=Q(
                    checkout_session_id__isnull=False,
                    status__in=["applied", "confirmed"]
                ),
            ),
            # Legacy idempotency: prevent duplicate discount applications while snapshot is pending
            # Allow same idempotency_key for historical/closed snapshots but prevent
            # concurrent/pending duplicates.
            models.UniqueConstraint(
                fields=["idempotency_key"],
                name="uniq_snapshot_by_idempotency_key_pending",
                condition=Q(idempotency_key__isnull=False) & Q(status="pending"),
            ),
        ]

    def __str__(self):
        return f"Snapshot {self.order_id} - {self.price_eur}€ ({self.discount_percent}%)"
