from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import User
from courses.models import Lesson, Course
from notifications.models import Notification, Exercise
from users.serializers import RegisterSerializer
from courses.serializers import LessonSerializer, CourseSerializer
from notifications.serializers import NotificationSerializer

class RegisterSerializerTests(TestCase):
    def test_password_validation(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Testpass123',
            'password2': 'Wrongpass456',
            'role': 'student'
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['password2'][0]),
            "Le password non coincidono."
        )

    def test_role_validation(self):
        invalid_data = {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'Testpass123',
            'password2': 'Testpass123',
            'role': 'admin'
        }
        serializer = RegisterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['role'][0]),
            '"admin" is not a valid choice.'
        )

class LessonSerializerTests(TestCase):
    def test_price_validation(self):
        teacher = User.objects.create_user(
            username='teacher',
            password='testpass',
            role='teacher'
        )
        data = {
            'title': 'Invalid Lesson',
            'content': 'Content',
            'price': -100,
            'duration': 60
        }
        serializer = LessonSerializer(data=data, context={'request': type('obj', (object,), {'user': teacher})})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            str(serializer.errors['price'][0]),
            'Ensure this value is greater than or equal to 0.'
        )

class CourseSerializerTests(TestCase):
    def test_calculated_fields(self):
        teacher = User.objects.create_user(
            username='course_teacher',
            password='testpass',
            role='teacher'
        )
        
        lesson1 = Lesson.objects.create(
            title='Lesson 1',
            content='Content 1',
            teacher=teacher,
            price=100,
            duration=45
        )
        lesson2 = Lesson.objects.create(
            title='Lesson 2',
            content='Content 2',
            teacher=teacher,
            price=150,
            duration=60
        )
        
        course = Course.objects.create(
            title='Test Course',
            description='Course Description',
            teacher=teacher,
            price=200
        )
        course.lessons.add(lesson1, lesson2)
        
        serializer = CourseSerializer(course)
        self.assertEqual(serializer.data['total_duration'], 105)

class NotificationSerializerTests(TestCase):
    def test_related_object_serialization(self):
        teacher = User.objects.create_user(
            username='notif_teacher',
            password='testpass',
            role='teacher'
        )
        student = User.objects.create_user(
            username='notif_student',
            password='testpass',
            role='student'
        )
        
        lesson = Lesson.objects.create(
            title='Notified Lesson',
            content='Content',
            teacher=teacher,
            price=100,
            duration=30
        )
        
        notification = Notification.objects.create(
            user=student,
            message='Lezione acquistata',
            notification_type='lesson_purchased',
            related_object_id=lesson.id
        )
        
        serializer = NotificationSerializer(notification)
        data = serializer.data
        self.assertEqual(data['related_object']['title'], 'Notified Lesson')

    def test_invalid_related_object(self):
        student = User.objects.create_user(
            username='student_invalid',
            password='testpass',
            role='student'
        )
        
        notification = Notification.objects.create(
            user=student,
            message='Notifica errata',
            notification_type='exercise_graded',
            related_object_id=9999
        )
        
        serializer = NotificationSerializer(notification)
        data = serializer.data
        self.assertIsNone(data['related_object'])