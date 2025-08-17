"""
Management command to create test data for Teacher Discount Absorption system
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Course
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for Teacher Discount Absorption system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--teacher-email',
            type=str,
            help='Teacher email address',
        )
        parser.add_argument(
            '--student-email', 
            type=str,
            help='Student email address',
        )
        parser.add_argument(
            '--course-id',
            type=int,
            help='Course ID',
        )

    def handle(self, *args, **options):
        teacher_email = options.get('teacher_email')
        student_email = options.get('student_email')
        course_id = options.get('course_id')

        if not all([teacher_email, student_email, course_id]):
            self.stdout.write(
                self.style.ERROR('Please provide --teacher-email, --student-email, and --course-id')
            )
            return

        try:
            # Get teacher and student
            teacher = User.objects.get(email=teacher_email, role='teacher')
            student = User.objects.get(email=student_email, role='student')
            course = Course.objects.get(id=course_id)

            self.stdout.write(f"Creating test absorption opportunity...")
            self.stdout.write(f"Teacher: {teacher.username} ({teacher.email})")
            self.stdout.write(f"Student: {student.username} ({student.email})")
            self.stdout.write(f"Course: {course.title}")

            # Create test discount data
            discount_data = {
                'course_price_eur': 100.0,  # Course costs 100€
                'discount_percentage': 10,   # Student used 10% discount
                'teo_used': 10.0,           # Student used 10 TEO
                'discount_amount_eur': 10.0  # Discount worth 10€
            }

            # Create absorption opportunity
            absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
                student=student,
                teacher=teacher,
                course=course,
                discount_data=discount_data
            )

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created absorption opportunity {absorption.pk}')
            )
            
            self.stdout.write(f"Teacher tier: {absorption.teacher_tier}")
            self.stdout.write(f"Commission rate: {absorption.teacher_commission_rate}%")
            self.stdout.write(f"Option A - EUR: €{absorption.option_a_teacher_eur}")
            self.stdout.write(f"Option B - EUR: €{absorption.option_b_teacher_eur} + {absorption.option_b_teacher_teo} TEO")
            self.stdout.write(f"Expires at: {absorption.expires_at}")
            
        except User.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'User not found: {e}')
            )
        except Course.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Course with ID {course_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating absorption opportunity: {e}')
            )
