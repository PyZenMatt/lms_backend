from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from django.contrib.auth import get_user_model
from django.db import models
import logging

from users.permissions import IsAdminOrApprovedTeacherOrReadOnly, IsTeacher
from courses.models import Course
from courses.serializers import CourseSerializer
from services.course_service import course_service
from services.exceptions import CourseNotFoundError, TeoArtServiceException

logger = logging.getLogger(__name__)


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApprovedTeacherOrReadOnly]
    
    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries with select_related and prefetch_related
        return Course.objects.select_related('teacher').prefetch_related(
            'students', 'lessons', 'enrollments'
        ).annotate(
            student_count=models.Count('students')
        )


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApprovedTeacherOrReadOnly]
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    filterset_fields = ['teacher', 'price_eur', 'category']
    search_fields = ['title', 'description', 'teacher__username']
    ordering_fields = ['created_at', 'price_eur', 'student_count']
    ordering = ['-created_at']  # Default ordering by newest

    def get_queryset(self):
        # Mostra solo corsi approvati per utenti non admin
        user = self.request.user
        if user.is_staff or user.is_superuser:
            # Admin può vedere tutti i corsi
            queryset = Course.objects.all()
        else:
            # Altri utenti vedono solo corsi approvati
            queryset = Course.objects.filter(is_approved=True)
            
        queryset = queryset.annotate(
            student_count=models.Count('students')
        ).prefetch_related('students', 'teacher', 'lessons')
        
        # Filtro per categoria se specificato tramite query params
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        return queryset

    def perform_create(self, serializer):
        try:
            user = self.request.user
            if getattr(user, 'role', None) != 'teacher':
                raise PermissionDenied("Solo i maestri possono creare corsi")
            
            User = get_user_model()
            user_obj = User.objects.get(pk=user.pk)
            if not getattr(user_obj, 'is_approved', False):
                raise PermissionDenied("Solo i teacher approvati possono creare corsi. Aspetta l'approvazione dell'admin.")
            
            serializer.save(teacher=user_obj)
        except PermissionDenied:
            raise  # Re-raise permission errors
        except Exception as e:
            logger.error(f"Error in perform_create: {e}")
            raise


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdminOrApprovedTeacherOrReadOnly]
    queryset = Course.objects.all()

    def get_object(self):
        try:
            obj = super().get_object()
            user = self.request.user
            # Admin può vedere tutto, altri solo corsi approvati
            if not (user.is_staff or user.is_superuser) and not obj.is_approved:
                raise PermissionDenied("Corso non approvato")
            return obj
        except Exception as e:
            logger.error(f"Error in get_object: {e}")
            raise

    def perform_update(self, serializer):
        try:
            if serializer.instance.teacher != self.request.user:
                raise PermissionDenied("Non sei il proprietario di questo corso")
            serializer.save()
        except PermissionDenied:
            raise  # Re-raise permission errors
        except Exception as e:
            logger.error(f"Error in perform_update: {e}")
            raise


class CreateCourseAPI(generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsTeacher]

    def perform_create(self, serializer):
        try:
            serializer.save(teacher=self.request.user)
        except Exception as e:
            logger.error(f"Error in CreateCourseAPI perform_create: {e}")
            raise


class CourseListAPIView(generics.ListAPIView):
    """
    API view for listing courses using CourseService
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        try:
            courses_data = course_service.get_available_courses(user=request.user)
            return Response({
                'courses': courses_data,
                'count': len(courses_data),
                'success': True
            })
        except TeoArtServiceException as e:
            logger.warning(f"Service error in CourseListAPIView: {e}")
            return Response(
                {'error': str(e)},
                status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in CourseListAPIView: {e}")
            return Response(
                {'error': 'An error occurred while retrieving courses'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseDetailAPIView(generics.RetrieveAPIView):
    """
    API view for course details using CourseService
    """
    permission_classes = [IsAuthenticated]
    
    def retrieve(self, request, *args, **kwargs):
        course_id = kwargs.get('pk')
        try:
            if not course_id:
                return Response(
                    {'error': 'Course ID is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            course_details = course_service.get_course_details(int(course_id), user=request.user)
            return Response({
                **course_details,
                'success': True
            })
        except (ValueError, TypeError):
            logger.warning(f"Invalid course ID: {course_id}")
            return Response(
                {'error': 'Invalid course ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except CourseNotFoundError:
            logger.info(f"Course not found: {course_id}")
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except TeoArtServiceException as e:
            logger.warning(f"Service error in CourseDetailAPIView: {e}")
            return Response(
                {'error': str(e)},
                status=e.status_code if hasattr(e, 'status_code') else status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in CourseDetailAPIView: {e}")
            return Response(
                {'error': 'An error occurred while retrieving course details'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )