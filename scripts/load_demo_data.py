import os
import django
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.dev')
django.setup()

from users.models import User
from courses.models import Course, Lesson, Exercise

PASSWORD = 'testpass123'
EMAIL_DOMAIN = 'artschool.it'


# Create 5 teachers
teachers = []
students = []
for i in range(1, 6):
    email = f'teacher{i}@{EMAIL_DOMAIN}'
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': f'Teacher{i}',
            'last_name': 'Demo',
            'role': 'teacher',
            'is_active': True,
            'username': email
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()
    teachers.append(user)

# Create 5 students
for i in range(1, 6):
    email = f'student{i}@{EMAIL_DOMAIN}'
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': f'Student{i}',
            'last_name': 'Demo',
            'role': 'student',
            'is_active': True,
            'username': email
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()
    students.append(user)

# Approva tutti gli utenti demo (teacher e student)
for user in teachers + students:
    if not user.is_approved:
        user.is_approved = True
        user.save()

# Create 1 course per teacher, each with 5 lessons and 1 exercise per lesson
for idx, teacher in enumerate(teachers, 1):
    course_title = f"Corso d'Arte {idx}"
    price_eur = random.randint(100, 150)
    course, created = Course.objects.get_or_create(
        title=course_title,
        defaults={
            'description': f"Corso d'arte demo creato per il maestro {teacher.first_name}",
            'teacher': teacher,
            'price_eur': price_eur,
            'is_approved': True
        }
    )
    for l in range(1, 6):
        lesson, _ = Lesson.objects.get_or_create(
            course=course,
            teacher=teacher,
            title=f"Lezione {l}",
            defaults={
                'content': f"Contenuto della lezione {l} del corso {course_title}"
            }
        )
        Exercise.objects.get_or_create(
            lesson=lesson,
            title=f"Esercizio {l}",
            defaults={
                'description': f"Esercizio per la lezione {l} del corso {course_title}"
            }
        )

print('Demo data loaded: 5 teachers, 5 students, 5 courses (con lezioni ed esercizi)')
