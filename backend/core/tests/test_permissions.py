from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import TeoCoinTransaction, Lesson
import time
import json

User = get_user_model()

class PermissionTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username=f'student_{time.time()}',
            password='testpass',
            role='student',
            teo_coins=1000
        )
        
        self.teacher = User.objects.create_user(
            username=f'teacher_{time.time()}',
            password='testpass',
            role='teacher'
        )
        
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            role='teacher'
        )
        
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Content',
            teacher=self.teacher,
            price=500
        )
        
        self.lessons_url = reverse('lesson_list_create')
        self.transactions_url = reverse('transaction-history')
        self.teocoins_url = reverse('teo-coins')
        self.transfer_url = reverse('transfer-teo-coins')

    # ... mantenere gli altri test uguali ...

    def test_transaction_visibility(self):
        TeoCoinTransaction.objects.create(user=self.student, amount=100, transaction_type='earned')
        TeoCoinTransaction.objects.create(user=self.teacher, amount=200, transaction_type='earned')
        
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.transactions_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], 100)
        
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.transactions_url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['amount'], 200)

    def test_admin_permissions(self):
        admin_only_urls = [
            reverse('admin:core_user_changelist'),
            reverse('admin:core_lesson_changelist')
        ]
        
        # Test utente normale
        self.client.force_authenticate(user=self.student)
        for url in admin_only_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        
        # Test admin (redirect alla login admin)
        self.client.force_authenticate(user=self.admin)
        for url in admin_only_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_teocoin_management_permissions(self):
        data = {'amount': 500}
        
        # Studente autenticato
        self.client.force_authenticate(user=self.student)
        response = self.client.post(
            self.teocoins_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Insegnante autenticato
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(
            self.teocoins_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Admin autenticato
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.teocoins_url, 
            json.dumps(data), 
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cross_user_access(self):
        self.client.force_authenticate(user=self.student)
        url = f"{self.transactions_url}?user_id={self.teacher.id}"
        response = self.client.get(url)
        self.assertEqual(len(response.data), 0)