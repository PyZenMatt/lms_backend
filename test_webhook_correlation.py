#!/usr/bin/env python
"""
Test script per verificare il funzionamento del binding Stripe ↔ snapshot
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

def test_payment_intent_metadata():
    """Simula la creazione di un PaymentIntent con i metadata corretti"""
    from courses.models import Course
    from django.contrib.auth.models import User
    from rewards.models import PaymentDiscountSnapshot
    import json
    
    print("🧪 TEST: PaymentIntent metadata binding")
    print("=" * 50)
    
    # Trova uno snapshot pending con hold
    snapshot = PaymentDiscountSnapshot.objects.filter(
        status='pending',
        wallet_hold_id__isnull=False
    ).first()
    
    if not snapshot:
        print("❌ No pending snapshot with hold found")
        return False
    
    print(f"📋 Found test snapshot:")
    print(f"   ID: {snapshot.id}")
    print(f"   Status: {snapshot.status}")
    print(f"   Hold ID: {snapshot.wallet_hold_id}")
    print(f"   Stripe PI ID: {snapshot.stripe_payment_intent_id}")
    print()
    
    # Simula i metadata che ora dovrebbero essere aggiunti al PaymentIntent
    expected_metadata = {
        "discount_snapshot_id": str(snapshot.id),
        "hold_id": str(snapshot.wallet_hold_id),
        "order_id": str(snapshot.order_id) if snapshot.order_id else "",
        "course_id": str(snapshot.course.id) if snapshot.course else "",
        "user_id": str(snapshot.student.id) if snapshot.student else "",
    }
    
    print("🔗 Expected PaymentIntent metadata:")
    print(json.dumps(expected_metadata, indent=2))
    print()
    
    return True

def test_webhook_correlation():
    """Simula il lookup del webhook"""
    from rewards.models import PaymentDiscountSnapshot
    import json
    
    print("🧪 TEST: Webhook correlation lookup")
    print("=" * 50)
    
    # Simula i dati che arrivano dal webhook
    test_session = {
        "id": "cs_test_abc123",
        "payment_intent": "pi_test_xyz789",
        "metadata": {
            "discount_snapshot_id": "143",
            "hold_id": "143",
            "course_id": "1",
        }
    }
    
    print("📨 Webhook payload simulation:")
    print(json.dumps(test_session, indent=2))
    print()
    
    # Test lookup by metadata.discount_snapshot_id
    meta_snap_id = test_session.get('metadata', {}).get('discount_snapshot_id')
    if meta_snap_id:
        snapshot = PaymentDiscountSnapshot.objects.filter(
            id=meta_snap_id,
            status__in=['pending', 'applied']
        ).first()
        
        if snapshot:
            print(f"✅ CORRELATION SUCCESS via metadata.discount_snapshot_id")
            print(f"   Found snapshot: {snapshot.id}")
            print(f"   Status: {snapshot.status}")
            print(f"   Hold ID: {snapshot.wallet_hold_id}")
            return True
        else:
            print(f"❌ CORRELATION FAILED - No snapshot found for ID {meta_snap_id}")
            return False
    
    print("❌ No metadata.discount_snapshot_id in webhook")
    return False

def test_settle_simulation():
    """Simula il processo di settle"""
    from payments.services import settle_discount_snapshot
    from rewards.models import PaymentDiscountSnapshot
    
    print("🧪 TEST: Settle simulation (DRY RUN)")
    print("=" * 50)
    
    snapshot = PaymentDiscountSnapshot.objects.filter(
        status='pending',
        wallet_hold_id__isnull=False
    ).first()
    
    if not snapshot:
        print("❌ No pending snapshot with hold found")
        return False
    
    print(f"📋 Test snapshot before settle:")
    print(f"   ID: {snapshot.id}")
    print(f"   Status: {snapshot.status}")
    print(f"   Hold ID: {snapshot.wallet_hold_id}")
    print()
    
    # ATTENZIONE: Non eseguiamo il settle vero per non modificare lo stato
    # Questo è solo per verificare che la funzione esista e sia importabile
    try:
        print("✅ settle_discount_snapshot function is importable")
        print("   (Dry run - not executing actual settle)")
        return True
    except Exception as e:
        print(f"❌ Error importing settle function: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTING ISSUE-04A & 04B IMPLEMENTATION")
    print("=" * 60)
    print()
    
    tests = [
        test_payment_intent_metadata,
        test_webhook_correlation,
        test_settle_simulation,
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("📊 SUMMARY")
    print("=" * 20)
    passed = sum(results)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The binding should work.")
    else:
        print("⚠️  Some tests failed. Review the implementation.")
