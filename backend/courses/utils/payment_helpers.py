"""
Payment Helper Functions for TeoCoin Discount System
Phase 3: Business Logic Integration
"""

import logging
from decimal import Decimal
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

from services.teocoin_discount_service import teocoin_discount_service

logger = logging.getLogger(__name__)


def process_teocoin_discount_payment(request, course, amount_eur, teocoin_discount, payment_method):
    """
    ✅ PHASE 3: Process TeoCoin discount payment with correct business logic
    
    Flow:
    1. Student signs discount request (gas-free)
    2. Backend creates smart contract discount request (platform pays gas)
    3. Student pays discounted EUR amount immediately
    4. Student gets course enrollment immediately
    5. Teacher gets notification to choose EUR vs TEO
    6. Platform absorbs discount cost until teacher decides
    
    Args:
        request: Django request object
        course: Course model instance
        amount_eur: Original course price in EUR
        teocoin_discount: Discount percentage (5-15%)
        payment_method: 'fiat_with_teocoin_discount'
        
    Returns:
        Response object with payment intent or error
    """
    try:
        # Get wallet addresses
        wallet_address = getattr(request.user, 'wallet_address', None)
        if not wallet_address:
            wallet_address = request.data.get('wallet_address')
        
        if not wallet_address:
            return Response({
                'success': False,
                'error': 'Please connect your wallet to use TeoCoin discounts'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        teacher_address = getattr(course.teacher, 'wallet_address', None)
        if not teacher_address:
            return Response({
                'success': False,
                'error': 'Teacher wallet not configured for TeoCoin discounts'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate discount amounts using our service
        try:
            teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                Decimal(str(amount_eur)), 
                teocoin_discount
            )
            discount_value_eur = amount_eur * teocoin_discount / 100
            required_teo = teo_cost / 10**18
            required_bonus = teacher_bonus / 10**18
            
            logger.info(f"TeoCoin calculation - Cost: {required_teo:.4f} TEO, Bonus: {required_bonus:.4f} TEO, Discount: €{discount_value_eur}")
        except Exception as calc_error:
            logger.error(f"TEO calculation error: {calc_error}")
            return Response({
                'success': False,
                'error': f'TEO calculation error: {str(calc_error)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check student TeoCoin balance
        teo_service = teocoin_discount_service.teocoin_service
        student_balance = teo_service.get_balance(wallet_address)
        
        if student_balance < required_teo:
            return Response({
                'success': False,
                'error': f'Insufficient TEO balance. Required: {required_teo:.4f} TEO, Available: {student_balance:.4f} TEO'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check reward pool balance for teacher bonus
        reward_pool_balance = teo_service.get_reward_pool_balance()
        
        if reward_pool_balance < required_bonus:
            return Response({
                'success': False,
                'error': 'Insufficient reward pool balance for teacher bonus'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ NEW BUSINESS LOGIC: Create discount request via smart contract
        student_signature = request.data.get('student_signature')
        if not student_signature:
            return Response({
                'success': False,
                'error': 'Student signature required for discount request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create discount request (platform pays gas)
        discount_request = teocoin_discount_service.create_discount_request(
            student_address=wallet_address,
            teacher_address=teacher_address,
            course_id=course.id,
            course_price=Decimal(str(amount_eur)),
            discount_percent=teocoin_discount,
            student_signature=student_signature
        )
        
        if not discount_request.get('success'):
            return Response({
                'success': False,
                'error': discount_request.get('error', 'Failed to create discount request')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"✅ Discount request created: {discount_request['request_id']}")
        
        # Calculate final price after discount (student pays discounted amount immediately)
        final_price = amount_eur - discount_value_eur
        
        # ✅ Create Stripe payment intent for the discounted amount
        import stripe
        from django.conf import settings
        stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        
        # Create Stripe payment intent with TeoCoin discount metadata
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(final_price * 100),  # Stripe uses cents
                currency='eur',
                payment_method_types=['card'],
                metadata={
                    'course_id': course.id,
                    'user_id': request.user.id,
                    'payment_type': 'fiat_with_teocoin_discount',
                    'teocoin_discount_applied': 'true',
                    'teocoin_discount_percent': str(teocoin_discount),
                    'teocoin_discount_request_id': str(discount_request['request_id']),
                    'student_wallet_address': wallet_address,
                    'teacher_wallet_address': teacher_address,
                    'discount_amount_eur': str(discount_value_eur),
                    'original_price_eur': str(amount_eur),
                    'course_title': course.title,
                    'student_email': request.user.email
                },
                description=f"Course: {course.title} (TeoCoin {teocoin_discount}% discount)"
            )
            
            return Response({
                'success': True,
                'payment_method': 'fiat_with_teocoin_discount',
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id,
                'final_amount': float(final_price),
                'discount_applied': float(discount_value_eur),
                'teo_cost': float(required_teo),
                'teacher_bonus': float(required_bonus),
                'discount_request_id': discount_request['request_id'],
                'message': f'✅ Discount applied! Student pays €{final_price:.2f}. Teacher will choose EUR vs TEO.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Failed to create discounted payment intent: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to create payment intent: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"TeoCoin discount payment processing failed: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error during discount processing'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_teocoin_discount_completion(payment_intent_metadata):
    """
    Handle completion of TeoCoin discount payment
    Called when Stripe payment is confirmed
    
    Args:
        payment_intent_metadata: Stripe payment intent metadata
    
    Returns:
        Dict with success status and enrollment info
    """
    try:
        # Extract metadata
        discount_request_id = payment_intent_metadata.get('teocoin_discount_request_id')
        course_id = payment_intent_metadata.get('course_id')
        user_id = payment_intent_metadata.get('user_id')
        
        if not all([discount_request_id, course_id, user_id]):
            logger.error("Missing required metadata for TeoCoin discount completion")
            return {'success': False, 'error': 'Missing payment metadata'}
        
        # ✅ Student gets enrolled immediately (guaranteed discount)
        from courses.models import Course, CourseEnrollment
        from django.contrib.auth.models import User
        
        course = Course.objects.get(id=course_id)
        user = User.objects.get(id=user_id)
        
        # Create enrollment
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'payment_method': 'fiat_with_teocoin_discount',
                'amount_paid': payment_intent_metadata.get('final_amount', course.price_eur),
                'teocoin_discount_applied': True,
                'teocoin_discount_request_id': discount_request_id
            }
        )
        
        if created:
            logger.info(f"✅ Student {user.email} enrolled in course {course.title} with TeoCoin discount")
        
        # ✅ Send notification to teacher about EUR vs TEO choice
        try:
            from notifications.services import send_teacher_discount_notification
            send_teacher_discount_notification(
                teacher=course.teacher,
                student=user,
                course=course,
                discount_request_id=discount_request_id,
                teo_amount=payment_intent_metadata.get('teo_cost'),
                discount_percent=payment_intent_metadata.get('teocoin_discount_percent')
            )
            logger.info(f"✅ Teacher notification sent for discount request {discount_request_id}")
        except Exception as notification_error:
            logger.warning(f"Teacher notification failed: {notification_error}")
            # Don't fail the payment for notification issues
        
        return {
            'success': True,
            'enrollment': {
                'id': enrollment.id,
                'course_title': course.title,
                'discount_applied': True,
                'teacher_notification_sent': True
            }
        }
        
    except Exception as e:
        logger.error(f"TeoCoin discount completion failed: {str(e)}")
        return {'success': False, 'error': str(e)}
