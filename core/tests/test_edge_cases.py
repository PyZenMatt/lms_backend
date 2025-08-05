from django.test import TestCase
from django.core.exceptions import ValidationError
from core.models import User, Course, Lesson, Notification, Exercise, TeoCoinTransaction

class EdgeCasesTests(TestCase):
    def test_course_without_lessons(self):
        teacher = User.objects.create(role='teacher')
        course = Course.objects.create(title="Empty Course", teacher=teacher)
        self.assertEqual(course.lessons.count(), 0)
        self.assertEqual(course.total_duration(), 0)

    def test_invalid_notification_type(self):
        student = User.objects.create(role='student')
        notification = Notification(
            user=student,
            message="Test",
            notification_type='invalid_type',
            related_object_id=1
        )

        with self.assertRaises(ValidationError):
            notification.full_clean()

    def test_max_score_exercise(self):
        # Crea l'utente insegnante
        teacher = User.objects.create(username='teacher1', role='teacher')
        
        # Crea la lezione correttamente
        lesson = Lesson.objects.create(
            title="Test Lesson",
            content="Content",
            teacher=teacher,
            price=100,
            duration=60
        )
        
        # Crea lo studente
        student = User.objects.create(username='student1', role='student')
        
        # Prova a creare esercizio con punteggio invalido
        exercise = Exercise(
            student=student,
            lesson=lesson,
            submission="Test submission",
            score=150  # Valore superiore al massimo consentito
        )
        
        with self.assertRaises(ValidationError) as context:
            exercise.full_clean()  # Esegue la validazione completa
        
        # Verifica che l'errore sia sul campo score
        self.assertIn('score', context.exception.message_dict)
        self.assertEqual(
            context.exception.message_dict['score'][0],
            'Il punteggio deve essere tra 0 e 100'
        )

    def test_user_deletion_cascade(self):
        user = User.objects.create(teo_coins=100)
        TeoCoinTransaction.objects.create(user=user, amount=50)
        user_pk = user.pk
        user.delete()
        self.assertFalse(TeoCoinTransaction.objects.filter(user_id=user_pk).exists())