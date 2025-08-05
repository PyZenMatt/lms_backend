from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import Notification, Lesson, Exercise
from datetime import timedelta, datetime
from django.test.utils import override_settings
from django.utils import timezone
import unittest
from unittest import skip, skipIf
from django.conf import settings

User = get_user_model()

class NotificationSystemTests(APITestCase):
    @override_settings(DISABLE_SIGNALS=True)
    def setUp(self):
        Notification.objects.all().delete() 
        Lesson.objects.all().delete()
        Exercise.objects.all().delete()

        # Crea utenti
        self.student = User.objects.create_user(
            username='test_student',
            password='testpass',
            role='student'
        )
        
        self.teacher = User.objects.create_user(
            username='test_teacher',
            password='testpass',
            role='teacher'
        )

        # Crea lezione
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Content',
            teacher=self.teacher,
            price=500
        )
        
        # Crea esercizio
        self.exercise = Exercise.objects.create(
            student=self.student,
            lesson=self.lesson,
            submission='Test submission',
            status='submitted'
        )

        # URL
        self.notifications_url = reverse('notification-list')
        self.mark_read_url = lambda id: reverse('notification-mark-read', args=[id])
    
    def create_test_notifications(self):
        now = timezone.now()
        for i in range(3):
            notification = Notification.objects.create(
            user=self.student,
            message=f"Ordine test {i}",
            notification_type='lesson_purchased',
            created_at=now - timedelta(hours=i)  # Notifiche più vecchie di 0, 1, 2 ore
        )
        # Forza il salvataggio con timestamp specifico
        notification.created_at = now - timedelta(hours=i)
        notification.save()

        @unittest.skip("Test temporaneamente disabilitato per debug")
        def test_notification_filters(self):
            now = timezone.now().replace(microsecond=0)
    
    # Crea notifiche con date precise
        for i in range(3):
            delta = timedelta(days=(3 - i))
            notification = Notification.objects.create(
            user=self.student,
            message=f"Notification {i}",
            notification_type='exercise_graded' if i < 2 else 'lesson_purchased',
            related_object_id=self.exercise.id if i < 2 else self.lesson.id,
            read=False
        )
        # Forza il timestamp
        notification.created_at = now - delta
        notification.save()

        cutoff_datetime = (now - timedelta(days=2)).isoformat()
        response = self.client.get(
        f"{self.notifications_url}?created_after={cutoff_datetime}"
    
    )
    
    # Verifica solo le notifiche degli ultimi 2 giorni
        self.assertEqual(len(response.data), 2)
    
    # Verifica che la notifica più vecchia sia esclusa
        dates = [n['created_at'] for n in response.data]
        oldest_allowed = (now - timedelta(days=2)).replace(
        hour=0, minute=0, second=0, microsecond=0
    ).isoformat()
        self.assertTrue(all(d >= oldest_allowed for d in dates))

    def test_notification_lifecycle(self):
        notification = Notification.objects.create(
            user=self.student,
            message="Test lifecycle",
            notification_type='lesson_purchased',
            read=False
        )
        
        self.client.force_authenticate(user=self.student)
        
        # Marca come letta
        response = self.client.post(self.mark_read_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verifica filtri
        response = self.client.get(f"{self.notifications_url}?read=false")
        self.assertEqual(len(response.data), 0)
        
        response = self.client.get(f"{self.notifications_url}?read=true")
        self.assertEqual(len(response.data), 1)

    def test_related_object_resolution(self):
        self.exercise.status = 'reviewed'
        self.exercise.score = 85  # Aggiungi questa riga
        self.exercise.save()

        notification = Notification.objects.create(
            user=self.student,
            message="Esercizio valutato",
            notification_type='exercise_graded',
            related_object_id=self.exercise.id
    )
    
        self.client.force_authenticate(user=self.student)
        response = self.client.get(self.notifications_url)
        
        self.assertEqual(response.data[0]['related_object']['id'], self.exercise.id)
        self.assertEqual(response.data[0]['related_object']['score'], 85) 

    def test_notification_ordering(self):
    # Crea notifiche con date diverse
        Notification.objects.create(
        user=self.user,
        message="Notifica 1",
        created_at=timezone.now() - timezone.timedelta(days=1)
    )
        Notification.objects.create(
        user=self.user,
        message="Notifica 2",
        created_at=timezone.now()
    )
    
        response = self.client.get(self.notifications_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertGreater(
            response.data[0]['created_at'], 
            response.data[1]['created_at']
        )

    def test_cross_user_security(self):
        """Test sicurezza tra utenti diversi"""
        other_user = User.objects.create_user(
            username='other_student',
            password='testpass',
            role='student'
        )
        
        notification = Notification.objects.create(
            user=other_user,
            message="Notifica privata",
            notification_type='lesson_purchased'
        )
        
        self.client.force_authenticate(user=self.student)
        response = self.client.post(self.mark_read_url(notification.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_automatic_notification_creation(self):
        """Verifica creazione automatica notifiche per esercizi valutati"""
        exercise = Exercise.objects.create(
            student=self.student,
            lesson=self.lesson,
            submission="Nuovo esercizio",
            status='reviewed',
            score=90
        )
        
        notification = Notification.objects.filter(
            notification_type='exercise_graded',
            related_object_id=exercise.id
        ).first()
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.user, self.student)


    
