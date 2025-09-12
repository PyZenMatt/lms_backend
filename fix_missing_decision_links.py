#!/usr/bin/env python3
"""
Fix Missing Decision Links Script

This script finds notifications pointing to TeacherDiscountDecision IDs
and ensures the corresponding snapshots are properly linked.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from notifications.models import Notification
from courses.models import TeacherDiscountDecision
from rewards.models import PaymentDiscountSnapshot

def fix_missing_decision_links():
    """Find and fix missing decision links in snapshots"""
    
    print("🔧 FIXING MISSING DECISION LINKS")
    print("=" * 40)
    
    # Find all TeoCoin discount notifications
    teo_notifications = Notification.objects.filter(
        notification_type='teocoin_discount_pending'
    ).order_by('-created_at')
    
    print(f"📬 Found {teo_notifications.count()} TeoCoin notifications")
    
    fixed_count = 0
    already_linked_count = 0
    
    for notification in teo_notifications:
        try:
            # Get the decision this notification points to
            decision = TeacherDiscountDecision.objects.get(id=notification.related_object_id)
            
            # Find snapshots for this teacher/student/course combination
            matching_snapshots = PaymentDiscountSnapshot.objects.filter(
                teacher=decision.teacher,
                student=decision.student,
                course=decision.course,
                decision__isnull=True  # Only unlinked snapshots
            ).order_by('-created_at')
            
            if matching_snapshots.exists():
                # Link the most recent matching snapshot to this decision
                snapshot = matching_snapshots.first()
                snapshot.decision = decision
                snapshot.save(update_fields=['decision'])
                
                print(f"✅ Fixed: Linked Snapshot {snapshot.id} → Decision {decision.id}")
                print(f"   Teacher: {decision.teacher.username}")
                print(f"   Student: {decision.student.username}")
                print(f"   Course: {decision.course.title}")
                fixed_count += 1
            else:
                # Check if already linked
                linked_snapshots = PaymentDiscountSnapshot.objects.filter(
                    teacher=decision.teacher,
                    student=decision.student,
                    course=decision.course,
                    decision=decision
                )
                if linked_snapshots.exists():
                    already_linked_count += 1
                else:
                    print(f"❌ No matching snapshot found for Decision {decision.id}")
                    print(f"   Teacher: {decision.teacher.username}")
                    print(f"   Student: {decision.student.username}")
                    print(f"   Course: {decision.course.title}")
                    
        except TeacherDiscountDecision.DoesNotExist:
            print(f"❌ Notification {notification.id} points to non-existent decision {notification.related_object_id}")
        except Exception as e:
            print(f"❌ Error processing notification {notification.id}: {e}")
    
    print(f"\n🎯 SUMMARY:")
    print(f"   Fixed links: {fixed_count}")
    print(f"   Already linked: {already_linked_count}")
    print(f"   Total notifications: {teo_notifications.count()}")
    
    if fixed_count > 0:
        print(f"\n✅ SUCCESS: Fixed {fixed_count} missing decision links")
        print(f"   Teacher opportunities should now appear in frontend")
    else:
        print(f"\n💡 No missing links found - all snapshots are properly linked")

if __name__ == "__main__":
    fix_missing_decision_links()
