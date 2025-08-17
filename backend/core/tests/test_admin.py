# tests/test_admin.py
from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.models import Permission
from courses.models import Lesson, Exercise
from courses.admin import LessonAdmin, ExerciseAdmin

User = get_user_model()

class MockRequest:
    pass

class LessonAdminTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            role='teacher'
        )
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='testpass',
            role='student'
        )
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Content',
            teacher=self.teacher,
            duration=60
        )
        self.client = Client()
        self.client.force_login(self.admin_user)
        self.lesson_admin = LessonAdmin(Lesson, AdminSite())

    def test_admin_filters(self):
        url = reverse('admin:core_lesson_changelist')
        response = self.client.get(url)
        self.assertContains(response, 'By teacher')  # Verifica label filtro

    def test_teacher_filter_queryset(self):
        request = MockRequest()
        request.user = self.admin_user
        form = self.lesson_admin.get_form(request)
        teacher_field = form.base_fields['teacher']
        
        teachers = User.objects.filter(role='teacher').order_by('id')
        self.assertQuerySetEqual(
            teacher_field.queryset.order_by('id'),
            teachers,
            transform=lambda x: x
        )
    
    def test_list_display(self):
        url = reverse('admin:core_lesson_changelist')
        response = self.client.get(url)
        self.assertContains(response, self.lesson.title)
        self.assertContains(response, str(self.lesson.teacher))
        self.assertContains(response, str(self.lesson.price))

    def test_search_fields(self):
        url = reverse('admin:core_lesson_changelist') + '?q=Test'
        response = self.client.get(url)
        self.assertContains(response, self.lesson.title)

class ExerciseAdminTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass',
            role='teacher'
        )
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='testpass',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username='student1',
            password='testpass',
            role='student'
        )
        self.lesson = Lesson.objects.create(
            title='Test Lesson',
            content='Content',
            teacher=self.teacher,
            price=100
        )
        self.exercise = Exercise.objects.create(
            student=self.student,
            lesson=self.lesson,
            submission='Test submission'
        )
        self.client = Client()
        self.client.force_login(self.admin_user)
        self.exercise_admin = ExerciseAdmin(Exercise, AdminSite())

    def test_admin_filters(self):
        url = reverse('admin:core_exercise_changelist')
        response = self.client.get(url)
        self.assertContains(response, 'student')
        self.assertContains(response, 'lesson')
        self.assertContains(response, 'status')

    def test_student_filter_queryset(self):
        request = MockRequest()
        request.user = self.admin_user
        form = self.exercise_admin.get_form(request)
        student_field = form.base_fields['student']
        self.assertQuerySetEqual(
            student_field.queryset,
            User.objects.filter(role='student'),
            transform=lambda x: x
        )

    def test_list_display(self):
        url = reverse('admin:core_exercise_changelist')
        response = self.client.get(url)
        self.assertContains(response, self.student.username)
        self.assertContains(response, self.lesson.title)

    def test_search_fields(self):
        # Test ricerca per titolo lezione
        url = reverse('admin:core_exercise_changelist') + '?q=Test'
        response = self.client.get(url)
        self.assertContains(response, self.lesson.title)
        
        # Test ricerca per username studente
        url = reverse('admin:core_exercise_changelist') + '?q=student1'
        response = self.client.get(url)
        self.assertContains(response, self.student.username)

    def test_admin_permissions(self):
        # Crea utente staff con permessi limitati
        staff_user = User.objects.create_user(
            username='staff',
            password='testpass',
            role='teacher',
            is_staff=True,
            is_superuser=False
        )
        
        # Assegna permessi specifici
        view_perm = Permission.objects.get(codename='view_exercise')
        change_perm = Permission.objects.get(codename='change_exercise')
        staff_user.user_permissions.add(view_perm, change_perm)
        
        self.client.force_login(staff_user)
        
        # Verifica accesso alla modifica
        url = reverse('admin:core_exercise_change', args=[self.exercise.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # Test modifica con permessi
        response = self.client.post(url, {
            'student': self.student.id,
            'lesson': self.lesson.id,
            'submission': 'Modified content',
            'status': 'reviewed',
            'score': 85
        })
        self.assertEqual(response.status_code, 302)  # Redirect dopo successo

        # Test senza permessi
        staff_user.user_permissions.remove(change_perm)
        response = self.client.post(url, {'submission': 'Modified again'})
        self.assertEqual(response.status_code, 403)