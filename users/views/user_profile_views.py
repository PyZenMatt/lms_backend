"""
User profile management views
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from courses.models import CourseEnrollment
from authentication.serializers import RegisterSerializer
from users.models import User
from ..serializers import UserProfileSerializer
import logging

# Service imports
from services.user_service import user_service
from services.exceptions import TeoArtServiceException, UserNotFoundError

logger = logging.getLogger(__name__)


class RegisterView(generics.CreateAPIView):
    """User registration view"""
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get user profile with course information"""
    try:
        profile_data = user_service.get_user_profile_data(request.user)
        return Response(profile_data)
    except UserNotFoundError as e:
        logger.warning(f"User not found in user_profile: {e}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_404_NOT_FOUND
        )
    except TeoArtServiceException as e:
        logger.warning(f"Service error in user_profile: {e}")
        return Response(
            {'error': str(e)},
            status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Unexpected error in user_profile: {e}")
        return Response(
            {'error': 'An error occurred while retrieving profile'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class UserProfileView(APIView):
    """User profile CRUD operations"""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """Get user profile details"""
        try:
            profile_data = user_service.get_user_profile_data(request.user)
            return Response(profile_data)
        except TeoArtServiceException as e:
            logger.warning(f"Service error in UserProfileView.get: {e}")
            return Response(
                {'error': str(e)},
                status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in UserProfileView.get: {e}")
            return Response(
                {"error": "Error retrieving profile"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request):
        """Update user profile"""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
