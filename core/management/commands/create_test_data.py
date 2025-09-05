from decimal import Decimal
from courses.models import Course, Exercise, Lesson
from django.core.management.base import BaseCommand
from users.models import User


class Command(BaseCommand):
	help = "Popola il database con dati demo"

	def handle(self, *args, **options):
		self.stdout.write("Creazione utenti demo...")

		# Crea insegnanti
		teachers = []
		for i in range(1, 6):  # 5 insegnanti
			teacher, created = User.objects.get_or_create(
				username=f"teacher{i}",
				defaults={
					"email": f"teacher{i}@teoart.it",
					"role": "teacher",
				},
			)
			if created:
				teacher.set_password("testpass123")
				teacher.save()
				self.stdout.write(f"Insegnante creato: {teacher.username}")
			teachers.append(teacher)

		# Crea studenti
		students = []
		for i in range(1, 21):  # 20 studenti
			student, created = User.objects.get_or_create(
				username=f"student{i}",
				defaults={
					"email": f"student{i}@teoart.it",
					"role": "student",
				},
			)
			if created:
				student.set_password("testpass123")
				student.save()
				self.stdout.write(f"Studente creato: {student.username}")
			students.append(student)

		# Crea corsi, lezioni ed esercizi
		self.stdout.write("Creazione corsi, lezioni ed esercizi...")
		for i, teacher in enumerate(teachers, start=1):
			for j in range(1, 4):  # Ogni insegnante crea 3 corsi
				course_title = f"Corso {i}-{j}: Arte e Creativit\u00e0"
				course, created = Course.objects.get_or_create(
					title=course_title,
					defaults={
						"description": f"Descrizione del {course_title}",
						"teacher": teacher,
						"price_eur": Decimal("100.00"),
					},
				)
				if created:
					self.stdout.write(f"Corso creato: {course.title}")

				# Crea lezioni per il corso
				for k in range(1, 11):  # Ogni corso ha 10 lezioni
					lesson_title = f"Lezione {k}: Introduzione al tema {k}"
					lesson, created = Lesson.objects.get_or_create(
						title=lesson_title,
						course=course,
						defaults={
							"content": f"Contenuto della {lesson_title}",
							"teacher": teacher,  # Associa l'insegnante del corso
							"order": k,
						},
					)
					if created:
						self.stdout.write(f"Lezione creata: {lesson.title}")

					# Crea esercizi per la lezione
					for idx in range(1, 11):  # Ogni lezione ha 10 esercizi
						exercise_title = f"Esercizio {idx}: Tema {k}-{idx}"
						exercise, created = Exercise.objects.get_or_create(
							lesson=lesson,
							title=exercise_title,
							defaults={
								"description": f"Descrizione dell'{exercise_title}",
								"status": "created",
							},
						)
						if created:
							self.stdout.write(f"Esercizio creato: {exercise.title}")

		self.stdout.write("Popolamento del database completato!")

