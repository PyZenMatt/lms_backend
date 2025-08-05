"""
Django management command to clean up staking data for students
and ensure only teachers have staking capabilities
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal

from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from users.models import TeacherProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up staking data for students - only teachers should be able to stake'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually making changes'
        )
    
    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Find all students with staking data
        students_with_staking = []
        student_users = User.objects.filter(role='student')
        
        for student in student_users:
            try:
                balance = DBTeoCoinBalance.objects.get(user=student)
                if balance.staked_balance > 0:
                    students_with_staking.append({
                        'user': student,
                        'balance': balance,
                        'staked_amount': balance.staked_balance
                    })
            except DBTeoCoinBalance.DoesNotExist:
                continue
        
        if not students_with_staking:
            self.stdout.write(
                self.style.SUCCESS("✅ No students found with staking data. System is clean!")
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f"Found {len(students_with_staking)} students with staking data:")
        )
        
        total_unstaked = Decimal('0.00')
        
        for data in students_with_staking:
            student = data['user']
            balance = data['balance']
            staked_amount = data['staked_amount']
            
            self.stdout.write(f"  • {student.email}: {staked_amount} TEO staked")
            
            if not dry_run:
                # Move staked balance back to available balance
                balance.available_balance += staked_amount
                balance.staked_balance = Decimal('0.00')
                balance.save()
                
                # Create transaction record
                DBTeoCoinTransaction.objects.create(
                    user=student,
                    transaction_type='unstaked',
                    amount=staked_amount,
                    description=f'Auto-unstaked {staked_amount} TEO - Students cannot stake (system cleanup)'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f"    ✅ Moved {staked_amount} TEO from staked to available")
                )
            
            total_unstaked += staked_amount
        
        # Clean up any TeacherProfile records for students
        student_teacher_profiles = TeacherProfile.objects.filter(user__role='student')
        
        if student_teacher_profiles.exists():
            profile_count = student_teacher_profiles.count()
            self.stdout.write(
                self.style.WARNING(f"Found {profile_count} TeacherProfile records for students")
            )
            
            if not dry_run:
                student_teacher_profiles.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"    ✅ Deleted {profile_count} invalid TeacherProfile records")
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"\nDRY RUN SUMMARY: Would unstake {total_unstaked} TEO from students")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n✅ CLEANUP COMPLETE:")
            )
            self.stdout.write(f"   • Unstaked {total_unstaked} TEO from {len(students_with_staking)} students")
            self.stdout.write(f"   • All TEO moved to available balance")
            self.stdout.write(f"   • Students can now only use TEO for discounts")
            self.stdout.write(f"   • Only teachers can stake TEO for commission benefits")
        
        # Show summary of teacher staking data
        teachers_with_staking = DBTeoCoinBalance.objects.filter(
            user__role='teacher',
            staked_balance__gt=0
        ).select_related('user')
        
        if teachers_with_staking.exists():
            self.stdout.write(
                self.style.SUCCESS(f"\n📊 Teachers with staking data:")
            )
            for balance in teachers_with_staking:
                teacher_profile = TeacherProfile.objects.filter(user=balance.user).first()
                tier = teacher_profile.staking_tier if teacher_profile else 'Unknown'
                commission = teacher_profile.commission_rate if teacher_profile else 'Unknown'
                
                self.stdout.write(
                    f"   • {balance.user.email}: {balance.staked_balance} TEO staked "
                    f"(Tier: {tier}, Commission: {commission}%)"
                )
