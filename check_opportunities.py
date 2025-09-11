#!/usr/bin/env python

import os
import sys
import django

# Add Django path and configure settings
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from rewards.models import PaymentDiscountSnapshot
from courses.models import TeacherDiscountDecision

def check_opportunities():
    """Check current snapshots and decisions"""
    
    print("=== Current Opportunities Analysis ===")
    
    # Count snapshots
    snapshots = PaymentDiscountSnapshot.objects.all()
    print(f"Total PaymentDiscountSnapshots: {snapshots.count()}")
    
    # Count decisions  
    decisions = TeacherDiscountDecision.objects.all()
    print(f"Total TeacherDiscountDecisions: {decisions.count()}")
    
    print("\n--- Recent Snapshots ---")
    for snap in snapshots.order_by('-created_at')[:5]:
        print(f"Snapshot {snap.id}: {snap.order_id} - €{snap.price_eur} ({snap.discount_percent}%) - flat: €{snap.discount_amount_eur}")
        print(f"  Student: {snap.student.email if snap.student else 'N/A'}")
        print(f"  Teacher: {snap.teacher.email if snap.teacher else 'N/A'}")
        print(f"  Course: {snap.course.title if snap.course else 'N/A'}")
        print(f"  Created: {snap.created_at}")
        print()
    
    print("\n--- Recent Decisions ---")  
    for decision in decisions.order_by('-created_at')[:5]:
        print(f"Decision {decision.id}: {decision.course.title} - €{decision.course_price} ({decision.discount_percentage}%)")
        print(f"  Student: {decision.student.email}")
        print(f"  Teacher: {decision.teacher.email}")
        print(f"  Status: {decision.decision}")
        print(f"  Created: {decision.created_at}")
        print()
    
    # Check for potential duplicates
    print("\n--- Potential Duplicates ---")
    snapshots_by_key = {}
    for snap in snapshots:
        if snap.student and snap.course and snap.teacher:
            key = (snap.student.id, snap.course.id, snap.teacher.id)
            if key in snapshots_by_key:
                snapshots_by_key[key].append(snap)
            else:
                snapshots_by_key[key] = [snap]
    
    duplicates = {k: v for k, v in snapshots_by_key.items() if len(v) > 1}
    if duplicates:
        print(f"Found {len(duplicates)} potential duplicate snapshot groups:")
        for key, snaps in duplicates.items():
            print(f"  Student {key[0]}, Course {key[1]}, Teacher {key[2]}: {len(snaps)} snapshots")
            for snap in snaps:
                print(f"    - Snapshot {snap.id}: {snap.order_id} (created {snap.created_at})")
    else:
        print("No duplicate snapshots found")

if __name__ == "__main__":
    check_opportunities()
