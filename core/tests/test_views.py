from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import Lesson, TeoCoinTransaction
import time

User = get_user_model()

class AuthAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('auth_register')
        self.login_url = reverse('token_obtain_pair')

    def test_user_registration(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Testpass123',
            'password2': 'Testpass123',
            'role': 'student'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_jwt_login(self):
        User.objects.create_user(
            username='testlogin',
            password='Testpass123',
            role='student'
        )
        data = {
            'username': 'testlogin',
            'password': 'Testpass123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

class LessonAPITests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username=f'teacher_{time.time()}',
            password='testpass',
            role='teacher'
        )
        self.lesson_data = {
            'title': 'Test Lesson',
            'content': 'Lesson Content',
            'price': 500,
            'duration': 60  # Aggiungi campo mancante
        }

        self.student = User.objects.create_user(
            username=f'student_{time.time()}',
            password='testpass',
            role='student',
            teo_coins=1000
        )
        self.client.force_authenticate(user=self.teacher)
        self.lesson_data = {
            'title': 'Test Lesson',
            'content': 'Lesson Content',
            'price': 500
        }

    def test_create_lesson_as_teacher(self):
        response = self.client.post(reverse('lesson_list_create'), self.lesson_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 1)

    def test_create_lesson_as_student(self):
        self.client.force_authenticate(user=self.student)
        response = self.client.post(reverse('lesson_list_create'), self.lesson_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class PurchaseAPITests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username=f'teacher_{time.time()}',
            password='testpass',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username=f'student_{time.time()}',
            password='testpass',
            role='student',
            teo_coins=1000  # Da 300 a 1000
        )
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Content',
            teacher=self.teacher,
            price=500,
            duration=60
        )
        

        self.client.force_authenticate(user=self.student)
        self.purchase_url = reverse('purchase-lesson', kwargs={'lesson_id': self.lesson.id})

    def test_successful_purchase(self):
        response = self.client.post(self.purchase_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student.refresh_from_db()
        self.lesson.refresh_from_db()
        self.assertEqual(self.student.teo_coins, 500)
        self.assertIn(self.student, self.lesson.students.all())
        self.assertEqual(TeoCoinTransaction.objects.count(), 2)

    def test_insufficient_balance_purchase(self):
        self.student.teo_coins = 100
        self.student.save()
        response = self.client.post(self.purchase_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_purchase(self):
        self.client.post(self.purchase_url)
        response = self.client.post(self.purchase_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Hai già acquistato questa lezione', response.data['error'])
 

class TransferAPITests(APITestCase):
    def setUp(self):
        self.sender = User.objects.create_user(
            username=f'sender_{time.time()}',
            password='testpass',
            role='student',
            teo_coins=1000
        )
        self.receiver = User.objects.create_user(
            username=f'receiver_{time.time()}',
            password='testpass',
            role='student'
        )
        self.client.force_authenticate(user=self.sender)
        self.transfer_url = reverse('transfer-teo-coins')

    def test_valid_transfer(self):
        data = {
            'to_user_id': self.receiver.id,
            'amount': 500
        }
        response = self.client.post(self.transfer_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.sender.refresh_from_db()
        self.receiver.refresh_from_db()
        self.assertEqual(self.sender.teo_coins, 500)
        self.assertEqual(self.receiver.teo_coins, 500)

    def test_transfer_to_invalid_user(self):
        data = {
            'to_user_id': 9999,
            'amount': 500
        }

class PermissionTests(APITestCase):
    def test_admin_teocoin_add(self):
        # Aggiungi email per evitare validation error
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',  # Aggiungi email
            password='adminpass',
            role='teacher'
        )