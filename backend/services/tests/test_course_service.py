"""
Tests for Course Service
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from courses.models import Course, CourseEnrollment, Lesson, LessonCompletion
from services.course_service import course_service
from services.exceptions import CourseNotFoundError, UserNotFoundError

User = get_user_model()


class CourseServiceTestCase(TestCase):
    """Test cases for CourseService"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher@test.com',
            password='testpass',
            role='teacher',
            first_name='John',
            last_name='Teacher'
        )
        
        self.student = User.objects.create_user(
            username='student1',
            email='student@test.com',
            password='testpass',
            role='student',
            first_name='Jane',
            last_name='Student'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='A test course',
            price=Decimal('99.99'),
            category='programming',
            teacher=self.teacher,
            is_approved=True
        )
        
        # Create test lessons
        self.lesson1 = Lesson.objects.create(
            title='Lesson 1',
            content='Content for lesson 1',
            course=self.course,
            lesson_type='video',
            duration=30,
            teacher=self.teacher
        )
        
        self.lesson2 = Lesson.objects.create(
            title='Lesson 2',
            content='Content for lesson 2',
            course=self.course,
            lesson_type='text',
            duration=15,
            teacher=self.teacher
        )
    
    def test_get_available_courses(self):
        """Test getting available courses"""
        courses = course_service.get_available_courses()
        
        self.assertEqual(len(courses), 1)
        course_data = courses[0]
        
        self.assertEqual(course_data['id'], self.course.id)
        self.assertEqual(course_data['title'], 'Test Course')
        self.assertEqual(course_data['price'], 99.0)
        self.assertEqual(course_data['lesson_count'], 2)
        self.assertFalse(course_data['is_enrolled'])
    
    def test_get_available_courses_with_user(self):
        """Test getting available courses with enrolled user"""
        # Enroll student
        CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            enrolled_at=timezone.now()
        )
        
        courses = course_service.get_available_courses(user=self.student)
        
        self.assertEqual(len(courses), 1)
        course_data = courses[0]
        self.assertTrue(course_data['is_enrolled'])
    
    def test_get_course_details(self):
        """Test getting course details"""
        details = course_service.get_course_details(self.course.id)
        
        self.assertEqual(details['id'], self.course.id)
        self.assertEqual(details['title'], 'Test Course')
        self.assertEqual(len(details['lessons']), 2)
        self.assertFalse(details['is_enrolled'])
        self.assertEqual(details['progress'], 0)
    
    def test_get_course_details_with_user(self):
        """Test getting course details with enrolled user"""
        # Enroll student
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            enrolled_at=timezone.now()
        )
        
        # Complete one lesson
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        
        details = course_service.get_course_details(self.course.id, user=self.student)
        
        self.assertTrue(details['is_enrolled'])
        self.assertEqual(details['progress'], 50)  # 1 out of 2 lessons completed
        
        # Check lesson completion status
        lesson_1_data = next(l for l in details['lessons'] if l['id'] == self.lesson1.id)
        lesson_2_data = next(l for l in details['lessons'] if l['id'] == self.lesson2.id)
        
        self.assertTrue(lesson_1_data['is_completed'])
        self.assertFalse(lesson_2_data['is_completed'])
    
    def test_get_course_details_not_found(self):
        """Test getting details for non-existent course"""
        with self.assertRaises(CourseNotFoundError):
            course_service.get_course_details(99999)
    
    def test_enroll_student_in_course(self):
        """Test enrolling student in course"""
        result = course_service.enroll_student_in_course(
            student_id=self.student.id,
            course_id=self.course.id
        )
        
        self.assertEqual(result['student_id'], self.student.id)
        self.assertEqual(result['course_id'], self.course.id)
        self.assertEqual(result['course_title'], 'Test Course')
        self.assertFalse(result['already_enrolled'])
        
        # Verify enrollment exists
        self.assertTrue(
            CourseEnrollment.objects.filter(
                student=self.student,
                course=self.course
            ).exists()
        )
    
    def test_enroll_student_already_enrolled(self):
        """Test enrolling student who is already enrolled"""
        # First enrollment
        CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            enrolled_at=timezone.now()
        )
        
        # Try to enroll again
        result = course_service.enroll_student_in_course(
            student_id=self.student.id,
            course_id=self.course.id
        )
        
        self.assertTrue(result['already_enrolled'])
    
    def test_enroll_student_not_found(self):
        """Test enrolling non-existent student"""
        with self.assertRaises(UserNotFoundError):
            course_service.enroll_student_in_course(
                student_id=99999,
                course_id=self.course.id
            )
    
    def test_enroll_course_not_found(self):
        """Test enrolling in non-existent course"""
        with self.assertRaises(CourseNotFoundError):
            course_service.enroll_student_in_course(
                student_id=self.student.id,
                course_id=99999
            )
    
    def test_get_student_enrollments(self):
        """Test getting student enrollments"""
        # Enroll student
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            enrolled_at=timezone.now()
        )
        
        # Complete one lesson
        LessonCompletion.objects.create(
            student=self.student,
            lesson=self.lesson1
        )
        
        enrollments = course_service.get_student_enrollments(self.student.id)
        
        self.assertEqual(len(enrollments), 1)
        enrollment_data = enrollments[0]
        
        self.assertEqual(enrollment_data['enrollment_id'], enrollment.id)
        self.assertEqual(enrollment_data['course']['id'], self.course.id)
        self.assertEqual(enrollment_data['course']['title'], 'Test Course')
        self.assertEqual(enrollment_data['progress'], 50)  # 1 out of 2 lessons completed
    
    def test_calculate_course_progress_no_lessons(self):
        """Test progress calculation for course with no lessons"""
        # Create course without lessons
        empty_course = Course.objects.create(
            title='Empty Course',
            description='No lessons',
            price=Decimal('0.00'),
            teacher=self.teacher,
            is_approved=True
        )
        
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=empty_course,
            enrolled_at=timezone.now()
        )
        
        progress = course_service._calculate_course_progress(enrollment)
        self.assertEqual(progress, 0)
    
    def test_calculate_course_progress_all_completed(self):
        """Test progress calculation when all lessons are completed"""
        enrollment = CourseEnrollment.objects.create(
            student=self.student,
            course=self.course,
            enrolled_at=timezone.now()
        )
        
        # Complete all lessons
        LessonCompletion.objects.create(student=self.student, lesson=self.lesson1)
        LessonCompletion.objects.create(student=self.student, lesson=self.lesson2)
        
        progress = course_service._calculate_course_progress(enrollment)
        self.assertEqual(progress, 100)
    
    def test_is_lesson_completed(self):
        """Test lesson completion check"""
        # Test lesson not completed
        self.assertFalse(course_service._is_lesson_completed(self.lesson1, self.student))
        
        # Complete lesson
        LessonCompletion.objects.create(student=self.student, lesson=self.lesson1)
        
        # Test lesson completed
        self.assertTrue(course_service._is_lesson_completed(self.lesson1, self.student))
        
        # Test with no user
        self.assertFalse(course_service._is_lesson_completed(self.lesson1, None))
