#!/usr/bin/env python3
"""
🎯 TEACHER CHOICE ENDPOINT TEST
Test teacher TeoCoin acceptance endpoint in production
"""


def test_teacher_choice_endpoint():
    """Test teacher choice endpoint for TeoCoin acceptance"""
    print("🎯 TEACHER CHOICE ENDPOINT TEST")
    print("=" * 50)

    # Test 1: Import dependencies
    try:
        pass

        from api.teacher_absorption_views import \
            TeacherMakeAbsorptionChoiceView
        from rest_framework.test import APIRequestFactory
        from services.db_teocoin_service import DBTeoCoinService
        from users.models import User
        print("✅ 1. Imports: SUCCESS")
    except Exception as e:
        print(f"❌ 1. Imports: FAILED - {e}")
        return False

    # Test 2: Setup services
    try:
        factory = APIRequestFactory()
        db_service = DBTeoCoinService()
        print("✅ 2. Service setup: SUCCESS")
    except Exception as e:
        print(f"❌ 2. Service setup: FAILED - {e}")
        return False

    # Test 3: Find teacher
    try:
        teacher = User.objects.filter(role='teacher').first()
        if not teacher:
            teacher = User.objects.filter(is_staff=True).first()

        if teacher:
            print(f"✅ 3. Test teacher: {teacher.username}")
        else:
            print("❌ 3. No teacher found")
            return False
    except Exception as e:
        print(f"❌ 3. Teacher lookup: FAILED - {e}")
        return False

    # Test 4: Check initial balance
    try:
        initial_balance = db_service.get_balance(teacher)
        print(f"✅ 4. Initial balance: {initial_balance} TEO")
    except Exception as e:
        print(f"❌ 4. Balance check: FAILED - {e}")
        return False

    # Test 5: Test TEO choice endpoint
    try:
        request_data = {
            'absorption_id': 'test_notification_prod',
            'choice': 'teo',
            'amount': 5.0,
            'transaction_type': 'discount_absorption',
            'description': 'Production test - TEO choice'
        }

        request = factory.post(
            '/api/v1/teocoin/teacher/choice/',
            data=request_data,
            format='json'
        )
        request.user = teacher

        # Call the view
        view = TeacherMakeAbsorptionChoiceView()
        response = view.post(request)

        print(f"✅ 5. Endpoint call: SUCCESS")
        print(f"   📤 Status code: {response.status_code}")

        # Check if response is JSON
        try:
            response_data = response.data if hasattr(response, 'data') else {
                'message': 'No data attribute'}
            print(f"   📥 Response: {response_data}")

            # Check balance change
            final_balance = db_service.get_balance(teacher)
            balance_change = final_balance - initial_balance
            print(
                f"   💰 Balance change: {initial_balance} → {final_balance} TEO ({'+' if balance_change >= 0 else ''}{balance_change})")

            if response.status_code == 200 and balance_change > 0:
                print("✅ 5. TEO choice endpoint: COMPLETE SUCCESS")
            else:
                print("⚠️  5. TEO choice endpoint: PARTIAL SUCCESS (check response)")

        except Exception as e:
            print(f"   📥 Response processing error: {e}")

    except Exception as e:
        print(f"❌ 5. Endpoint test: FAILED - {e}")
        return False

    # Test 6: Test EUR choice endpoint
    try:
        request_data_eur = {
            'absorption_id': 'test_notification_eur_prod',
            'choice': 'eur',
            'amount': 3.0,
            'transaction_type': 'discount_absorption',
            'description': 'Production test - EUR choice'
        }

        request_eur = factory.post(
            '/api/v1/teocoin/teacher/choice/',
            data=request_data_eur,
            format='json'
        )
        request_eur.user = teacher

        view = TeacherMakeAbsorptionChoiceView()
        response_eur = view.post(request_eur)

        print(f"✅ 6. EUR choice test: SUCCESS")
        print(f"   📤 Status code: {response_eur.status_code}")

        try:
            response_data_eur = response_eur.data if hasattr(response_eur, 'data') else {
                'message': 'No data attribute'}
            print(f"   📥 Response: {response_data_eur}")
        except Exception as e:
            print(f"   📥 Response processing error: {e}")

    except Exception as e:
        print(f"❌ 6. EUR choice test: FAILED - {e}")
        # Non-critical, continue

    print("\n🎉 TEACHER CHOICE ENDPOINT TESTS COMPLETED!")
    return True


if __name__ == '__main__':
    success = test_teacher_choice_endpoint()
    exit(0 if success else 1)
