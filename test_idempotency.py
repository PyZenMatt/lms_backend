#!/usr/bin/env python3
"""
Test script per verificare l'idempotenza del sistema di sconti TEO.

Testa scenari di:
- Click multipli sulla stessa percentuale
- Richieste concurrent
- Retry di rete
- Cambio di percentuale durante applicazione
"""

import os
import sys
import django
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
django.setup()

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.db.models import Sum
from courses.models import Course
from rewards.models import PaymentDiscountSnapshot
from blockchain.models import DBTeoCoinTransaction
from services.wallet_hold_service import WalletHoldService
import json

User = get_user_model()

class IdempotencyTestRunner:
    """Test runner per scenari di idempotenza"""
    
    def __init__(self):
        self.client = Client()
        self.test_user = None
        self.test_course = None
        self.setup_test_data()
    
    def setup_test_data(self):
        """Crea dati di test"""
        print("🔧 Setting up test data...")
        
        # Crea utente test
        self.test_user, created = User.objects.get_or_create(
            username='test_idempotency',
            defaults={
                'email': 'test_idempotency@example.com',
                'first_name': 'Test',
                'last_name': 'Idempotency'
            }
        )
        
        # Crea corso test
        self.test_course, created = Course.objects.get_or_create(
            title='Test Course Idempotency',
            defaults={
                'description': 'Course for testing discount idempotency',
                'slug': 'test-course-idempotency',
                'price_eur': Decimal('100.00'),
                'teacher_id': getattr(self.test_user, 'id', 1)  # type: ignore
            }
        )
        
        # Assicura che l'utente abbia TEO sufficienti
        self._ensure_teo_balance(1000)  # 1000 TEO
        
        print(f"✅ Test user: {self.test_user.username}")
        print(f"✅ Test course: {self.test_course.title}")
        print(f"✅ User TEO balance: {self._get_teo_balance()}")
    
    def _ensure_teo_balance(self, amount):
        """Assicura che l'utente abbia un balance TEO specifico"""
        # Prima reset del balance
        DBTeoCoinTransaction.objects.filter(user=self.test_user).delete()
        
        # Aggiungi balance
        DBTeoCoinTransaction.objects.create(
            user=self.test_user,
            amount=amount,
            transaction_type='admin_add',
            description='Test setup balance'
        )
    
    def _get_teo_balance(self):
        """Ottieni il balance TEO corrente"""
        from django.db.models import Sum
        balance = DBTeoCoinTransaction.objects.filter(
            user=self.test_user
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0
        return balance
    
    def _cleanup_snapshots(self):
        """Pulisci snapshot esistenti per questo test"""
        PaymentDiscountSnapshot.objects.filter(
            user=self.test_user,
            course=self.test_course
        ).delete()
    
    def _make_discount_request(self, percentage, checkout_session_id=None):
        """Effettua una richiesta di sconto"""
        if not checkout_session_id:
            checkout_session_id = f"test_session_{int(time.time() * 1000)}"
        
        # Login (ignore type checking for test)
        if self.test_user:
            self.client.force_login(self.test_user)  # type: ignore
        
        url = reverse('api:confirm_discount')
        data = {
            'course_id': getattr(self.test_course, 'id', None),
            'discount_percentage': percentage,
            'order_id': checkout_session_id
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        return response, checkout_session_id
    
    def test_multiple_clicks_same_percentage(self):
        """Test: Click multipli sulla stessa percentuale dovrebbero essere idempotenti"""
        print("\n🧪 Test: Multiple clicks same percentage")
        self._cleanup_snapshots()
        
        session_id = f"test_multi_click_{int(time.time() * 1000)}"
        responses = []
        
        # Esegui 5 richieste consecutive
        for i in range(5):
            response, _ = self._make_discount_request(10, session_id)
            responses.append(response)
            print(f"  Request {i+1}: Status {response.status_code}")
            
        # Verifica risultati
        success_count = sum(1 for r in responses if r.status_code == 200)
        snapshots = PaymentDiscountSnapshot.objects.filter(
            user=self.test_user,
            course=self.test_course,
            checkout_session_id=session_id
        )
        
        print(f"  ✅ Successful responses: {success_count}/5")
        print(f"  ✅ Snapshots created: {snapshots.count()}")
        print(f"  ✅ Should be exactly 1 snapshot: {snapshots.count() == 1}")
        
        # Verifica che il balance TEO sia stato decrementato solo una volta
        expected_balance = 1000 - 10  # 10 TEO per 10% di sconto su corso da 100 EUR
        actual_balance = self._get_teo_balance()
        print(f"  ✅ TEO balance correct: {actual_balance} == {expected_balance}")
        
        return snapshots.count() == 1 and actual_balance == expected_balance
    
    def test_concurrent_requests(self):
        """Test: Richieste concurrent dovrebbero essere gestite correttamente"""
        print("\n🧪 Test: Concurrent requests")
        self._cleanup_snapshots()
        
        session_id = f"test_concurrent_{int(time.time() * 1000)}"
        num_threads = 10
        
        def make_request():
            try:
                response, _ = self._make_discount_request(15, session_id)
                return response.status_code, response.content
            except Exception as e:
                return None, str(e)
        
        # Esegui richieste concurrent
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_threads)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for status, _ in results if status == 200)
        snapshots = PaymentDiscountSnapshot.objects.filter(
            user=self.test_user,
            course=self.test_course,
            checkout_session_id=session_id
        )
        
        print(f"  ✅ Concurrent requests: {num_threads}")
        print(f"  ✅ Successful responses: {success_count}")
        print(f"  ✅ Snapshots created: {snapshots.count()}")
        print(f"  ✅ Should be exactly 1 snapshot: {snapshots.count() == 1}")
        
        return snapshots.count() == 1
    
    def test_percentage_change_during_session(self):
        """Test: Cambio percentuale durante sessione dovrebbe supersedere il precedente"""
        print("\n🧪 Test: Percentage change during session")
        self._cleanup_snapshots()
        
        session_id = f"test_change_{int(time.time() * 1000)}"
        
        # Prima richiesta: 10%
        response1, _ = self._make_discount_request(10, session_id)
        print(f"  First request (10%): Status {response1.status_code}")
        
        time.sleep(0.1)  # Piccola pausa
        
        # Seconda richiesta: 20% (dovrebbe supersedere la prima)
        response2, _ = self._make_discount_request(20, session_id)
        print(f"  Second request (20%): Status {response2.status_code}")
        
        # Verifica risultati
        snapshots = PaymentDiscountSnapshot.objects.filter(
            user=self.test_user,
            course=self.test_course,
            checkout_session_id=session_id
        )
        
        active_snapshots = snapshots.filter(status='applied')
        superseded_snapshots = snapshots.filter(status='superseded')
        
        print(f"  ✅ Total snapshots: {snapshots.count()}")
        print(f"  ✅ Active snapshots: {active_snapshots.count()}")
        print(f"  ✅ Superseded snapshots: {superseded_snapshots.count()}")
        
        if active_snapshots.exists():
            active_percentage = active_snapshots.first().discount_percentage
            print(f"  ✅ Active percentage: {active_percentage}% (should be 20%)")
            return active_percentage == 20
        
        return False
    
    def test_wallet_hold_release(self):
        """Test: Verifica che gli hold vengano gestiti correttamente"""
        print("\n🧪 Test: Wallet hold/release")
        self._cleanup_snapshots()
        
        initial_balance = self._get_teo_balance()
        session_id = f"test_hold_{int(time.time() * 1000)}"
        
        # Crea uno sconto
        response, _ = self._make_discount_request(25, session_id)
        print(f"  Discount request: Status {response.status_code}")
        
        snapshot = PaymentDiscountSnapshot.objects.filter(
            user=self.test_user,
            course=self.test_course,
            checkout_session_id=session_id
        ).first()
        
        if snapshot and snapshot.wallet_hold_id:
            # Verifica che l'hold esista
            hold_service = WalletHoldService()
            
            # Il balance dovrebbe essere diminuito
            current_balance = self._get_teo_balance()
            hold_amount = 25  # 25 TEO per 25% di sconto
            
            print(f"  ✅ Initial balance: {initial_balance}")
            print(f"  ✅ Current balance: {current_balance}")
            print(f"  ✅ Expected decrease: {hold_amount}")
            print(f"  ✅ Hold ID: {snapshot.wallet_hold_id}")
            
            return current_balance == initial_balance - hold_amount
        
        return False

    def test_create_hold_deferred_and_capture_idempotent(self):
        """New test: create_hold must not deduct available balance; capture_hold deducts once."""
        print("\n🧪 Test: create_hold deferred deduction and idempotent capture")
        self._cleanup_snapshots()

        initial_balance = self._get_teo_balance()
        session_id = f"test_deferred_{int(time.time() * 1000)}"

        # Trigger discount which will create a hold
        response, _ = self._make_discount_request(10, session_id)
        snapshot = PaymentDiscountSnapshot.objects.filter(
            user=self.test_user,
            course=self.test_course,
            checkout_session_id=session_id
        ).first()

        assert snapshot is not None, "Snapshot must exist"
        assert snapshot.wallet_hold_id, "Snapshot must have wallet_hold_id"

        # Balance should be unchanged after create_hold
        after_hold_balance = self._get_teo_balance()
        print(f"  Initial balance: {initial_balance}, after hold: {after_hold_balance}")
        if after_hold_balance != initial_balance:
            print("  ❌ Balance changed on create_hold")
            return False

        # Capture the hold
        hold_service = WalletHoldService()
        captured_amount = hold_service.capture_hold(snapshot.wallet_hold_id, description="test capture")
        if not captured_amount:
            print("  ❌ capture_hold failed")
            return False

        # Balance should decrease by captured_amount
        post_capture_balance = self._get_teo_balance()
        print(f"  Post capture balance: {post_capture_balance}, captured_amount: {captured_amount}")
        if post_capture_balance != initial_balance - int(captured_amount):
            print("  ❌ Balance did not decrease correctly on capture")
            return False

        # Calling capture again must be idempotent (no further balance change)
        captured_again = hold_service.capture_hold(snapshot.wallet_hold_id, description="test capture retry")
        after_retry_balance = self._get_teo_balance()
        print(f"  After retry balance: {after_retry_balance}")
        if after_retry_balance != post_capture_balance:
            print("  ❌ Re-capture caused balance change")
            return False

        return True

    
    def run_all_tests(self):
        """Esegui tutti i test"""
        print("🚀 Starting idempotency tests...")
        print("=" * 50)
        
        tests = [
            self.test_multiple_clicks_same_percentage,
            self.test_concurrent_requests,
            self.test_percentage_change_during_session,
            self.test_wallet_hold_release
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append(result)
                print(f"  {'✅ PASS' if result else '❌ FAIL'}")
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
                results.append(False)
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {sum(results)}/{len(results)} passed")
        
        if all(results):
            print("🎉 All idempotency tests PASSED!")
        else:
            print("⚠️  Some tests FAILED - check implementation")
        
        return all(results)

if __name__ == '__main__':
    runner = IdempotencyTestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
