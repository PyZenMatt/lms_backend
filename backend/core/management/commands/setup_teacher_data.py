"""
Django management command to set up test data for teacher1 with the specific balances mentioned
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from users.models import TeacherProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up test data for teacher1 with specific TeoCoin balances'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='teacher1@example.com',
            help='Email of the teacher to set up (default: teacher1@example.com)'
        )
        parser.add_argument(
            '--unstaked',
            type=float,
            default=323.50,
            help='Unstaked (available) balance (default: 323.50)'
        )
        parser.add_argument(
            '--staked',
            type=float,
            default=250.00,
            help='Staked balance (default: 250.00)'
        )
    
    def handle(self, *args, **options):
        email = options['email']
        unstaked_amount = Decimal(str(options['unstaked']))
        staked_amount = Decimal(str(options['staked']))
        total_amount = unstaked_amount + staked_amount
        
        try:
            # Get or create the user
            try:
                user = User.objects.get(email=email)
                self.stdout.write(f"Using existing user: {email}")
            except User.DoesNotExist:
                # Create new user with unique username
                username = email.split('@')[0]
                counter = 1
                original_username = username
                
                # Make sure username is unique
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create(
                    email=email,
                    username=username,
                    first_name='Teacher',
                    last_name='One',
                    role='teacher',
                    is_approved=True
                )
                user.set_password('teacher123')
                user.save()
                self.stdout.write(f"Created new user: {email} (username: {username})")
            
            # Get or create TeoCoin balance
            teo_balance, created = DBTeoCoinBalance.objects.get_or_create(
                user=user,
                defaults={
                    'available_balance': unstaked_amount,
                    'staked_balance': staked_amount
                }
            )
            
            if not created:
                # Update existing balance
                teo_balance.available_balance = unstaked_amount
                teo_balance.staked_balance = staked_amount
                teo_balance.save()
                self.stdout.write(f"Updated existing TeoCoin balance")
            else:
                self.stdout.write(f"Created new TeoCoin balance")
            
            # Get or create teacher profile
            teacher_profile, created = TeacherProfile.objects.get_or_create(
                user=user,
                defaults={
                    'staked_teo_amount': staked_amount,
                    'commission_rate': Decimal('50.00'),
                    'staking_tier': 'Bronze'
                }
            )
            
            if not created:
                # Update existing profile
                teacher_profile.staked_teo_amount = staked_amount
                teacher_profile.save()
            
            # Update tier and commission based on staked amount
            tier_info = teacher_profile.update_tier_and_commission()
            teacher_profile.save()
            
            # Clear existing transactions and create initial ones
            DBTeoCoinTransaction.objects.filter(user=user).delete()
            
            # Create initial deposit transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type='deposit',
                amount=total_amount,
                description=f'Initial deposit of {total_amount} TEO from test setup'
            )
            
            # Create staking transaction if any amount is staked
            if staked_amount > 0:
                DBTeoCoinTransaction.objects.create(
                    user=user,
                    transaction_type='staked',
                    amount=staked_amount,
                    description=f'Initial stake of {staked_amount} TEO - Tier: {tier_info["tier"]}'
                )
            
            # Display results
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✅ Successfully set up {email}:\n"
                    f"   • Available Balance: {unstaked_amount} TEO\n"
                    f"   • Staked Balance: {staked_amount} TEO\n"
                    f"   • Total Balance: {total_amount} TEO\n"
                    f"   • Staking Tier: {tier_info['tier']}\n"
                    f"   • Commission Rate: {tier_info['commission_rate']}%\n"
                    f"   • Teacher Earnings: {100 - float(tier_info['commission_rate'])}%"
                )
            )
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error setting up teacher data: {str(e)}")
            )
            raise e
