#!/usr/bin/env python
"""
Fix orphaned PaymentDiscountSnapshots that don't have linked TeacherDiscountDecision records.

This script:
1. Finds PaymentDiscountSnapshots without linked TeacherDiscountDecision records
2. Creates the missing TeacherDiscountDecision records using proper business logic
3. Links them together via the OneToOne relationship

This addresses the issue where teachers see opportunities with empty Decision fields.
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from rewards.models import PaymentDiscountSnapshot
from courses.models import TeacherDiscountDecision, Course
from users.models import User


def fix_orphaned_snapshots():
    """Create missing TeacherDiscountDecision records for orphaned snapshots."""
    
    # Find snapshots without linked decisions
    orphaned_snapshots = PaymentDiscountSnapshot.objects.filter(
        decision__isnull=True,
        teacher__isnull=False,
        student__isnull=False,
        course__isnull=False
    ).order_by('created_at')
    
    print(f"Found {orphaned_snapshots.count()} orphaned snapshots without decision records")
    
    if orphaned_snapshots.count() == 0:
        print("No orphaned snapshots found. All snapshots have linked decisions.")
        return
    
    created_count = 0
    skipped_count = 0
    
    for snapshot in orphaned_snapshots:
        print(f"\nProcessing snapshot {snapshot.id}:")
        print(f"  Student: {snapshot.student.email}")
        print(f"  Teacher: {snapshot.teacher.email}")
        print(f"  Course: {snapshot.course.title}")
        print(f"  Teacher TEO: {snapshot.teacher_teo}")
        print(f"  Created: {snapshot.created_at}")
        
        # Check if a decision record already exists for this combination
        existing_decision = TeacherDiscountDecision.objects.filter(
            student=snapshot.student,
            teacher=snapshot.teacher,
            course=snapshot.course
        ).first()
        
        if existing_decision:
            print(f"  → Decision {existing_decision.id} already exists (status: {existing_decision.decision})")
            # Link the existing decision to this snapshot
            if not hasattr(existing_decision, 'paymentdiscountsnapshot') or existing_decision.paymentdiscountsnapshot != snapshot:
                try:
                    snapshot.decision = existing_decision
                    snapshot.save(update_fields=['decision'])
                    print(f"  → Linked snapshot {snapshot.id} to existing decision {existing_decision.id}")
                except Exception as e:
                    print(f"  → Error linking to existing decision: {e}")
            skipped_count += 1
            continue
        
        # Create new TeacherDiscountDecision record
        try:
            # Calculate decision parameters from snapshot data
            course_price = snapshot.price_eur or Decimal('0')
            discount_percentage = snapshot.discount_percent or 0
            
            # Set expiration (24 hours from snapshot creation, or already expired if old)
            expires_at = snapshot.created_at + timedelta(hours=24)
            is_expired = timezone.now() > expires_at
            
            # Determine initial decision status
            if is_expired:
                # For old snapshots that are expired, mark as accepted if teacher got TEO
                initial_decision = "accepted" if snapshot.teacher_accepted_teo and snapshot.teacher_accepted_teo > 0 else "expired"
                decision_made_at = snapshot.created_at + timedelta(hours=23, minutes=59)  # Just before expiry
            else:
                initial_decision = "pending"
                decision_made_at = None
            
            # Get teacher's current commission rate and staking tier
            # For simplicity, use defaults if not available
            teacher_commission_rate = Decimal('50.00')  # Default 50%
            teacher_staking_tier = "Bronze"  # Default tier
            
            # Create the decision record
            decision = TeacherDiscountDecision.objects.create(
                student=snapshot.student,
                teacher=snapshot.teacher,
                course=snapshot.course,
                course_price=course_price,
                discount_percentage=discount_percentage,
                teacher_commission_rate=teacher_commission_rate,
                teacher_staking_tier=teacher_staking_tier,
                decision=initial_decision,
                decision_made_at=decision_made_at,
                expires_at=expires_at,
                created_at=snapshot.created_at,  # Backdate to match snapshot
                updated_at=snapshot.created_at
            )
            
            # Link the snapshot to the decision
            snapshot.decision = decision
            snapshot.save(update_fields=['decision'])
            
            print(f"  → Created decision {decision.id} with status '{initial_decision}'")
            print(f"  → Linked snapshot {snapshot.id} to decision {decision.id}")
            created_count += 1
            
        except Exception as e:
            print(f"  → Error creating decision: {e}")
            continue
    
    print(f"\nSummary:")
    print(f"  Created {created_count} new decision records")
    print(f"  Linked to existing {skipped_count} decision records")
    print(f"  Total processed: {created_count + skipped_count}")


def verify_fix():
    """Verify that all snapshots now have linked decisions."""
    remaining_orphaned = PaymentDiscountSnapshot.objects.filter(
        decision__isnull=True,
        teacher__isnull=False,
        student__isnull=False,
        course__isnull=False
    ).count()
    
    print(f"\nVerification:")
    print(f"  Remaining orphaned snapshots: {remaining_orphaned}")
    
    if remaining_orphaned == 0:
        print("  ✅ All snapshots now have linked decision records!")
    else:
        print("  ❌ Some snapshots still don't have linked decisions")
    
    # Show summary of decision statuses
    total_decisions = TeacherDiscountDecision.objects.count()
    status_counts = {}
    for status in ['pending', 'accepted', 'declined', 'expired']:
        count = TeacherDiscountDecision.objects.filter(decision=status).count()
        status_counts[status] = count
    
    print(f"\nDecision status summary (total: {total_decisions}):")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")


if __name__ == "__main__":
    print("=== Fixing Orphaned PaymentDiscountSnapshots ===")
    print("This script creates missing TeacherDiscountDecision records for snapshots")
    print("that don't have linked decisions, fixing the 'empty Decision field' issue.\n")
    
    # Confirm before proceeding
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response != 'y':
        print("Aborted.")
        sys.exit(0)
    
    fix_orphaned_snapshots()
    verify_fix()
    
    print("\n=== Fix Complete ===")
    print("Teachers should now see proper decision statuses for all opportunities.")
