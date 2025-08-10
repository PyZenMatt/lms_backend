"""
Teacher Choice API - Handle TeoCoin discount decisions

This API allows teachers to:
1. View pending discount requests
2. Accept/decline TeoCoin discount requests  
3. Configure their choice preferences
4. View earnings comparisons for each choice
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal

from courses.models import TeacherDiscountDecision, TeacherChoicePreference
from courses.serializers import TeacherDiscountDecisionSerializer, TeacherChoicePreferenceSerializer
from users.permissions import IsTeacher
from services.teocoin_discount_service import teocoin_discount_service
from services.payment_service import payment_service


class TeacherChoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teacher discount decisions
    """
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherDiscountDecisionSerializer
    
    def get_queryset(self):
        """Return only decisions for the current teacher"""
        return TeacherDiscountDecision.objects.filter(
            teacher=self.request.user
        ).select_related('student', 'course')
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending discount requests for the teacher"""
        pending_requests = self.get_queryset().filter(
            decision='pending',
            expires_at__gt=timezone.now()
        ).order_by('-created_at')
        
        serializer = self.get_serializer(pending_requests, many=True)
        return Response({
            'success': True,
            'pending_requests': serializer.data,
            'count': pending_requests.count()
        })
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a TeoCoin discount request"""
        try:
            decision = self.get_object()
            
            # Validate decision can be made
            if decision.decision != 'pending':
                return Response({
                    'success': False,
                    'error': f'Decision already {decision.decision}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if decision.is_expired:
                return Response({
                    'success': False,
                    'error': 'Decision period has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update decision
            decision.decision = 'accepted'
            decision.decision_made_at = timezone.now()
            decision.save()
            
            # Calculate earnings breakdown
            earnings_accepted = decision.teacher_earnings_if_accepted
            earnings_declined = decision.teacher_earnings_if_declined
            
            return Response({
                'success': True,
                'message': 'TeoCoin discount request accepted!',
                'decision_id': decision.id,
                'earnings': {
                    'choice_made': 'accepted',
                    'fiat_amount': str(earnings_accepted['fiat']),
                    'teo_amount': str(earnings_accepted['teo']),
                    'total_teo': str(earnings_accepted['total_teo']),
                    'alternative_fiat': str(earnings_declined['fiat'])
                },
                'next_steps': 'Student will be notified and payment will be processed'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        """Decline a TeoCoin discount request"""
        try:
            decision = self.get_object()
            
            # Validate decision can be made
            if decision.decision != 'pending':
                return Response({
                    'success': False,
                    'error': f'Decision already {decision.decision}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if decision.is_expired:
                return Response({
                    'success': False,
                    'error': 'Decision period has expired'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update decision
            decision.decision = 'declined'
            decision.decision_made_at = timezone.now()
            decision.save()
            
            # Calculate earnings breakdown
            earnings_accepted = decision.teacher_earnings_if_accepted
            earnings_declined = decision.teacher_earnings_if_declined
            
            return Response({
                'success': True,
                'message': 'TeoCoin discount request declined',
                'decision_id': decision.id,
                'earnings': {
                    'choice_made': 'declined',
                    'fiat_amount': str(earnings_declined['fiat']),
                    'teo_amount': str(earnings_declined['teo']),
                    'alternative_fiat_loss': str(earnings_accepted['fiat']),
                    'alternative_teo_loss': str(earnings_accepted['teo'])
                },
                'next_steps': 'Student will pay full price without TeoCoin discount'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def earnings_comparison(self, request, pk=None):
        """Compare earnings for accepting vs declining"""
        try:
            decision = self.get_object()
            
            earnings_accepted = decision.teacher_earnings_if_accepted
            earnings_declined = decision.teacher_earnings_if_declined
            
            # Calculate the difference
            fiat_difference = earnings_declined['fiat'] - earnings_accepted['fiat']
            teo_gained = earnings_accepted['teo']
            
            return Response({
                'success': True,
                'decision_id': decision.id,
                'course': {
                    'title': decision.course.title if decision.course else f'Course #{decision.course.id}',
                    'price': str(decision.course_price),
                    'discount_percent': decision.discount_percentage
                },
                'student': {
                    'email': decision.student.email,
                    'teo_cost': decision.teo_cost_display
                },
                'teacher_tier': {
                    'current_tier': decision.teacher_staking_tier,
                    'commission_rate': f"{decision.teacher_commission_rate}%"
                },
                'comparison': {
                    'accept_teocoin': {
                        'fiat_earnings': str(earnings_accepted['fiat']),
                        'teo_earnings': str(earnings_accepted['teo']),
                        'description': f'€{earnings_accepted["fiat"]} + {earnings_accepted["teo"]} TEO'
                    },
                    'decline_teocoin': {
                        'fiat_earnings': str(earnings_declined['fiat']),
                        'teo_earnings': str(earnings_declined['teo']),
                        'description': f'€{earnings_declined["fiat"]} + 0 TEO'
                    },
                    'trade_off': {
                        'fiat_loss_if_accept': str(fiat_difference),
                        'teo_gain_if_accept': str(teo_gained),
                        'recommendation': 'accept' if teo_gained > fiat_difference * 2 else 'consider'
                    }
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeacherPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing teacher choice preferences
    """
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherChoicePreferenceSerializer
    
    def get_queryset(self):
        """Return preference for the current teacher"""
        return TeacherChoicePreference.objects.filter(teacher=self.request.user)
    
    def get_object(self):
        """Get or create preference for the current teacher"""
        preference, created = TeacherChoicePreference.objects.get_or_create(
            teacher=self.request.user
        )
        return preference
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current teacher preferences"""
        preference = self.get_object()
        serializer = self.get_serializer(preference)
        
        return Response({
            'success': True,
            'preferences': serializer.data,
            'description': {
                'always_accept': 'Automatically accept all TeoCoin discounts',
                'always_decline': 'Automatically decline all TeoCoin discounts', 
                'manual': 'Review each discount request manually',
                'threshold_based': f'Auto-accept if TEO amount > {preference.minimum_teo_threshold or 0}'
            }
        })
    
    @action(detail=False, methods=['post'])
    def update_preference(self, request):
        """Update teacher choice preferences"""
        try:
            preference = self.get_object()
            
            # Validate preference choice
            valid_choices = [choice[0] for choice in TeacherChoicePreference.PREFERENCE_CHOICES]
            new_preference = request.data.get('preference')
            
            if new_preference not in valid_choices:
                return Response({
                    'success': False,
                    'error': f'Invalid preference. Must be one of: {valid_choices}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Update preference
            preference.preference = new_preference
            
            # Handle threshold-based preference
            if new_preference == 'threshold_based':
                threshold = request.data.get('minimum_teo_threshold')
                if not threshold or Decimal(str(threshold)) <= 0:
                    return Response({
                        'success': False,
                        'error': 'minimum_teo_threshold required for threshold_based preference'
                    }, status=status.HTTP_400_BAD_REQUEST)
                preference.minimum_teo_threshold = Decimal(str(threshold))
            
            # Update notification preferences
            if 'email_notifications' in request.data:
                preference.email_notifications = bool(request.data['email_notifications'])
            if 'immediate_notifications' in request.data:
                preference.immediate_notifications = bool(request.data['immediate_notifications'])
            
            preference.save()
            
            serializer = self.get_serializer(preference)
            return Response({
                'success': True,
                'message': 'Preferences updated successfully',
                'preferences': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get teacher decision statistics"""
        try:
            # Get all decisions for this teacher
            decisions = TeacherDiscountDecision.objects.filter(teacher=request.user)
            
            total = decisions.count()
            accepted = decisions.filter(decision='accepted').count()
            declined = decisions.filter(decision='declined').count()
            pending = decisions.filter(decision='pending', expires_at__gt=timezone.now()).count()
            expired = decisions.filter(decision='expired').count() + decisions.filter(
                decision='pending', expires_at__lte=timezone.now()
            ).count()
            
            # Calculate earnings
            accepted_decisions = decisions.filter(decision='accepted')
            total_fiat_earned = sum([d.teacher_earnings_if_accepted['fiat'] for d in accepted_decisions])
            total_teo_earned = sum([d.teacher_earnings_if_accepted['teo'] for d in accepted_decisions])
            
            declined_decisions = decisions.filter(decision='declined')
            total_fiat_from_declined = sum([d.teacher_earnings_if_declined['fiat'] for d in declined_decisions])
            
            return Response({
                'success': True,
                'statistics': {
                    'total_requests': total,
                    'accepted': accepted,
                    'declined': declined,
                    'pending': pending,
                    'expired': expired,
                    'acceptance_rate': f'{(accepted/total*100):.1f}%' if total > 0 else '0%'
                },
                'earnings': {
                    'total_fiat_from_teocoin': str(total_fiat_earned),
                    'total_teo_earned': str(total_teo_earned),
                    'total_fiat_from_declined': str(total_fiat_from_declined),
                    'teo_value_estimate': f'{total_teo_earned * Decimal("1.2"):.2f} EUR' # Estimate TEO value
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
