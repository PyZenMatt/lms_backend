"""
Clean TeoCoin Discount Payment Processing
Implements the correct business logic without old escrow complexity
"""

from decimal import Decimal
import logging
from rest_framework.response import Response
from rest_framework import status
from services.teocoin_discount_service import teocoin_discount_service
from courses.models import Course, CourseEnrollment

logger = logging.getLogger(__name__)


def process_teocoin_discount_payment(request, course_id, amount_eur, teocoin_discount, payment_method):
    """
    Process TeoCoin discount payment with correct business logic:
    1. Student gets immediate discount and enrollment
    2. Create discount request for teacher (platform pays gas)
    3. Teacher chooses EUR vs TEO later
    4. Return Stripe payment intent for discounted amount
    """
    try:
        course = Course.objects.get(id=course_id)
        
        # Validate wallet addresses
        wallet_address = getattr(request.user, 'wallet_address', None) or request.data.get('wallet_address')
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
        
        # Calculate discount amounts
        try:
            teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                Decimal(str(amount_eur)), 
                teocoin_discount
            )
            discount_value_eur = amount_eur * teocoin_discount / 100
            final_price = amount_eur - discount_value_eur
            
            logger.info(f"TeoCoin discount calculation - Cost: {teo_cost}, Bonus: {teacher_bonus}, Discount: €{discount_value_eur}")
        except Exception as calc_error:
            logger.error(f"TEO calculation error: {calc_error}")
            return Response({
                'success': False,
                'error': f'TEO calculation error: {str(calc_error)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate balances
        teo_service = teocoin_discount_service.teocoin_service
        student_balance = teo_service.get_balance(wallet_address)
        required_teo = teo_cost / 10**18
        
        if student_balance < required_teo:
            return Response({
                'success': False,
                'error': f'Insufficient TEO balance. Required: {required_teo:.4f} TEO, Available: {student_balance:.4f} TEO'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check reward pool for teacher bonus
        reward_pool_balance = teo_service.get_reward_pool_balance()
        required_bonus = teacher_bonus / 10**18
        
        if reward_pool_balance < required_bonus:
            return Response({
                'success': False,
                'error': 'Insufficient reward pool balance for teacher bonus'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get student signature
        student_signature = request.data.get('student_signature')
        if not student_signature:
            return Response({
                'success': False,
                'error': 'Student signature required for discount request'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ STEP 1: Create discount request (platform pays gas)
        logger.info(f"Creating discount request for course {course_id} with {teocoin_discount}% discount")
        
        discount_request = teocoin_discount_service.create_discount_request(
            student_address=wallet_address,
            teacher_address=teacher_address,
            course_id=course_id,
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
        
        # ✅ STEP 2: Student gets immediate enrollment and discount
        try:
            enrollment, created = CourseEnrollment.objects.get_or_create(
                user=request.user,
                course=course,
                defaults={
                    'payment_method': 'teocoin_discount',
                    'amount_paid': final_price,
                    'teocoin_discount_percent': teocoin_discount,
                    'teocoin_discount_amount': discount_value_eur,
                    'teocoin_discount_request_id': discount_request['request_id'],
                }
            )
            
            if not created:
                logger.warning(f"User {request.user.id} already enrolled in course {course_id}")
                return Response({
                    'success': False,
                    'error': 'You are already enrolled in this course'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"✅ Student enrolled immediately with discount: {enrollment.id}")
            
        except Exception as enrollment_error:
            logger.error(f"Enrollment error: {enrollment_error}")
            return Response({
                'success': False,
                'error': 'Failed to enroll student'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ✅ STEP 3: Create Stripe payment intent for discounted amount (if needed)
        if final_price > 0:
            try:
                import stripe
                from django.conf import settings
                
                stripe.api_key = settings.STRIPE_SECRET_KEY
                
                # Create payment intent for discounted amount
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(final_price * 100),  # Convert to cents
                    currency='eur',
                    metadata={
                        'course_id': course_id,
                        'user_id': request.user.id,
                        'teocoin_discount': teocoin_discount,
                        'discount_request_id': discount_request['request_id'],
                        'original_price': str(amount_eur),
                        'final_price': str(final_price),
                    }
                )
                
                logger.info(f"✅ Stripe payment intent created for discounted amount: €{final_price}")
                
                return Response({
                    'success': True,
                    'client_secret': payment_intent.client_secret,
                    'final_amount': final_price,
                    'original_amount': amount_eur,
                    'discount_applied': discount_value_eur,
                    'discount_percent': teocoin_discount,
                    'teo_cost': required_teo,
                    'teacher_bonus': required_bonus,
                    'discount_request_id': discount_request['request_id'],
                    'enrollment_id': enrollment.id,
                    'message': f"Student enrolled with {teocoin_discount}% discount! Teacher will choose EUR vs TEO."
                })
                
            except Exception as stripe_error:
                logger.error(f"Stripe error: {stripe_error}")
                return Response({
                    'success': False,
                    'error': 'Failed to create payment intent for discounted amount'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        else:
            # Full discount - no payment needed
            logger.info(f"✅ Full TeoCoin discount applied - no payment needed")
            
            return Response({
                'success': True,
                'final_amount': 0,
                'original_amount': amount_eur,
                'discount_applied': discount_value_eur,
                'discount_percent': teocoin_discount,
                'teo_cost': required_teo,
                'teacher_bonus': required_bonus,
                'discount_request_id': discount_request['request_id'],
                'enrollment_id': enrollment.id,
                'message': f"Course free with {teocoin_discount}% TeoCoin discount! Teacher will choose EUR vs TEO."
            })
            
    except Course.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Course not found'
        }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        logger.error(f"TeoCoin discount payment error: {e}")
        return Response({
            'success': False,
            'error': 'TeoCoin discount payment processing failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_teacher_discount_notification(teacher, course, discount_request_id, student):
    """
    Send notification to teacher about discount request
    """
    try:
        # TODO: Implement notification system
        # For now, just log the notification
        logger.info(f"📧 Teacher notification: {teacher.email} has discount request {discount_request_id} for course {course.title} from student {student.email}")
        
        # This would integrate with the notification system when available
        # notification_service.send_teacher_discount_notification(...)
        
    except Exception as e:
        logger.error(f"Failed to send teacher notification: {e}")
