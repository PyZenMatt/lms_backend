from decimal import Decimal
from rest_framework.test import APIClient
from django.test import TestCase
from django.contrib.auth import get_user_model
from rewards.models import Tier
from courses.models import Course


User = get_user_model()


class TestConfirmInsufficientBalance(TestCase):
    def setUp(self):
        self.client = APIClient()
        # create teacher and student
        self.teacher = User.objects.create_user(username='t_teacher', email='t@example.com', password='pass', role='teacher')
        self.student = User.objects.create_user(username='s_student', email='s_student@example.com', password='pass', role='student')

        # ensure Bronze tier exists
        Tier.objects.update_or_create(
            name="Bronzo",
            defaults={
                "teacher_split_percent": Decimal("50.00"),
                "platform_split_percent": Decimal("50.00"),
                "max_accept_discount_ratio": Decimal("1.00"),
                "teo_bonus_multiplier": Decimal("1.25"),
                "is_active": True,
            },
        )

        # course
        self.course = Course.objects.create(title='C1', price_eur=Decimal('50.00'), teacher=self.teacher)

        # Ensure student has zero balance (best-effort cleanup)
        try:
            from blockchain.models import DBTeoCoinBalance

            DBTeoCoinBalance.objects.filter(user=self.student).delete()
        except Exception:
            pass

        # Ensure DB connection settings include ATOMIC_REQUESTS key to avoid KeyError in request handling
        try:
            from django.db import connections
            if 'default' in connections:
                try:
                    # connections.settings is a dict mapping alias->settings dict
                    if hasattr(connections, 'settings') and isinstance(connections.settings, dict):
                        connections.settings.setdefault('default', {})
                        connections.settings['default'].setdefault('ATOMIC_REQUESTS', False)
                    # also set on the connection object for robustness
                    try:
                        connections['default'].settings_dict.setdefault('ATOMIC_REQUESTS', False)
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def test_confirm_rejects_on_insufficient_balance(self):
        self.client.force_authenticate(self.student)

        payload = {
            'order_id': 'test_insufficient_1',
            'course_id': self.course.id,
            'price_eur': '50.00',
            'discount_percent': '10',
            'accept_teo': True,
            'teacher_id': self.teacher.id,
        }

        res = self.client.post('/api/v1/rewards/discounts/confirm/', payload, format='json')

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data.get('error'), 'INSUFFICIENT_TOKENS')
