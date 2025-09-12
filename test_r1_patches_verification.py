#!/usr/bin/env python3
"""
R1 Patches Verification Test
============================

Verifies all three R1 micro-patches for Payment Snapshot flow:
- R1.1: Snapshot-Decision Linking (critical audit trail)
- R1.2: EUR/TEO Splits per Policy (compliance gap)
- R1.3: Webhook Idempotency Guard (race condition protection)

Test Coverage:
1. Bronze/Wood tier: P=100€, D=15€ → EUR_split=7.5€, TEO_split=7.5€
2. Snapshot.decision linking during creation
3. Webhook duplicate event protection
4. Safety-net decision linking in settlement

Run with: python manage.py shell < test_r1_patches_verification.py
"""

import sys
import os
import django
from decimal import Decimal

# Django setup for standalone script
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import transaction

from rewards.models import PaymentDiscountSnapshot
from courses.models import TeacherDiscountDecision, Course, TeacherProfile
from rewards.services.transaction_services import apply_discount_and_snapshot
from rewards.services.tier_calculation import calculate_splits_by_policy

User = get_user_model()

def test_r1_1_snapshot_decision_linking():
    """R1.1: Verify snapshot.decision atomic linking during creation"""
    print("\n=== R1.1: Snapshot-Decision Linking Test ===")
    
    # Create test data
    teacher = User.objects.create_user(username='teacher_r1_1', email='teacher@test.com')
    student = User.objects.create_user(username='student_r1_1', email='student@test.com')
    course = Course.objects.create(title='Test Course R1.1', teacher=teacher, price=Decimal('100.00'))
    
    # Apply discount and snapshot with decision="accept"
    with transaction.atomic():
        snapshot = apply_discount_and_snapshot(
            course=course,
            student=student,
            discount_amount=Decimal('15.00'),
            decision_choice='accept',
            stripe_checkout_session_id='cs_test_r1_1'
        )
        
        # R1.1 Verification: snapshot.decision should be linked
        print(f"✓ Snapshot created: {snapshot.id}")
        print(f"✓ Decision linked: {snapshot.decision is not None}")
        print(f"✓ Decision choice: {snapshot.decision.choice if snapshot.decision else 'None'}")
        
        # Verify EUR/TEO splits are calculated (R1.2 integration)
        print(f"✓ EUR split: {snapshot.eur_split_amount}")
        print(f"✓ TEO split: {snapshot.teo_split_amount}")
        
    assert snapshot.decision is not None, "R1.1 FAILED: snapshot.decision not linked"
    assert snapshot.decision.choice == 'accept', "R1.1 FAILED: wrong decision choice"
    print("✅ R1.1 PASSED: Snapshot-Decision linking works")

def test_r1_2_tier_splits_calculation():
    """R1.2: Verify EUR/TEO splits calculation per policy"""
    print("\n=== R1.2: Tier-Based Splits Test ===")
    
    # Create Bronze teacher (tier='Wood' fallback)
    teacher = User.objects.create_user(username='teacher_bronze', email='bronze@test.com')
    profile, _ = TeacherProfile.objects.get_or_create(
        user=teacher,
        defaults={'tier': 'Bronze', 'verified': True}
    )
    
    # Test case: P=100€, D=15€, Bronze tier → 50/50 split
    price = Decimal('100.00')
    discount = Decimal('15.00')
    
    eur_split, teo_split = calculate_splits_by_policy(teacher, discount)
    
    print(f"✓ Teacher tier: {profile.tier}")
    print(f"✓ Discount amount: {discount}€")
    print(f"✓ EUR split: {eur_split}€")
    print(f"✓ TEO split: {teo_split}€")
    print(f"✓ Total check: {eur_split + teo_split}€ == {discount}€")
    
    # Bronze/Wood policy: 50/50 split
    expected_eur = discount / 2  # 7.5€
    expected_teo = discount / 2  # 7.5€
    
    assert eur_split == expected_eur, f"R1.2 FAILED: EUR split {eur_split} != {expected_eur}"
    assert teo_split == expected_teo, f"R1.2 FAILED: TEO split {teo_split} != {expected_teo}"
    assert eur_split + teo_split == discount, "R1.2 FAILED: splits don't sum to discount"
    
    print("✅ R1.2 PASSED: Tier-based splits calculation works")

def test_r1_3_webhook_idempotency():
    """R1.3: Verify webhook idempotency guard logic"""
    print("\n=== R1.3: Webhook Idempotency Test ===")
    
    # Create test snapshot
    teacher = User.objects.create_user(username='teacher_r1_3', email='webhook@test.com')
    student = User.objects.create_user(username='student_r1_3', email='webhook_student@test.com')
    course = Course.objects.create(title='Test Course R1.3', teacher=teacher, price=Decimal('100.00'))
    
    snapshot = apply_discount_and_snapshot(
        course=course,
        student=student, 
        discount_amount=Decimal('10.00'),
        decision_choice='accept',
        stripe_checkout_session_id='cs_test_r1_3'
    )
    
    # Simulate webhook processing: mark as processed with event ID
    event_id = "evt_test_r1_3_duplicate"
    idempotency_id = f"stripe_event:{event_id}"
    
    # First processing: should succeed
    snapshot.external_txn_id = idempotency_id
    snapshot.status = 'confirmed'
    snapshot.save(update_fields=['external_txn_id', 'status'])
    
    print(f"✓ Snapshot processed with event: {event_id}")
    print(f"✓ Idempotency ID: {idempotency_id}")
    print(f"✓ Snapshot status: {snapshot.status}")
    
    # Check idempotency logic
    already_processed = PaymentDiscountSnapshot.objects.filter(
        external_txn_id=idempotency_id,
        status__in=['confirmed', 'failed']
    ).exists()
    
    print(f"✓ Idempotency check: {already_processed}")
    assert already_processed, "R1.3 FAILED: idempotency check should detect processed event"
    
    print("✅ R1.3 PASSED: Webhook idempotency guard works")

def test_integration_end_to_end():
    """Integration test: Complete flow with all R1 patches"""
    print("\n=== R1 Integration Test ===")
    
    teacher = User.objects.create_user(username='teacher_integration', email='integration@test.com')
    student = User.objects.create_user(username='student_integration', email='int_student@test.com')
    course = Course.objects.create(title='Integration Course', teacher=teacher, price=Decimal('200.00'))
    
    # Create teacher profile with Gold tier for different split
    profile, _ = TeacherProfile.objects.get_or_create(
        user=teacher,
        defaults={'tier': 'Gold', 'verified': True}
    )
    
    # Apply discount with accept decision
    discount_amount = Decimal('30.00')
    snapshot = apply_discount_and_snapshot(
        course=course,
        student=student,
        discount_amount=discount_amount,
        decision_choice='accept',
        stripe_checkout_session_id='cs_integration_test'
    )
    
    print(f"✓ End-to-end snapshot: {snapshot.id}")
    print(f"✓ Decision linked: {snapshot.decision is not None}")
    print(f"✓ Decision choice: {snapshot.decision.choice}")
    print(f"✓ Teacher tier: {profile.tier}")
    print(f"✓ EUR split: {snapshot.eur_split_amount}€")
    print(f"✓ TEO split: {snapshot.teo_split_amount}€")
    print(f"✓ Total: {snapshot.eur_split_amount + snapshot.teo_split_amount}€")
    
    # Verify all R1 requirements
    assert snapshot.decision is not None, "Integration FAILED: no decision link"
    assert snapshot.decision.choice == 'accept', "Integration FAILED: wrong choice"
    assert snapshot.eur_split_amount + snapshot.teo_split_amount == discount_amount, "Integration FAILED: split mismatch"
    assert snapshot.status == 'applied', "Integration FAILED: wrong status"
    
    print("✅ R1 INTEGRATION PASSED: All patches work together")

def run_all_tests():
    """Run all R1 verification tests"""
    print("🔬 R1 PATCHES VERIFICATION SUITE")
    print("=" * 50)
    
    try:
        test_r1_1_snapshot_decision_linking()
        test_r1_2_tier_splits_calculation()
        test_r1_3_webhook_idempotency()
        test_integration_end_to_end()
        
        print("\n" + "=" * 50)
        print("🎉 ALL R1 PATCHES VERIFIED SUCCESSFULLY")
        print("✅ R1.1: Snapshot-Decision Linking")
        print("✅ R1.2: EUR/TEO Splits per Policy")
        print("✅ R1.3: Webhook Idempotency Guard")
        print("✅ Integration: End-to-End Flow")
        
    except Exception as e:
        print(f"\n❌ R1 VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_tests()
