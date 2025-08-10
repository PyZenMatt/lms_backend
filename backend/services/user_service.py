"""
User Service - Business Logic for User Management

Handles all user-related operations including registration, profile management,
and teacher approval workflows.
"""

from typing import Dict, List, Optional, Any
from django.contrib.auth import get_user_model
from django.db import transaction
from courses.models import CourseEnrollment
from notifications.models import Notification
from services.base import TransactionalService
from services.exceptions import (
    TeoArtServiceException,
    UserNotFoundError,
    UserAlreadyExistsError,
)

User = get_user_model()


class UserService(TransactionalService):
    """
    Service for managing user operations.
    
    Handles user registration, profile management, teacher approval,
    and user-related business logic.
    """
    
    def get_user_profile_data(self, user) -> Dict[str, Any]:
        """
        Get complete user profile data including courses.
        
        Args:
            user: User instance
            
        Returns:
            Dict containing user profile data
            
        Raises:
            TeoArtServiceException: If error retrieving data
        """
        try:
            self.log_info(f"Retrieving profile data for user {user.id}")
            
            if user.role == 'student':
                courses = self._get_student_courses(user)
            elif user.role == 'teacher':
                courses = self._get_teacher_courses(user)
            else:
                courses = []
            
            profile_data = {
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'courses': courses,
                'teo_coins': getattr(user, 'teo_coins', 0),
                'is_approved': getattr(user, 'is_approved', False),
                'bio': getattr(user, 'bio', ''),
                'avatar': user.avatar.url if hasattr(user, 'avatar') and user.avatar else None,
                'wallet_address': getattr(user, 'wallet_address', None),  # Add wallet_address for frontend compatibility
                'profession': getattr(user, 'profession', ''),
                'artistic_aspirations': getattr(user, 'artistic_aspirations', ''),
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
            }
            
            self.log_info(f"Successfully retrieved profile data for user {user.id}")
            return profile_data
            
        except Exception as e:
            self.log_error(f"Error retrieving profile data for user {user.id}: {str(e)}")
            raise TeoArtServiceException(f"Error retrieving user profile: {str(e)}")
    
    def _get_student_courses(self, user) -> List[Dict]:
        """Get courses for a student user."""
        enrollments = CourseEnrollment.objects.filter(student=user).select_related('course')
        return [
            {
                'id': enrollment.course.id,
                'title': enrollment.course.title,
                'description': getattr(enrollment.course, 'description', ''),
                'price': getattr(enrollment.course, 'price', 0),
                'category': getattr(enrollment.course, 'category', 'other'),
                'cover_image': enrollment.course.cover_image.url if hasattr(enrollment.course, 'cover_image') and enrollment.course.cover_image else None,
                'completed': enrollment.completed,
                'progress': 100 if enrollment.completed else 0,  # Simple progress: 0% or 100%
                'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None,
            }
            for enrollment in enrollments
        ]
    
    def _get_teacher_courses(self, user) -> List[Dict]:
        """Get courses for a teacher user."""
        courses = user.created_courses.all()
        return [
            {
                'id': course.id,
                'title': course.title,
                'description': getattr(course, 'description', ''),
                'price': getattr(course, 'price', 0),
                'category': getattr(course, 'category', 'other'),
                'cover_image': course.cover_image.url if hasattr(course, 'cover_image') and course.cover_image else None,
                'student_count': course.enrollments.count() if hasattr(course, 'enrollments') else 0,
                'created_at': course.created_at.isoformat() if hasattr(course, 'created_at') else None,
            }
            for course in courses
        ]
    
    def get_pending_teachers(self) -> List[Dict[str, Any]]:
        """
        Get list of teachers pending approval.
        
        Returns:
            List of pending teacher data
        """
        try:
            self.log_info("Retrieving pending teachers")
            
            pending_teachers = User.objects.filter(
                role='teacher', 
                is_approved=False
            ).values(
                'id', 'username', 'email', 'bio', 'profession', 
                'artistic_aspirations', 'date_joined'
            )
            
            teachers_list = list(pending_teachers)
            self.log_info(f"Found {len(teachers_list)} pending teachers")
            
            return teachers_list
            
        except Exception as e:
            self.log_error(f"Error retrieving pending teachers: {str(e)}")
            raise TeoArtServiceException(f"Error retrieving pending teachers: {str(e)}")
    
    def approve_teacher(self, teacher_id: int) -> Dict[str, Any]:
        """
        Approve a teacher application.
        
        Args:
            teacher_id: ID of the teacher to approve
            
        Returns:
            Dict with approval result
            
        Raises:
            UserNotFoundError: If teacher not found
            TeoArtServiceException: If approval fails
        """
        def _approve_operation():
            try:
                teacher = User.objects.get(id=teacher_id, role='teacher')
            except User.DoesNotExist:
                raise UserNotFoundError(user_id=teacher_id)
            
            if teacher.is_approved:
                self.log_info(f"Teacher {teacher_id} is already approved")
                return {
                    'teacher_id': teacher.id,
                    'teacher_email': teacher.email,
                    'already_approved': True
                }
            
            # Approve teacher
            teacher.is_approved = True
            teacher.save(update_fields=['is_approved'])
            
            # Create notification
            Notification.objects.create(
                user=teacher,
                message="Il tuo profilo docente è stato approvato!",
                notification_type='teacher_approved',
                related_object_id=teacher.pk
            )
            
            self.log_info(f"Successfully approved teacher {teacher_id}")
            
            return {
                'teacher_id': teacher.id,
                'teacher_email': teacher.email,
                'approved_at': teacher.updated_at.isoformat() if hasattr(teacher, 'updated_at') else None
            }
        
        try:
            return self.execute_in_transaction(_approve_operation)
        except UserNotFoundError:
            raise
        except Exception as e:
            self.log_error(f"Error approving teacher {teacher_id}: {str(e)}")
            raise TeoArtServiceException(f"Error approving teacher: {str(e)}")
    
    def reject_teacher(self, teacher_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject a teacher application.
        
        Args:
            teacher_id: ID of the teacher to reject
            reason: Optional rejection reason
            
        Returns:
            Dict with rejection result
            
        Raises:
            UserNotFoundError: If teacher not found
            TeoArtServiceException: If rejection fails
        """
        def _reject_operation():
            try:
                teacher = User.objects.get(id=teacher_id, role='teacher')
            except User.DoesNotExist:
                raise UserNotFoundError(user_id=teacher_id)
            
            # Create rejection notification
            rejection_message = "La tua candidatura come docente è stata respinta."
            if reason:
                rejection_message += f" Motivo: {reason}"
            
            Notification.objects.create(
                user=teacher,
                message=rejection_message,
                notification_type='teacher_rejected',
                related_object_id=teacher.pk
            )
            
            # For now, we don't delete the user, just notify
            # In future, we might want to change role or delete
            
            self.log_info(f"Successfully rejected teacher {teacher_id}")
            
            return {
                'teacher_id': teacher.id,
                'teacher_email': teacher.email,
                'rejection_reason': reason
            }
        
        try:
            return self.execute_in_transaction(_reject_operation)
        except UserNotFoundError:
            raise
        except Exception as e:
            self.log_error(f"Error rejecting teacher {teacher_id}: {str(e)}")
            raise TeoArtServiceException(f"Error rejecting teacher: {str(e)}")


# Singleton instance for easy access
user_service = UserService()
