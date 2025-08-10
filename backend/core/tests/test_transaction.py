from django.urls import reverse
from rest_framework.test import APITestCase
from core.models import User, Lesson, TeoCoinTransaction

class TransactionTests(APITestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='teacher', role='teacher', teo_coins=0)
        self.student = User.objects.create_user(username='student', role='student', teo_coins=1000)
        self.lesson = Lesson.objects.create(title='Test Lesson', teacher=self.teacher, price=300)

    def test_lesson_purchase(self):
        self.client.force_authenticate(user=self.student)
        url = reverse('purchase-lesson', args=[self.lesson.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.teacher.refresh_from_db()
        
        self.assertEqual(self.student.teo_coins, 700)
        self.assertEqual(self.teacher.teo_coins, 270)  # 300 * 0.9
        self.assertEqual(TeoCoinTransaction.objects.count(), 2)