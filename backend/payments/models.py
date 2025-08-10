from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal


class TeacherDiscountDecision(models.Model):
    """
    Track teacher decisions on TeoCoin discount requests
    """
    DECISION_CHOICES = [
        ('pending', 'Pending Decision'),
        ('accepted', 'Accepted TeoCoin'),
        ('declined', 'Declined TeoCoin'),
        ('expired', 'Decision Expired')
    ]
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_decisions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discount_requests')
    course_title = models.CharField(max_length=255)
    
    # Financial details
    course_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.IntegerField()
    teo_cost = models.BigIntegerField(help_text="TEO cost in wei (18 decimals)")
    teacher_bonus = models.BigIntegerField(help_text="Teacher bonus in wei (18 decimals)")
    
    # Commission calculation snapshot
    teacher_commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission rate at time of request")
    teacher_staking_tier = models.CharField(max_length=20, help_text="Staking tier at time of request")
    
    # Decision tracking
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES, default='pending')
    decision_made_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="When the decision expires")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Transaction tracking
    student_transaction_hash = models.CharField(max_length=66, blank=True, null=True)
    teacher_payment_completed = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['teacher', 'decision']),
            models.Index(fields=['student', 'created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.student.email} → {self.teacher.email}: {self.course_title} ({self.decision})"
    
    @property
    def teo_cost_display(self):
        """Convert wei to TEO for display"""
        return self.teo_cost / 10**18
    
    @property
    def teacher_bonus_display(self):
        """Convert wei to TEO for display"""
        return self.teacher_bonus / 10**18
    
    @property
    def discounted_price(self):
        """Calculate the discounted course price"""
        return self.course_price * (Decimal('100') - Decimal(str(self.discount_percentage))) / Decimal('100')
    
    @property
    def teacher_earnings_if_accepted(self):
        """Calculate teacher earnings if they accept TeoCoin"""
        fiat_amount = self.discounted_price * (Decimal('1') - (self.teacher_commission_rate / Decimal('100')))
        teo_amount = (self.teo_cost + self.teacher_bonus) / 10**18
        return {
            'fiat': fiat_amount,
            'teo': teo_amount,
            'total_teo': teo_amount
        }
    
    @property
    def teacher_earnings_if_declined(self):
        """Calculate teacher earnings if they decline TeoCoin"""
        fiat_amount = self.course_price * (Decimal('1') - (self.teacher_commission_rate / Decimal('100')))
        return {
            'fiat': fiat_amount,
            'teo': Decimal('0'),
            'total_teo': Decimal('0')
        }
    
    @property
    def is_expired(self):
        """Check if the decision period has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def clean(self):
        """Validate the model data"""
        if self.teacher.role != 'teacher':
            raise ValidationError('Teacher must have teacher role')
        if self.student.role != 'student':
            raise ValidationError('Student must have student role')
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError('Discount percentage must be between 0 and 100')
        if self.course_price <= 0:
            raise ValidationError('Course price must be positive')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class TeacherChoicePreference(models.Model):
    """
    Store teacher preferences for automatic decisions
    """
    PREFERENCE_CHOICES = [
        ('always_accept', 'Always Accept TeoCoin'),
        ('always_decline', 'Always Decline TeoCoin'),
        ('manual', 'Manual Decision Required'),
        ('threshold_based', 'Accept if TEO value > threshold')
    ]
    
    teacher = models.OneToOneField(User, on_delete=models.CASCADE, related_name='choice_preference')
    preference = models.CharField(max_length=20, choices=PREFERENCE_CHOICES, default='manual')
    
    # For threshold-based decisions
    minimum_teo_threshold = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Minimum TEO amount to auto-accept"
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    immediate_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.teacher.email}: {self.get_preference_display()}"
    
    def should_auto_accept(self, teo_amount_display):
        """
        Determine if this preference should auto-accept a discount request
        """
        if self.preference == 'always_accept':
            return True
        elif self.preference == 'always_decline':
            return False
        elif self.preference == 'threshold_based' and self.minimum_teo_threshold:
            return Decimal(str(teo_amount_display)) >= self.minimum_teo_threshold
        return False  # manual or no auto-decision
