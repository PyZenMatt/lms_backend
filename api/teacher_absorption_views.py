"""
API Views for Teacher Discount Absorption System
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rewards.models import TeacherDiscountAbsorption
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
import logging

logger = logging.getLogger(__name__)


class TeacherPendingAbsorptionsView(APIView):
    """
    Get pending discount absorption opportunities for the teacher
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Check if user is a teacher (has role='teacher' OR has created courses OR is staff)
            is_teacher = (
                getattr(request.user, 'role', None) == 'teacher' or
                request.user.is_staff or
                hasattr(request.user, 'created_courses') and request.user.created_courses.exists()
            )
            
            if not is_teacher:
                return Response({
                    'success': False,
                    'error': 'Only teachers can access absorption opportunities'
                }, status=status.HTTP_403_FORBIDDEN)
            
            service = TeacherDiscountAbsorptionService()
            pending_absorptions = service.get_pending_absorptions(request.user)
            
            # Serialize the data
            absorptions_data = []
            for absorption in pending_absorptions:
                absorptions_data.append({
                    'id': absorption.pk,
                    'course': {
                        'id': absorption.course.id,
                        'title': absorption.course.title,
                        'price': float(absorption.course_price_eur)
                    },
                    'student': {
                        'username': absorption.student.username,
                        'email': absorption.student.email
                    },
                    'discount': {
                        'percentage': absorption.discount_percentage,
                        'teo_used': float(absorption.teo_used_by_student),
                        'eur_amount': float(absorption.discount_amount_eur)
                    },
                    'options': {
                        'option_a': {
                            'description': 'Standard EUR Commission',
                            'teacher_eur': float(absorption.option_a_teacher_eur),
                            'teacher_teo': 0,
                            'platform_eur': float(absorption.option_a_platform_eur)
                        },
                        'option_b': {
                            'description': 'Absorb Discount for TEO',
                            'teacher_eur': float(absorption.option_b_teacher_eur),
                            'teacher_teo': float(absorption.option_b_teacher_teo),
                            'platform_eur': float(absorption.option_b_platform_eur)
                        }
                    },
                    'timing': {
                        'created_at': absorption.created_at.isoformat(),
                        'expires_at': absorption.expires_at.isoformat(),
                        'hours_remaining': absorption.hours_remaining
                    }
                })
            
            return Response({
                'success': True,
                'pending_absorptions': absorptions_data,
                'count': len(absorptions_data)
            })
            
        except Exception as e:
            logger.error(f"Error fetching pending absorptions: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch pending absorptions'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherMakeAbsorptionChoiceView(APIView):
    """
    Process teacher's choice for a discount absorption opportunity
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Check if user is a teacher (has role='teacher' OR has created courses OR is staff)
            is_teacher = (
                getattr(request.user, 'role', None) == 'teacher' or
                request.user.is_staff or
                hasattr(request.user, 'created_courses') and request.user.created_courses.exists()
            )
            
            if not is_teacher:
                return Response({
                    'success': False,
                    'error': 'Only teachers can make absorption choices'
                }, status=status.HTTP_403_FORBIDDEN)
            
            absorption_id = request.data.get('absorption_id')
            choice = request.data.get('choice')  # 'absorb' or 'refuse'
            
            if not absorption_id:
                return Response({
                    'success': False,
                    'error': 'absorption_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if choice not in ['absorb', 'refuse']:
                return Response({
                    'success': False,
                    'error': 'choice must be either "absorb" or "refuse"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            service = TeacherDiscountAbsorptionService()
            absorption = service.process_teacher_choice(
                absorption_id=absorption_id,
                choice=choice,
                teacher=request.user
            )
            
            return Response({
                'success': True,
                'absorption': {
                    'id': absorption.pk,
                    'status': absorption.status,
                    'choice_made': choice,
                    'final_teacher_eur': float(absorption.final_teacher_eur) if absorption.final_teacher_eur else 0,
                    'final_teacher_teo': float(absorption.final_teacher_teo),
                    'final_platform_eur': float(absorption.final_platform_eur) if absorption.final_platform_eur else 0,
                    'decided_at': absorption.decided_at.isoformat() if absorption.decided_at else None
                },
                'message': f'Successfully {"absorbed discount for TEO" if choice == "absorb" else "chose EUR commission"}'
            })
            
        except ValueError as ve:
            return Response({
                'success': False,
                'error': str(ve)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error processing absorption choice: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to process absorption choice'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherAbsorptionHistoryView(APIView):
    """
    Get teacher's absorption history and statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Check if user is a teacher (has role='teacher' OR has created courses OR is staff)
            is_teacher = (
                getattr(request.user, 'role', None) == 'teacher' or
                request.user.is_staff or
                hasattr(request.user, 'created_courses') and request.user.created_courses.exists()
            )
            
            if not is_teacher:
                return Response({
                    'success': False,
                    'error': 'Only teachers can access absorption history'
                }, status=status.HTTP_403_FORBIDDEN)
            
            days = int(request.GET.get('days', 30))
            service = TeacherDiscountAbsorptionService()
            
            # Get history and stats
            history = service.get_teacher_absorption_history(request.user, days)
            stats = service.get_teacher_absorption_stats(request.user, days)
            
            # Serialize history
            history_data = []
            for absorption in history:
                history_data.append({
                    'id': absorption.pk,
                    'course_title': absorption.course.title,
                    'student_username': absorption.student.username,
                    'status': absorption.status,
                    'discount_percentage': absorption.discount_percentage,
                    'teo_used': float(absorption.teo_used_by_student),
                    'final_teacher_eur': float(absorption.final_teacher_eur) if absorption.final_teacher_eur else 0,
                    'final_teacher_teo': float(absorption.final_teacher_teo),
                    'created_at': absorption.created_at.isoformat(),
                    'decided_at': absorption.decided_at.isoformat() if absorption.decided_at else None
                })
            
            return Response({
                'success': True,
                'history': history_data,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Error fetching absorption history: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch absorption history'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAbsorptionOverviewView(APIView):
    """
    Admin view for platform absorption statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Only admin/staff should access this
            if not request.user.is_staff:
                return Response({
                    'success': False,
                    'error': 'Only admin users can access platform statistics'
                }, status=status.HTTP_403_FORBIDDEN)
            
            service = TeacherDiscountAbsorptionService()
            platform_savings = service.calculate_platform_savings()
            
            # Get recent absorptions for overview
            recent_absorptions = TeacherDiscountAbsorption.objects.filter(
                status__in=['absorbed', 'refused', 'expired']
            ).select_related('teacher', 'course').order_by('-created_at')[:20]
            
            recent_data = []
            for absorption in recent_absorptions:
                recent_data.append({
                    'id': absorption.pk,
                    'teacher': absorption.teacher.username,
                    'course': absorption.course.title,
                    'status': absorption.status,
                    'discount_eur': float(absorption.discount_amount_eur),
                    'final_teacher_eur': float(absorption.final_teacher_eur) if absorption.final_teacher_eur else 0,
                    'final_teacher_teo': float(absorption.final_teacher_teo),
                    'created_at': absorption.created_at.isoformat(),
                    'decided_at': absorption.decided_at.isoformat() if absorption.decided_at else None
                })
            
            return Response({
                'success': True,
                'platform_savings': platform_savings,
                'recent_absorptions': recent_data
            })
            
        except Exception as e:
            logger.error(f"Error fetching admin absorption overview: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to fetch absorption overview'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
