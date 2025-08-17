"""
API Views for Teacher Discount Absorption System
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal, InvalidOperation
from rest_framework.permissions import IsAuthenticated
from services.db_teocoin_service import DBTeoCoinService
from django.shortcuts import get_object_or_404
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
from rewards.models import TeacherDiscountAbsorption
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
        """
        Process teacher choice for discount absorption using the service layer.
        Trust server-side calculated amounts; do not accept client-provided TEO numbers.
        Expected payload: { absorption_id: int, choice: 'teo' | 'eur' }
        """
        try:
            # Auth and role checks
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                return Response({'success': False, 'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            is_teacher = (getattr(request.user, 'role', None) == 'teacher') or request.user.is_staff
            if not is_teacher:
                return Response({'success': False, 'error': 'Only teachers can make absorption choices'}, status=status.HTTP_403_FORBIDDEN)

            # Parse input
            raw_choice = str(request.data.get('choice', '')).lower().strip()
            if raw_choice not in ('teo', 'eur', 'absorb', 'refuse'):
                return Response({'success': False, 'error': 'Invalid choice'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                absorption_id = int(request.data.get('absorption_id'))
            except (TypeError, ValueError):
                return Response({'success': False, 'error': 'Missing or invalid absorption_id'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate absorption belongs to teacher and is pending
            absorption = get_object_or_404(TeacherDiscountAbsorption, pk=absorption_id, teacher=request.user)
            if getattr(absorption, 'is_expired', False):
                absorption.auto_expire()
                return Response({'success': False, 'error': 'This opportunity has expired'}, status=status.HTTP_400_BAD_REQUEST)
            if absorption.status != 'pending':
                return Response({'success': False, 'error': f'Already processed with status {absorption.status}'}, status=status.HTTP_400_BAD_REQUEST)

            # Map choice to service expected values
            svc_choice = 'absorb' if raw_choice in ('teo', 'absorb') else 'refuse'

            # Use service to process business logic and credit TEO when needed
            processed = TeacherDiscountAbsorptionService.process_teacher_choice(absorption_id, svc_choice, request.user)

            # Build response
            data = {
                'success': True,
                'choice': 'teo' if svc_choice == 'absorb' else 'eur',
                'absorption': {
                    'id': processed.pk,
                    'status': processed.status,
                    'final_teacher_eur': float(processed.final_teacher_eur or 0),
                    'final_teacher_teo': float(processed.final_teacher_teo or 0),
                    'decided_at': processed.decided_at.isoformat() if processed.decided_at else None,
                }
            }

            # Optionally include balances if needed
            try:
                from services.db_teocoin_service import DBTeoCoinService
                db = DBTeoCoinService()
                data['new_balance'] = float(db.get_balance(request.user))
            except Exception:
                pass

            return Response(data)

        except Exception as e:
            logger.exception("Error in teacher choice endpoint")
            return Response({'success': False, 'error': f'Processing error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
