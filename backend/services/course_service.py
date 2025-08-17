"""
Course Service - Business Logic for Course Management

Handles all course-related operations including creation, enrollment,
purchase workflows, and progress tracking.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone

from courses.models import Course, CourseEnrollment, Lesson, LessonCompletion
from services.base import TransactionalService
from services.exceptions import (
    TeoArtServiceException,
    CourseNotFoundError,
    UserNotFoundError,
)

User = get_user_model()


class CourseService(TransactionalService):
    """
    Service for managing course operations.
    
    Handles course creation, enrollment, purchase workflows,
    progress tracking, and course-related business logic.
    """
    
    def get_available_courses(self, user=None) -> List[Dict[str, Any]]:
        """
        Get list of available courses for a user.
        
        Args:
            user: User instance (optional, affects filtering)
            
        Returns:
            List of course data
        """
        try:
            self.log_info("Retrieving available courses")
            
            # Get approved courses
            courses = Course.objects.filter(
                is_approved=True
            ).select_related('teacher')
            
            course_list = []
            for course in courses:
                # Check if user is enrolled (if user provided)
                is_enrolled = False
                if user:
                    is_enrolled = CourseEnrollment.objects.filter(
                        student=user, 
                        course=course
                    ).exists()
                
                course_data = {
                    'id': course.id,
                    'title': course.title,
                    'description': course.description,
                    'price': float(course.price),
                    'category': course.category,
                    'cover_image': course.cover_image.url if course.cover_image else None,
                    'creator': {
                        'id': course.teacher.id,
                        'username': course.teacher.username,
                    },
                    'is_enrolled': is_enrolled,
                    'lesson_count': course.lessons_in_course.count(),
                    'created_at': course.created_at.isoformat(),
                }
                course_list.append(course_data)
            
            self.log_info(f"Retrieved {len(course_list)} available courses")
            return course_list
            
        except Exception as e:
            self.log_error(f"Error retrieving available courses: {str(e)}")
            raise TeoArtServiceException(f"Error retrieving courses: {str(e)}")
    
    def get_course_details(self, course_id: int, user=None) -> Dict[str, Any]:
        """
        Get detailed information about a specific course.
        
        Args:
            course_id: ID of the course
            user: User instance (optional, for enrollment status)
            
        Returns:
            Dict containing course details
            
        Raises:
            CourseNotFoundError: If course not found
        """
        try:
            self.log_info(f"Retrieving course details for course {course_id}")
            
            try:
                course = Course.objects.select_related('teacher').get(
                    id=course_id,
                    is_approved=True
                )
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Get enrollment status
            enrollment = None
            is_enrolled = False
            progress = 0
            
            if user:
                try:
                    enrollment = CourseEnrollment.objects.get(
                        student=user,
                        course=course
                    )
                    is_enrolled = True
                    progress = self._calculate_course_progress(enrollment)
                except CourseEnrollment.DoesNotExist:
                    pass
            
            # Get lessons
            lessons = course.lessons_in_course.all().order_by('id')
            lessons_data = [
                {
                    'id': lesson.id,
                    'title': lesson.title,
                    'content': lesson.content,
                    'lesson_type': lesson.lesson_type,
                    'duration': lesson.duration,
                    'is_completed': self._is_lesson_completed(lesson, user) if user else False,
                }
                for lesson in lessons
            ]
            
            course_details = {
                'id': course.id,
                'title': course.title,
                'description': course.description,
                'price': float(course.price),
                'category': course.category,
                'cover_image': course.cover_image.url if course.cover_image else None,
                'creator': {
                    'id': course.teacher.id,
                    'username': course.teacher.username,
                    'bio': course.teacher.bio,
                },
                'is_enrolled': is_enrolled,
                'progress': progress,
                'lessons': lessons_data,
                'total_lessons': len(lessons_data),
                'created_at': course.created_at.isoformat(),
                'updated_at': course.updated_at.isoformat(),
            }
            
            self.log_info(f"Successfully retrieved course {course_id} details")
            return course_details
            
        except CourseNotFoundError:
            raise
        except Exception as e:
            self.log_error(f"Error retrieving course {course_id} details: {str(e)}")
            raise TeoArtServiceException(f"Error retrieving course details: {str(e)}")
    
    def enroll_student_in_course(self, student_id: int, course_id: int) -> Dict[str, Any]:
        """
        Enroll a student in a course (free enrollment).
        
        Args:
            student_id: ID of the student
            course_id: ID of the course
            
        Returns:
            Dict with enrollment result
            
        Raises:
            UserNotFoundError: If student not found
            CourseNotFoundError: If course not found
            TeoArtServiceException: If enrollment fails
        """
        def _enrollment_operation():
            # Validate student
            try:
                student = User.objects.get(id=student_id, role='student')
            except User.DoesNotExist:
                raise UserNotFoundError(user_id=student_id)
            
            # Validate course
            try:
                course = Course.objects.get(id=course_id, is_approved=True)
            except Course.DoesNotExist:
                raise CourseNotFoundError(course_id)
            
            # Check if already enrolled
            enrollment, created = CourseEnrollment.objects.get_or_create(
                student=student,
                course=course,
                defaults={'enrolled_at': timezone.now()}
            )
            
            if not created:
                self.log_info(f"Student {student_id} already enrolled in course {course_id}")
                return {
                    'enrollment_id': enrollment.id,
                    'student_id': student.id,
                    'course_id': course.id,
                    'already_enrolled': True,
                    'enrolled_at': enrollment.enrolled_at.isoformat()
                }
            
            self.log_info(f"Successfully enrolled student {student_id} in course {course_id}")
            
            return {
                'enrollment_id': enrollment.id,
                'student_id': student.id,
                'course_id': course.id,
                'course_title': course.title,
                'enrolled_at': enrollment.enrolled_at.isoformat(),
                'already_enrolled': False
            }
        
        try:
            return self.execute_in_transaction(_enrollment_operation)
        except (UserNotFoundError, CourseNotFoundError):
            raise
        except Exception as e:
            self.log_error(f"Error enrolling student {student_id} in course {course_id}: {str(e)}")
            raise TeoArtServiceException(f"Error enrolling in course: {str(e)}")
    
    def get_student_enrollments(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Get all enrollments for a student.
        
        Args:
            student_id: ID of the student
            
        Returns:
            List of enrollment data
        """
        try:
            self.log_info(f"Retrieving enrollments for student {student_id}")
            
            enrollments = CourseEnrollment.objects.filter(
                student_id=student_id
            ).select_related('course', 'course__teacher')
            
            enrollments_data = []
            for enrollment in enrollments:
                progress = self._calculate_course_progress(enrollment)
                
                enrollment_data = {
                    'enrollment_id': enrollment.id,
                    'course': {
                        'id': enrollment.course.id,
                        'title': enrollment.course.title,
                        'description': enrollment.course.description,
                        'cover_image': enrollment.course.cover_image.url if enrollment.course.cover_image else None,
                        'creator': enrollment.course.teacher.username,
                    },
                    'enrolled_at': enrollment.enrolled_at.isoformat(),
                    'completed': enrollment.completed,
                    'progress': progress,
                }
                enrollments_data.append(enrollment_data)
            
            self.log_info(f"Retrieved {len(enrollments_data)} enrollments for student {student_id}")
            return enrollments_data
            
        except Exception as e:
            self.log_error(f"Error retrieving enrollments for student {student_id}: {str(e)}")
            raise TeoArtServiceException(f"Error retrieving enrollments: {str(e)}")
    
    def _calculate_course_progress(self, enrollment: CourseEnrollment) -> int:
        """Calculate progress percentage for a course enrollment."""
        total_lessons = enrollment.course.lessons_in_course.count()
        if total_lessons == 0:
            return 0
        
        completed_lessons = LessonCompletion.objects.filter(
            student=enrollment.student,
            lesson__course=enrollment.course
        ).count()
        
        return int((completed_lessons / total_lessons) * 100)
    
    def _is_lesson_completed(self, lesson, user) -> bool:
        """Check if a lesson is completed by a user."""
        if not user:
            return False
        
        return LessonCompletion.objects.filter(
            student=user,
            lesson=lesson
        ).exists()


# Singleton instance for easy access
course_service = CourseService()
