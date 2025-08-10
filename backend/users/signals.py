"""
User signals for auto-creating related profiles

This module handles automatic creation of user profiles when users are created or updated.
Specifically handles TeacherProfile creation for users with teacher role.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import TeacherProfile
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_teacher_profile(sender, instance, created, **kwargs):
    """
    Automatically create TeacherProfile for teacher users
    
    This signal fires every time a User is saved and ensures that:
    1. Teachers get a TeacherProfile with default settings
    2. Non-teachers don't get unnecessary profiles
    3. Existing teachers get profiles if they don't have one
    """
    if instance.role == 'teacher':
        # Check if teacher profile already exists
        if not hasattr(instance, 'teacher_profile') or not instance.teacher_profile:
            try:
                # Create new teacher profile with defaults
                teacher_profile = TeacherProfile.objects.create(
                    user=instance,
                    commission_rate=50.00,  # Default Bronze tier (50% commission)
                    staking_tier='Bronze',
                    staked_teo_amount=0.00,
                    wallet_address=getattr(instance, 'wallet_address', None)
                )
                
                logger.info(f"Created TeacherProfile for {instance.email} with Bronze tier (50% commission)")
                
            except Exception as e:
                logger.error(f"Failed to create TeacherProfile for {instance.email}: {e}")
    

@receiver(post_save, sender=User)
def sync_wallet_address(sender, instance, created, **kwargs):
    """
    Sync wallet address between User and TeacherProfile
    
    When a user updates their wallet address, ensure the TeacherProfile
    is also updated to maintain consistency.
    """
    if instance.role == 'teacher' and hasattr(instance, 'teacher_profile'):
        teacher_profile = instance.teacher_profile
        
        # Only update if wallet address has changed
        if teacher_profile.wallet_address != instance.wallet_address:
            teacher_profile.wallet_address = instance.wallet_address
            teacher_profile.save(update_fields=['wallet_address', 'updated_at'])
            
            logger.info(f"Synced wallet address for teacher {instance.email}: {instance.wallet_address}")


# Signal to clean up non-teacher profiles if role changes
@receiver(post_save, sender=User)
def cleanup_teacher_profile(sender, instance, created, **kwargs):
    """
    Remove TeacherProfile if user role changes from teacher to something else
    
    This ensures data integrity when user roles are modified.
    """
    if not created and instance.role != 'teacher':
        # User role changed away from teacher
        try:
            if hasattr(instance, 'teacher_profile') and instance.teacher_profile:
                teacher_profile = instance.teacher_profile
                teacher_profile.delete()
                logger.info(f"Removed TeacherProfile for {instance.email} (role changed to {instance.role})")
        except Exception as e:
            logger.error(f"Failed to remove TeacherProfile for {instance.email}: {e}")
