from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.db import transaction
from users.models import User
from courses.models import Lesson, Exercise
from rewards.models import TeoCoinTransaction
import time
from django.db.models import F

class UserModelTests(TestCase):
    def test_user_creation_with_roles(self):
        # Usa username unici con timestamp
        timestamp = str(time.time()).replace('.', '')
        
        teacher = User.objects.create_user(
            username=f'teacher_{timestamp}',
            password='testpass123',
            role='teacher'
        )
        
        student = User.objects.create_user(
            username=f'student_{timestamp}',
            password='testpass123',
            role='student'
        )
        
        self.assertEqual(teacher.role, 'teacher')
        self.assertEqual(student.role, 'student')

    def test_teocoin_operations(self):
        user = User.objects.create_user(
            username=f'coin_user_{time.time()}',
            password='testpass123',
            role='student',
            teo_coins=100
        )
        
        user.add_teo_coins(50)
        user.refresh_from_db()
        self.assertEqual(user.teo_coins, 150)
        
        user.subtract_teo_coins(70)
        user.refresh_from_db()
        self.assertEqual(user.teo_coins, 80)
        
        with self.assertRaises(ValueError):
            user.subtract_teo_coins(100)

class LessonModelTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username=f'art_teacher_{time.time()}',
            password='testpass123',
            role='teacher'
        )
        
    def test_price_constraint(self):
        with self.assertRaises(ValidationError):
            lesson = Lesson(
                title='Invalid Lesson',
                content='Test content',
                teacher=self.teacher,
                price=-100
            )
            lesson.full_clean()

    def test_lesson_purchase_flow(self):
        student = User.objects.create_user(
            username=f'student_{time.time()}',
            password='testpass123',
            role='student',
            teo_coins=500
        )
        
        lesson = Lesson.objects.create(
            title='Painting Basics',
            content='Intro to colors',
            teacher=self.teacher,
            price=300,
            duration=60
        )
        
        lesson.purchase_by_student(student)
        student.refresh_from_db()
        
        self.assertIn(student, lesson.students.all())
        self.assertEqual(student.teo_coins, 200)
        self.assertEqual(TeoCoinTransaction.objects.count(), 2)

class ExerciseModelTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username=f'ex_teacher_{time.time()}',
            password='testpass123',
            role='teacher'
        )
        
        self.student = User.objects.create_user(
            username=f'learner_{time.time()}',
            password='testpass123',
            role='student'
        )
        
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Content',
            teacher=self.teacher,
            price=0,
            duration=30
        )

    def test_teocoin_assignment(self):
        exercise = Exercise.objects.create(
            student=self.student,
            lesson=self.lesson,
            submission='My work',
            status='submitted'
        )
        
        # Aggiorna a reviewed con punteggio
        exercise.status = 'reviewed'
        exercise.score = 85
        exercise.save()
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.teo_coins, 8)
        self.assertEqual(TeoCoinTransaction.objects.count(), 1)

    def tearDown(self):
        Exercise.objects.all().delete()

class ConcurrencyTests(TransactionTestCase):
    def test_teocoin_race_condition(self):
        user = User.objects.create_user(
            username=f'race_user_{time.time()}',
            password='testpass123',
            role='student',
            teo_coins=1000
        )
        
        # Test sequenziale con F() expressions
        for _ in range(10):
            User.objects.filter(pk=user.pk).update(
                teo_coins=F('teo_coins') + 10
            )
        
        user.refresh_from_db()
        self.assertEqual(user.teo_coins, 1100)