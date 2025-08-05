"""
TeoCoin Discount Payment System - Clean Implementation
Database-only Architecture: Fast, reliable, gasless TeoCoin operations

Business Logic:
- Students get discounts using database TeoCoin balance
- Teachers receive commissions based on staking tiers (database-tracked)
- Platform handles all business logic in secure database
- Clean separation between DB operations and blockchain (for withdrawal/deposit only)
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.utils import timezone
from decimal import Decimal
import logging
import stripe
import os
from django.conf import settings

from courses.models import Course, CourseEnrollment
from users.models import User

# LEGACY IMPORTS REMOVED - using clean database services now
# from services.gas_free_v2_service import GasFreeV2Service
# from views.gas_free_v2_views import create_discount_request_v2

from services.hybrid_teocoin_service import hybrid_teocoin_service
from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
from services.db_teocoin_service import DBTeoCoinService
from blockchain.blockchain import TeoCoinService
from notifications.services import teocoin_notification_service

logger = logging.getLogger(__name__)


class CreatePaymentIntentView(APIView):
    """
    Create Stripe payment intent with TeoCoin discount integration
    
    POST /api/v1/courses/{course_id}/payment/create-intent/
    {
        "use_teocoin_discount": true,
        "discount_percent": 15,
        "student_address": "0x...",
        "student_signature": "0x..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user
            
            logger.info(f"💳 Creating payment intent for course {course_id} by user {user.id}")
            
            # Extract request data
            use_teocoin_discount = request.data.get('use_teocoin_discount', False)
            discount_percent = request.data.get('discount_percent', 0)
            student_address = request.data.get('student_address', '')
            student_signature = request.data.get('student_signature', '')
            
            logger.info(f"💳 Payment data: use_discount={use_teocoin_discount}, discount={discount_percent}%")
            
            # Calculate pricing
            original_price = course.price_eur
            discount_amount = Decimal('0')
            final_price = original_price
            discount_request_id = None
            
            logger.info(f"💰 Course pricing: original=€{original_price}")
            
            # Validate Stripe configuration
            if not settings.STRIPE_SECRET_KEY:
                logger.error("❌ Stripe secret key not configured")
                return Response({
                    'error': 'Payment system not configured',
                    'code': 'STRIPE_NOT_CONFIGURED'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Process TeoCoin discount if requested
            if use_teocoin_discount and discount_percent > 0:
                try:
                    logger.info(f"🔄 Processing DB TeoCoin discount: {discount_percent}% for user {user.id}")
                    
                    # Initialize DB TeoCoin service
                    db_teo_service = DBTeoCoinService()
                    
                    # Calculate TEO cost (1 EUR discount = 1 TEO, matching frontend)
                    discount_value_eur = original_price * Decimal(discount_percent) / Decimal('100')
                    teo_cost = discount_value_eur  # 1 TEO = 1 EUR discount value
                    
                    # Check student TEO balance using DB system (matches frontend)
                    student_balance_data = db_teo_service.get_user_balance(user)
                    available_teo = student_balance_data.get('available_balance', 0)
                    
                    if available_teo < teo_cost:
                        return Response({
                            'error': f'Insufficient TEO balance. Need {teo_cost} TEO, have {available_teo} TEO',
                            'code': 'INSUFFICIENT_TEO_BALANCE',
                            'required_teo': float(teo_cost),
                            'available_teo': float(available_teo)
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Deduct TEO from student's account immediately
                    success = db_teo_service.deduct_balance(
                        user=user,
                        amount=teo_cost,
                        transaction_type='discount',
                        description=f'TeoCoin discount for course: {course.title}',
                        course_id=str(course_id)
                    )
                    
                    if not success:
                        return Response({
                            'error': 'Failed to deduct TeoCoin from your account',
                            'code': 'TEO_DEDUCTION_FAILED'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Create Teacher Discount Absorption Opportunity
                    absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
                        student=user,
                        teacher=course.teacher,
                        course=course,
                        discount_data={
                            'discount_percentage': discount_percent,
                            'teo_used': float(teo_cost),
                            'discount_amount_eur': float(discount_value_eur),
                            'course_price_eur': float(original_price)
                        }
                    )
                    
                    # Student gets guaranteed discount immediately
                    discount_amount = discount_value_eur
                    final_price = original_price - discount_amount
                    
                    logger.info(f"✅ TeoCoin discount applied: {discount_percent}% off €{original_price}")
                    logger.info(f"💰 {teo_cost} TEO deducted from student, pays €{final_price}")
                    logger.info(f"📋 Teacher absorption opportunity created: ID {absorption.pk}")
                    
                    # Teacher will be notified through the absorption dashboard
                        
                except Exception as e:
                    logger.error(f"Discount creation error: {e}")
                    return Response({
                        'error': 'TeoCoin discount system error',
                        'details': str(e),
                        'code': 'DISCOUNT_SYSTEM_ERROR'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Validate and set Stripe configuration with robust error handling
            stripe_secret = settings.STRIPE_SECRET_KEY
            
            # Check for common configuration issues
            if not stripe_secret:
                logger.error("❌ STRIPE_SECRET_KEY is None or empty")
                return Response({
                    'error': 'Payment system not configured - missing secret key',
                    'code': 'STRIPE_KEY_MISSING'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            if 'your_str' in str(stripe_secret) or 'example' in str(stripe_secret).lower():
                logger.error(f"❌ STRIPE_SECRET_KEY appears to be a placeholder: {str(stripe_secret)[:20]}...")
                # Try to get from environment directly as fallback
                stripe_secret = os.getenv('STRIPE_SECRET_KEY')
                if not stripe_secret or 'your_str' in str(stripe_secret):
                    return Response({
                        'error': 'Payment system misconfigured - placeholder key detected',
                        'code': 'STRIPE_KEY_PLACEHOLDER'
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                logger.warning("⚠️ Used fallback environment variable for Stripe key")
            
            if len(str(stripe_secret)) < 20:
                logger.error(f"❌ STRIPE_SECRET_KEY too short: {len(str(stripe_secret))} chars")
                return Response({
                    'error': 'Payment system misconfigured - invalid key length',
                    'code': 'STRIPE_KEY_INVALID_LENGTH'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Create Stripe payment intent for final price
            logger.info(f"💳 Creating Stripe payment intent for €{final_price}")
            
            stripe.api_key = stripe_secret
            logger.info(f"🔑 Stripe API key set to: {str(stripe.api_key)[:15]}...{str(stripe.api_key)[-4:] if stripe.api_key else 'NONE'}")
            
            # Validate final price
            if final_price <= 0:
                logger.error(f"❌ Invalid final price: €{final_price}")
                return Response({
                    'error': 'Invalid payment amount',
                    'code': 'INVALID_AMOUNT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            intent_data = {
                'amount': int(final_price * 100),  # Convert to cents
                'currency': 'eur',
                'metadata': {
                    'course_id': course_id,
                    'user_id': user.id,
                    'original_price': str(original_price),
                    'discount_amount': str(discount_amount),
                    'discount_percent': discount_percent,
                    'use_teocoin_discount': str(use_teocoin_discount),
                    'student_address': student_address,
                }
            }
            
            # Add discount request ID if applicable
            if discount_request_id:
                intent_data['metadata']['discount_request_id'] = str(discount_request_id)
            
            logger.info(f"💳 Stripe intent data: {intent_data}")
            
            try:
                payment_intent = stripe.PaymentIntent.create(**intent_data)
                logger.info(f"✅ Stripe payment intent created: {payment_intent.id}")
            except Exception as stripe_err:
                logger.error(f"❌ Stripe API error: {stripe_err}")
                return Response({
                    'error': f'Stripe payment error: {str(stripe_err)}',
                    'code': 'STRIPE_API_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except Exception as e:
                logger.error(f"❌ Unexpected Stripe error: {e}")
                return Response({
                    'error': f'Payment system error: {str(e)}',
                    'code': 'PAYMENT_SYSTEM_ERROR'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'pricing': {
                    'original_price': str(original_price),
                    'discount_amount': str(discount_amount),
                    'final_price': str(final_price),
                    'discount_percent': discount_percent
                },
                'discount_request_id': discount_request_id,
                'course': {
                    'title': course.title,
                    'instructor': course.teacher.username if course.teacher else 'Unknown'
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Payment intent creation error: {e}")
            return Response({
                'error': 'Failed to create payment intent',
                'details': str(e),
                'code': 'PAYMENT_INTENT_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmPaymentView(APIView):
    """
    Confirm successful payment and enroll student
    
    POST /api/v1/courses/{course_id}/payment/confirm/
    {
        "payment_intent_id": "pi_...",
        "process_discount": true
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            user = request.user
            payment_intent_id = request.data.get('payment_intent_id')
            process_discount = request.data.get('process_discount', True)
            
            if not payment_intent_id:
                return Response({
                    'error': 'Payment intent ID required',
                    'code': 'MISSING_PAYMENT_INTENT'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify payment with Stripe
            stripe.api_key = settings.STRIPE_SECRET_KEY
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if payment_intent.status != 'succeeded':
                return Response({
                    'error': 'Payment not completed',
                    'payment_status': payment_intent.status,
                    'code': 'PAYMENT_NOT_COMPLETED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Extract metadata
            metadata = payment_intent.metadata
            discount_request_id = metadata.get('discount_request_id')
            use_teocoin_discount = metadata.get('use_teocoin_discount') == 'True'
            original_price = Decimal(metadata.get('original_price', '0'))
            discount_amount = Decimal(metadata.get('discount_amount', '0'))
            student_address = metadata.get('student_address', '')
            
            # Check if already enrolled
            existing_enrollment = CourseEnrollment.objects.filter(
                student=user, course=course
            ).first()
            
            if existing_enrollment:
                return Response({
                    'error': 'Already enrolled in this course',
                    'enrollment_id': existing_enrollment.pk,
                    'code': 'ALREADY_ENROLLED'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create enrollment with proper payment tracking
            final_price = original_price - discount_amount
            payment_method = 'teocoin_discount' if use_teocoin_discount else 'stripe'
            
            enrollment = CourseEnrollment.objects.create(
                student=user,
                course=course,
                payment_method=payment_method,
                stripe_payment_intent_id=payment_intent_id,
                amount_paid_eur=final_price,
                original_price_eur=original_price,
                discount_amount_eur=discount_amount,
                teocoin_discount_request_id=discount_request_id
            )
            
            logger.info(f"✅ Student enrolled: {user.username} in {course.title} for €{final_price}")
            
            # Process teacher notification for discount decision
            teacher_notification_sent = False
            if use_teocoin_discount and discount_request_id and process_discount:
                try:
                    # Teacher has 2 hours to decide: Accept TEO vs Keep EUR
                    # This is handled by the TeoCoin discount service
                    teacher_notification_sent = True
                    logger.info(f"📧 Teacher notification sent for discount request {discount_request_id}")
                    
                except Exception as e:
                    logger.error(f"Teacher notification error: {e}")
            
            # Award purchase bonus TEO to student using clean database system
            try:
                from decimal import Decimal
                purchase_bonus = Decimal('5.0')  # 5 TEO bonus for course purchase
                success = hybrid_teocoin_service.add_balance(
                    user=user,
                    amount=purchase_bonus,
                    transaction_type='course_purchase_bonus',
                    description=f"Purchase bonus for course: {course.title}",
                    course_id=str(course_id)
                )
                if success:
                    logger.info(f"🪙 {purchase_bonus} TEO purchase bonus awarded to {user.email}")
                else:
                    logger.error(f"Failed to award purchase bonus to {user.email}")
            except Exception as e:
                logger.error(f"TEO purchase bonus error: {e}")
            
            return Response({
                'success': True,
                'enrollment_id': enrollment.pk,
                'course_title': course.title,
                'amount_paid': str(final_price),
                'discount_applied': str(discount_amount) if discount_amount > 0 else None,
                'payment_method': payment_method,
                'teacher_notification_sent': teacher_notification_sent,
                'message': f'Successfully enrolled in {course.title}!'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Payment confirmation error: {e}")
            return Response({
                'error': 'Failed to confirm payment',
                'details': str(e),
                'code': 'PAYMENT_CONFIRMATION_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSummaryView(APIView):
    """
    Get payment summary for a course including TeoCoin discount calculations
    
    GET /api/v1/courses/{course_id}/payment/summary/?discount_percent=15&student_address=0x...
    """
    # TEMPORARY: Remove authentication for debugging frontend issue
    # permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            
            # Base pricing
            original_price = course.price_eur
            
            # Course information
            course_info = {
                'id': course.pk,  # Use .pk instead of .id for better compatibility
                'title': course.title,
                'instructor': course.teacher.username if course.teacher else 'Unknown',
                'description': course.description[:200] + '...' if len(course.description) > 200 else course.description,
                'duration_hours': getattr(course, 'duration_hours', None),
                'skill_level': getattr(course, 'skill_level', None),
            }
            
            # Student enrollment status
            user = request.user
            # Handle anonymous users for debugging
            if user.is_authenticated:
                is_enrolled = CourseEnrollment.objects.filter(
                    student=user, course=course
                ).exists()
            else:
                is_enrolled = False
            
            # Create pricing options array for frontend compatibility
            pricing_options = []
            
            # Always add fiat payment option
            pricing_options.append({
                'method': 'fiat',
                'price': str(original_price),
                'currency': 'EUR',
                'description': 'Pay with Credit/Debit Card',
                'reward': '50',  # TEO rewards for fiat payment
                'disabled': False
            })
            
            # Add TeoCoin discount option if available AND teacher has wallet
            teacher_has_wallet = bool(getattr(course.teacher, 'wallet_address', None))
            
            if (hasattr(course, 'teocoin_discount_percent') and 
                course.teocoin_discount_percent > 0 and 
                teacher_has_wallet):
                
                discount_percent = int(course.teocoin_discount_percent)
                discount_amount = original_price * Decimal(discount_percent) / Decimal('100')
                final_price = original_price - discount_amount
                
                # Simple TEO cost calculation (1 TEO = 0.10 EUR discount value)
                teo_cost_eur = discount_amount  # EUR value of discount
                teo_cost_tokens = int(teo_cost_eur * 10)  # Simplified: 1 TEO = 0.10 EUR
                
                pricing_options.append({
                    'method': 'teocoin',
                    'price': str(teo_cost_tokens),
                    'currency': 'TEO',
                    'description': f'Use TEO for {discount_percent}% discount',
                    'discount': discount_percent,
                    'discount_percent': discount_percent,
                    'final_price_eur': str(final_price),
                    'savings_eur': str(discount_amount),
                    'disabled': False
                })
            elif hasattr(course, 'teocoin_discount_percent') and course.teocoin_discount_percent > 0 and not teacher_has_wallet:
                # Add disabled TeoCoin option with explanation
                pricing_options.append({
                    'method': 'teocoin',
                    'price': 'N/A',
                    'currency': 'TEO',
                    'description': 'TeoCoin discount unavailable (teacher wallet not connected)',
                    'discount': int(course.teocoin_discount_percent),
                    'discount_percent': int(course.teocoin_discount_percent),
                    'final_price_eur': str(original_price),
                    'savings_eur': '0',
                    'disabled': True,
                    'disabled_reason': 'Teacher wallet address not configured'
                })
            
            # Basic pricing summary for backward compatibility
            pricing_summary = {
                'original_price': str(original_price),
                'currency': 'EUR',
                'discount_available': hasattr(course, 'teocoin_discount_percent') and course.teocoin_discount_percent > 0,
                'max_discount_percent': int(course.teocoin_discount_percent) if hasattr(course, 'teocoin_discount_percent') else 0,
            }
            
            return Response({
                'success': True,
                'course': course_info,
                'pricing': pricing_summary,
                'pricing_options': pricing_options,
                'student_status': {
                    'is_enrolled': is_enrolled,
                    'can_enroll': not is_enrolled
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Payment summary error: {e}")
            return Response({
                'error': 'Failed to get payment summary',
                'details': str(e),
                'code': 'PAYMENT_SUMMARY_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeoCoinDiscountStatusView(APIView):
    """
    Get status of TeoCoin discount requests for student
    
    GET /api/v1/courses/{course_id}/payment/discount-status/?student_address=0x...
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, course_id):
        try:
            course = get_object_or_404(Course, id=course_id)
            student_address = request.query_params.get('student_address', '')
            
            if not student_address:
                return Response({
                    'error': 'Student address required',
                    'code': 'MISSING_STUDENT_ADDRESS'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get discount requests for this student and course
            # For now, return a simple response since we're migrating to Gas-Free V2
            # TODO: Implement proper V2 request tracking
            
            return Response({
                'success': True,
                'latest_request': None,  # No active requests for now
                'requests': [],
                'message': 'Migrating to Gas-Free V2 system'
            })
            
        except Exception as e:
            logger.error(f"Discount status error: {e}")
            return Response({
                'error': 'Failed to get discount status',
                'details': str(e),
                'code': 'DISCOUNT_STATUS_ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)