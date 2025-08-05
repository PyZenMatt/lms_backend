from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from decimal import Decimal

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('L\'email è obbligatoria')
        if 'role' not in extra_fields or not extra_fields['role']:
            raise ValueError('Il ruolo è obbligatorio')
        email = self.normalize_email(email)
        role = extra_fields.get('role')

        # Gli studenti sono approvati automaticamente
        if role == 'student':
            extra_fields['is_approved'] = True

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Il superuser deve avere is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Il superuser deve avere is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    is_approved = models.BooleanField(
        default=False,
        help_text="Solo gli insegnanti approvati da admin possono pubblicare corsi/lezioni."
    )
    bio = models.TextField(
        blank=True, null=True,
        help_text="Breve biografia (opzionale)."
    )
    avatar = models.ImageField(
        upload_to='avatars/', blank=True, null=True,
        help_text="Immagine di profilo (opzionale)."
    )
    email = models.EmailField(unique=True)
    ROLE_CHOICES = (
        ('student', 'Studente'),
        ('teacher', 'Maestro'),
        ('admin', 'Amministratore'),
    )
    enrolled_courses = models.ManyToManyField('courses.Course', related_name='enrolled_students', blank=True)
    created_courses = models.ManyToManyField('courses.Course', related_name='teachers', blank=True)
    is_email_verified = models.BooleanField(default=False)
    role = models.CharField(
        max_length=10, 
        choices=ROLE_CHOICES,
        error_messages={
            'invalid_choice': '"%(value)s" non è una scelta valida.'
        }
    )

    email_verification_token = models.CharField(max_length=100, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']
    objects = UserManager()
    address = models.TextField(blank=True, null=True)  # Campo per l'indirizzo
    purchased_lessons = models.ManyToManyField(
        'courses.Lesson',
        related_name='purchasers',
        blank=True
    )
    phone = models.CharField(max_length=30, blank=True)  # Nuovo campo per il numero di telefono
    
    # Blockchain Integration
    wallet_address = models.CharField(
        max_length=42, 
        blank=True, 
        null=True,
        help_text="Indirizzo wallet Ethereum/Polygon per TeoCoins"
    )
    
    # Campi specifici per la scuola d'arte
    profession = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Professione artistica (es. illustratore, pittore ad olio, scultore)"
    )
    artistic_aspirations = models.TextField(
        blank=True, 
        null=True,
        help_text="Aspirazioni e specializzazioni artistiche"
    )
    
    def __str__(self):
        return self.email
    
    def send_verification_email(self):
        self.email_verification_token = get_random_string(50)
        self.save()
        send_mail(
            'Verifica il tuo account TeoArt',
            f'Clicca per verificare: http://localhost:8000/auth/verify-email/{self.email_verification_token}/',
            'noreply@teoart.it',
            [self.email],
            fail_silently=False,
        )

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        app_label = 'users'


class UserSettings(models.Model):
    """Model for storing user preferences and settings"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=False)
    course_reminders = models.BooleanField(default=True)
    weekly_digest = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # UI preferences
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    language = models.CharField(max_length=5, default='it')
    timezone = models.CharField(max_length=50, default='Europe/Rome')
    
    # Privacy settings
    show_profile = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=False)
    show_achievements = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Impostazioni Utente"
        verbose_name_plural = "Impostazioni Utenti"
    
    def __str__(self):
        return f"Settings for {self.user.email}"


class UserProgress(models.Model):
    """Model for tracking user progress across categories"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    
    # Overall statistics
    total_courses_enrolled = models.PositiveIntegerField(default=0)
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_lessons_completed = models.PositiveIntegerField(default=0)
    total_exercises_completed = models.PositiveIntegerField(default=0)
    total_hours_studied = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Tracking fields
    last_activity_date = models.DateTimeField(null=True, blank=True)
    streak_days = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Progresso Utente"
        verbose_name_plural = "Progressi Utenti"
    
    def __str__(self):
        return f"Progress for {self.user.email}"
    
    def calculate_overall_progress(self):
        """Calculate overall progress percentage"""
        if self.total_courses_enrolled == 0:
            return 0
        return round((self.total_courses_completed / self.total_courses_enrolled) * 100, 2)


class Achievement(models.Model):
    """Model for achievements that users can earn"""
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='award')
    color = models.CharField(max_length=7, default='#feca57')  # Hex color
    points_required = models.PositiveIntegerField(default=0)
    achievement_type = models.CharField(max_length=50, choices=[
        ('course_completion', 'Course Completion'),
        ('streak', 'Learning Streak'),
        ('score', 'High Score'),
        ('participation', 'Participation'),
        ('special', 'Special Achievement')
    ])
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
    
    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """Model for tracking which achievements users have earned"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='earned_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    class Meta:
        unique_together = ('user', 'achievement')
        verbose_name = "Achievement Utente"
        verbose_name_plural = "Achievements Utenti"
    
    def __str__(self):
        return f"{self.user.email} - {self.achievement.title}"


class TeacherProfile(models.Model):
    """
    Teacher-specific profile for commission rates and staking data
    
    This model stores the dynamic commission rates and staking information
    that are updated by the TeoCoin staking system.
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='teacher_profile',
        help_text="User account associated with this teacher profile"
    )
    
    # Commission and earnings data
    commission_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('50.00'),
        help_text="Platform commission rate percentage (e.g., 50.00 for 50%)"
    )
    
    # Staking information
    staking_tier = models.CharField(
        max_length=20, 
        default='Bronze',
        choices=[
            ('Bronze', 'Bronze (0 TEO)'),
            ('Silver', 'Silver (100 TEO)'),
            ('Gold', 'Gold (300 TEO)'),
            ('Platinum', 'Platinum (600 TEO)'),
            ('Diamond', 'Diamond (1,000 TEO)'),
        ],
        help_text="Current staking tier based on TEO staked"
    )
    
    staked_teo_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Amount of TEO currently staked"
    )
    
    # Blockchain integration
    wallet_address = models.CharField(
        max_length=42, 
        blank=True, 
        null=True,
        help_text="Teacher's blockchain wallet address for staking"
    )
    
    # Earnings tracking
    total_earned_eur = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total EUR earned from course sales"
    )
    
    total_earned_teo = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total TEO earned from student discounts"
    )
    
    # Course statistics
    total_courses = models.PositiveIntegerField(
        default=0,
        help_text="Total number of courses created by this teacher"
    )
    
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Combined total earnings (EUR equivalent)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_staking_update = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Profilo Insegnante"
        verbose_name_plural = "Profili Insegnanti"
        indexes = [
            models.Index(fields=['staking_tier']),
            models.Index(fields=['commission_rate']),
            models.Index(fields=['wallet_address']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.staking_tier} ({self.commission_rate}%)"
    
    @property
    def teacher_earnings_percentage(self):
        """Calculate teacher's earnings percentage (100% - commission%)"""
        return Decimal('100.00') - self.commission_rate
    
    @property
    def commission_rate_decimal(self):
        """Get commission rate as decimal (for calculations)"""
        return self.commission_rate / Decimal('100.00')
    
    def update_from_staking_info(self, staking_info):
        """
        Update teacher profile with data from TeoCoin staking service
        
        Args:
            staking_info: Dict from TeoCoinStakingService.get_user_staking_info()
        """
        self.commission_rate = Decimal(str(staking_info.get('commission_percentage', 50.00)))
        self.staking_tier = staking_info.get('tier_name', 'Bronze')
        self.staked_teo_amount = Decimal(str(staking_info.get('staked_amount_formatted', 0.00)))
        self.wallet_address = staking_info.get('wallet_address', self.wallet_address)
        self.last_staking_update = timezone.now()
        self.save()
        
    def can_stake_more(self):
        """Check if teacher can progress to next tier"""
        tier_requirements = {
            'Bronze': Decimal('100.00'),    # Next: Silver
            'Silver': Decimal('300.00'),    # Next: Gold  
            'Gold': Decimal('600.00'),      # Next: Platinum
            'Platinum': Decimal('1000.00'), # Next: Diamond
            'Diamond': None                 # Already at max
        }
        
        next_requirement = tier_requirements.get(self.staking_tier)
        if next_requirement is None:
            return False, "Already at maximum tier (Diamond)"
        
        needed = next_requirement - self.staked_teo_amount
        if needed <= 0:
            return True, "Ready to upgrade tier!"
        
        return True, f"Need {needed} more TEO for next tier"

    def update_tier_and_commission(self):
        """
        Update teacher's tier and commission based on current staked amount
        
        This method calculates the appropriate tier based on the staked amount
        and updates both the tier and commission rate accordingly.
        """
        # Define tier thresholds and commission rates (CORRECTED to match business logic)
        tier_config = {
            'Bronze': {'min_stake': Decimal('0'), 'commission_rate': Decimal('50.00')},     # 50% platform
            'Silver': {'min_stake': Decimal('100.00'), 'commission_rate': Decimal('45.00')}, # 45% platform  
            'Gold': {'min_stake': Decimal('300.00'), 'commission_rate': Decimal('40.00')},   # 40% platform
            'Platinum': {'min_stake': Decimal('600.00'), 'commission_rate': Decimal('35.00')}, # 35% platform
            'Diamond': {'min_stake': Decimal('1000.00'), 'commission_rate': Decimal('25.00')}, # 25% platform
        }
        
        # Determine the appropriate tier based on staked amount
        current_staked = self.staked_teo_amount or Decimal('0')
        new_tier = 'Bronze'  # Default
        new_commission = Decimal('50.00')  # Default
        
        # Check from highest tier down
        for tier_name, config in reversed(list(tier_config.items())):
            if current_staked >= config['min_stake']:
                new_tier = tier_name
                new_commission = config['commission_rate']
                break
        
        # Update if changed
        if self.staking_tier != new_tier or self.commission_rate != new_commission:
            self.staking_tier = new_tier
            self.commission_rate = new_commission
            self.last_staking_update = timezone.now()
            
            # Log the change
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Updated teacher {self.user.email}: Tier={new_tier}, Commission={new_commission}%")
        
        return {
            'tier': new_tier,
            'commission_rate': new_commission,
            'staked_amount': current_staked
        }

    def sync_with_staking_service(self):
        """
        DEPRECATED: Legacy staking service integration removed.
        Now uses database-only staking system.
        """
        try:
            # Use database-only staking system instead
            update_result = self.update_tier_and_commission()
            
            # Save changes
            self.save()
            
            return True, {
                'message': 'Profile updated using database staking system',
                'tier': update_result['tier'],
                'commission_rate': update_result['commission_rate'],
                'staked_amount': update_result['staked_amount']
            }
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Staking sync failed for {self.user.email}: {str(e)}")
            return False, f"Sync error: {str(e)}"


