"""
Teacher approval management views
"""
from rest_framework import generics, status
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.shortcuts import get_object_or_404
from notifications.models import Notification
from users.models import User
from users.serializers import UserSerializer
from core.api_standards import StandardizedAPIView
import logging

# Service imports
from services.user_service import user_service
from services.exceptions import TeoArtServiceException, UserNotFoundError

logger = logging.getLogger(__name__)


class PendingTeachersView(ListAPIView, StandardizedAPIView):
    """List teachers pending approval"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, *args, **kwargs):
        """Get list of pending teachers using UserService"""
        try:
            pending_teachers = user_service.get_pending_teachers()
            
            return self.handle_success(
                data=pending_teachers,
                message="Pending teachers retrieved successfully"
            )
        except Exception as e:
            return self.handle_server_error(e)


class ApproveTeacherView(APIView, StandardizedAPIView):
    """Approve a teacher application"""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        """Approve teacher using UserService"""
        try:
            result = user_service.approve_teacher(user_id)
            
            return self.handle_success(
                data=result,
                message=f"Teacher {result['teacher_email']} has been approved."
            )
            
        except UserNotFoundError as e:
            return self.handle_not_found(str(e))
        except Exception as e:
            return self.handle_server_error(e)


class RejectTeacherView(APIView, StandardizedAPIView):
    """Reject a teacher application"""
    permission_classes = [IsAdminUser]

    def post(self, request, user_id):
        """Reject teacher using UserService"""
        try:
            # Get optional rejection reason from request
            reason = request.data.get('reason', None)
            
            result = user_service.reject_teacher(user_id, reason=reason)
            
            return self.handle_success(
                data=result,
                message=f"Teacher {result['teacher_email']} has been rejected."
            )
            
        except UserNotFoundError as e:
            return self.handle_not_found(str(e))
        except Exception as e:
            return self.handle_server_error(e)
