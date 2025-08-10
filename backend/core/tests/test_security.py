from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from core.models import User

class SecurityTests(APITestCase):
    def test_teacher_lesson_creation(self):
        # Studente prova a creare lezione
        user = User.objects.create_user(username='student', role='student')
        self.client.force_authenticate(user=user)
        response = self.client.post(reverse('lesson_list_create'), {
            'title': 'Illegal Lesson',
            'content': 'Test content',
            'price': 100
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)