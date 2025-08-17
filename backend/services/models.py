"""
Services App Models

This module contains database models used by the services layer.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class DiscountRequest(models.Model):
    """Model for tracking gas-free discount requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    # Request details
    student_address = models.CharField(max_length=42, help_text="Student's wallet address")
    teacher_address = models.CharField(max_length=42, help_text="Teacher's wallet address")
    course_id = models.PositiveIntegerField(help_text="Course ID for discount")
    course_price = models.PositiveIntegerField(help_text="Course price in EUR cents")
    discount_percent = models.PositiveIntegerField(help_text="Discount percentage (5-15)")
    teo_cost = models.DecimalField(max_digits=12, decimal_places=2, help_text="TEO cost for discount")
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    student_signature = models.CharField(max_length=132, help_text="Student's message signature")
    platform_tx_hash = models.CharField(max_length=66, blank=True, help_text="Platform transaction hash")
    teacher_decision_reason = models.TextField(blank=True, help_text="Teacher's reason for decision")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    teacher_responded_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="Request expiration time")
    
    # On-chain data
    contract_request_id = models.PositiveIntegerField(null=True, blank=True, help_text="Contract request ID")
    gas_cost_matic = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True, help_text="Platform gas cost in MATIC")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student_address', 'status']),
            models.Index(fields=['teacher_address', 'status']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-set expiration time (24 hours from creation)
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def __str__(self):
        return f"DiscountRequest {self.id}: {self.student_address[:10]}... -> {self.teacher_address[:10]}... ({self.status})"


class StakingActivity(models.Model):
    """Model for tracking teacher staking activities"""
    ACTIVITY_TYPES = [
        ('stake', 'Stake Tokens'),
        ('unstake', 'Unstake Tokens'),
        ('tier_update', 'Tier Update'),
    ]
    
    teacher_address = models.CharField(max_length=42, help_text="Teacher's wallet address")
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    teo_amount = models.DecimalField(max_digits=18, decimal_places=8, help_text="TEO amount involved")
    previous_tier = models.CharField(max_length=20, blank=True, help_text="Previous staking tier")
    new_tier = models.CharField(max_length=20, help_text="New staking tier")
    platform_tx_hash = models.CharField(max_length=66, help_text="Platform transaction hash")
    gas_cost_matic = models.DecimalField(max_digits=10, decimal_places=6, help_text="Platform gas cost in MATIC")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher_address', 'activity_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"StakingActivity {self.id}: {self.teacher_address[:10]}... {self.activity_type} ({self.teo_amount} TEO)"


class PlatformGasExpense(models.Model):
    """Model for tracking platform gas expenses"""
    EXPENSE_TYPES = [
        ('student_approval', 'Student Approval'),
        ('discount_creation', 'Discount Creation'),
        ('discount_approval', 'Discount Approval'),
        ('teacher_staking', 'Teacher Staking'),
        ('teacher_unstaking', 'Teacher Unstaking'),
        ('batch_operations', 'Batch Operations'),
    ]
    
    expense_type = models.CharField(max_length=30, choices=EXPENSE_TYPES)
    transaction_hash = models.CharField(max_length=66, unique=True, help_text="Transaction hash")
    gas_used = models.PositiveIntegerField(help_text="Gas units used")
    gas_price_gwei = models.DecimalField(max_digits=10, decimal_places=2, help_text="Gas price in Gwei")
    total_cost_matic = models.DecimalField(max_digits=10, decimal_places=6, help_text="Total cost in MATIC")
    total_cost_usd = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True, help_text="Total cost in USD")
    related_address = models.CharField(max_length=42, blank=True, help_text="Related user address")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expense_type', 'created_at']),
            models.Index(fields=['related_address']),
        ]
    
    def __str__(self):
        return f"GasExpense {self.id}: {self.expense_type} - {self.total_cost_matic} MATIC"


class PlatformAllowance(models.Model):
    """Model for tracking platform allowances given to students"""
    student_address = models.CharField(max_length=42, unique=True, help_text="Student's wallet address")
    total_allowance = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total TEO allowance given")
    used_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="TEO allowance used")
    remaining_allowance = models.DecimalField(max_digits=12, decimal_places=2, help_text="TEO allowance remaining")
    last_topped_up = models.DateTimeField(null=True, blank=True, help_text="Last top-up timestamp")
    approval_tx_hash = models.CharField(max_length=66, blank=True, help_text="Initial approval transaction")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['student_address']),
            models.Index(fields=['remaining_allowance']),
        ]
    
    def save(self, *args, **kwargs):
        # Auto-calculate remaining allowance
        self.remaining_allowance = self.total_allowance - self.used_allowance
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Allowance {self.student_address[:10]}...: {self.remaining_allowance}/{self.total_allowance} TEO"
