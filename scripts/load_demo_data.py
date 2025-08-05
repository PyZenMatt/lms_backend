import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from users.models import User
from courses.models import Course, Lesson, Exercise

PASSWORD = 'testpass123'
EMAIL_DOMAIN = 'artschool.it'

# Create 5 teachers
teachers = []
for i in range(1, 6):
    email = f'teacher{i}@{EMAIL_DOMAIN}'
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': f'Teacher{i}',
            'last_name': 'Demo',
            'is_teacher': True,
            'is_active': True
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
            'is_teacher': False,
            'is_active': True
        }
    )
    if created:
        user.set_password(PASSWORD)
        user.save()

# Create 1 course per teacher, each with 5 lessons and 1 exercise per lesson
for idx, teacher in enumerate(teachers, 1):
    course_title = f"Corso d'Arte {idx}"
    price = random.randint(100, 150)
    course, created = Course.objects.get_or_create(
        title=course_title,
        defaults={
            'description': f"Corso d'arte demo creato per il maestro {teacher.first_name}",
            'teacher': teacher,
            'price': price,
            'is_active': True
        }
    )
    for l in range(1, 6):
        lesson, _ = Lesson.objects.get_or_create(
            course=course,
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
