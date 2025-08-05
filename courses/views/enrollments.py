from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.conf import settings
from decimal import Decimal
import uuid
import logging

from courses.models import Course
from rewards.models import BlockchainTransaction
from courses.serializers import StudentCourseSerializer
from users.permissions import IsTeacher

# Service Layer imports
from services.payment_service import payment_service
from services.exceptions import (
    TeoArtServiceException, 
    UserNotFoundError, 
    CourseNotFoundError,
    InsufficientTeoCoinsError
)

logger = logging.getLogger(__name__)


class PurchaseCourseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        """Handle course purchase using PaymentService"""
        try:
            wallet_address = request.data.get('wallet_address')
            transaction_hash = request.data.get('transaction_hash')
            payment_confirmed = request.data.get('payment_confirmed', False)

            # Validate required data
            if not wallet_address:
                return Response({
                    "error": "Wallet address is required for purchase",
                    "action_required": "provide_wallet"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Use PaymentService to initiate purchase
            if not payment_confirmed or not transaction_hash:
                try:
                    # Initiate purchase workflow
                    result = payment_service.initiate_course_purchase(
                        user_id=request.user.id,
                        course_id=course_id,
                        wallet_address=wallet_address
                    )
                    
                    return Response(result, status=status.HTTP_402_PAYMENT_REQUIRED)
                    
                except InsufficientTeoCoinsError as e:
                    return Response({
                        "error": str(e),
                        "required": getattr(e, 'required', None),
                        "available": getattr(e, 'available', None)
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                except (UserNotFoundError, CourseNotFoundError, TeoArtServiceException) as e:
                    return Response({
                        "error": str(e)
                    }, status=getattr(e, 'status_code', 400))
            
            # Complete purchase with transaction hash
            try:
                result = payment_service.complete_course_purchase(
                    user_id=request.user.id,
                    course_id=course_id,
                    transaction_hash=transaction_hash,
                    wallet_address=wallet_address
                )
                
                return Response({
                    "message": result['message'],
                    "course_title": result['course_title'],
                    "total_paid": result['total_paid'],
                    "teacher_received": result['teacher_received'],
                    "platform_commission": result['platform_commission'],
                    "transaction_hash": result['transaction_hash'],
                    "wallet_address": wallet_address,
                    "blockchain_verified": True,
                    "payment_breakdown": {
                        "student_paid": result['total_paid'],
                        "teacher_received": result['teacher_received'],
                        "platform_commission": result['platform_commission'],
                        "commission_rate": "50%"  # Updated to new business model
                    },
                    "enrollment_confirmed": result['enrollment_confirmed']
                }, status=status.HTTP_200_OK)
                
            except (UserNotFoundError, CourseNotFoundError, TeoArtServiceException) as e:
                return Response({
                    "error": str(e)
                }, status=getattr(e, 'status_code', 400))

        except Exception as e:
            logger.error(f"PurchaseCourseView service failed: {str(e)}")
            # Return error response
            return Response({
                "error": "Payment service temporarily unavailable. Please try again later.",
                "details": str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _verify_course_payment_transaction(self, tx_hash, student_address, teacher_address, course_price):
        """
        Verifica che il pagamento del corso sia stato effettuato correttamente:
        - Cerca le transazioni nei nostri record (potrebbero essere multiple per un corso)
        - Verifica che lo studente abbia pagato il prezzo completo
        - Verifica che il teacher abbia ricevuto l'importo netto
        - Verifica che la reward pool abbia ricevuto la commissione
        """
        try:
            from rewards.models import BlockchainTransaction
            from decimal import Decimal
            
            # Cerca transazioni correlate al transaction hash principale
            related_transactions = BlockchainTransaction.objects.filter(
                transaction_hash=tx_hash
            )
            
            if related_transactions.exists():
                # Verifica se è una transazione registrata nei nostri record
                for tx in related_transactions:
                    if (tx.from_address and tx.to_address and
                        tx.from_address.lower() == student_address.lower() and
                        tx.to_address.lower() == teacher_address.lower() and
                        abs(tx.amount) >= course_price * Decimal('0.85')):  # Teacher riceve almeno 85%
                        logger.info(f"Found valid course payment transaction: {tx_hash}")
                        return True
                
            # Fallback: usa la logica blockchain standard
            return self._verify_blockchain_transaction(tx_hash, student_address, teacher_address, course_price)
            
        except Exception as e:
            logger.error(f"Error verifying course payment transaction {tx_hash}: {str(e)}")
            return False

    def _verify_blockchain_transaction(self, tx_hash, from_address, to_address, expected_amount):
        """Verifica che la transazione sulla blockchain sia valida"""
        try:
            # Check if this is a simulated transaction hash (for testing)
            if tx_hash.startswith("0x") and len(tx_hash) == 66:
                # Check if this is a simulated transaction in our database
                from rewards.models import BlockchainTransaction
                simulated_tx = BlockchainTransaction.objects.filter(
                    transaction_hash=tx_hash,
                    transaction_type='simulated_payment',
                    status='completed'
                ).first()
                
                if simulated_tx:
                    # Verify the simulated transaction details match
                    simulated_from = simulated_tx.from_address.lower() if simulated_tx.from_address else ""
                    simulated_to = simulated_tx.to_address.lower() if simulated_tx.to_address else ""
                    request_from = from_address.lower() if from_address else ""
                    request_to = to_address.lower() if to_address else ""
                    
                    if (simulated_from == request_from and 
                        simulated_to == request_to and
                        simulated_tx.amount >= expected_amount):
                        logger.info(f"Valid simulated transaction found: {tx_hash}")
                        return True
                    else:
                        logger.warning(f"Simulated transaction details don't match: {tx_hash}")
                        return False
            
            # Standard blockchain verification for real transactions
            from blockchain.views import teocoin_service
            
            # Ottieni la ricevuta della transazione
            receipt = teocoin_service.w3.eth.get_transaction_receipt(tx_hash)
            
            if receipt["status"] != 1:  # Transazione fallita
                logger.warning(f"Transaction failed: {tx_hash}")
                return False
            
            # Ottieni i dettagli della transazione
            tx = teocoin_service.w3.eth.get_transaction(tx_hash)
            
            # Verifica che sia una transazione verso il contratto TeoCoin
            tx_to = tx.get("to")
            contract_addr = getattr(teocoin_service, 'contract_address', None)
            if tx_to and contract_addr and str(tx_to).lower() != str(contract_addr).lower():
                logger.warning(f"Transaction not to TeoCoin contract: {tx_hash}")
                return False
            
            # Decodifica i log per verificare il trasferimento
            transfer_events = teocoin_service.contract.events.Transfer().process_receipt(receipt)
            
            for event in transfer_events:
                event_from = event.args['from'].lower()
                event_to = event.args['to'].lower()
                event_amount = teocoin_service.w3.from_wei(event.args['value'], 'ether')
                
                # Verifica che il trasferimento corrisponda
                if (event_from == from_address.lower() and 
                    (to_address is None or event_to == to_address.lower()) and
                    Decimal(str(event_amount)) >= expected_amount):
                    logger.info(f"Valid transfer found: {event_amount} TEO from {event_from} to {event_to}")
                    return True
            
            logger.warning(f"No valid transfer event found in transaction: {tx_hash}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying transaction {tx_hash}: {str(e)}")
            return False


class StudentEnrolledCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user
        enrolled_courses = Course.objects.filter(students=student, is_approved=True)
        serializer = StudentCourseSerializer(enrolled_courses, many=True)
        return Response(serializer.data)


class TeacherCourseStudentsView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def get(self, request):
        teacher = request.user
        courses = Course.objects.filter(teacher=teacher).prefetch_related('students')

        data = []
        for course in courses:
            students = course.students.all()
            student_data = [
                {"id": s.id, "username": s.username, "email": s.email}
                for s in students
            ]
            data.append({
                "course_id": course.pk,
                "course_title": course.title,
                "students": student_data
            })

        return Response(data)


class CourseEnrollmentView(APIView):
    """Handle course enrollment with Stripe payment"""
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        """Enroll student in course with payment processing"""
        try:
            course = get_object_or_404(Course, id=course_id)
            
            payment_method = request.data.get('payment_method', 'stripe')
            amount = Decimal(str(request.data.get('amount', course.price_eur)))
            discount_applied = request.data.get('discount_applied', False)
            discount_info = request.data.get('discount_info', None)
            
            logger.info(f"Course enrollment request - Course: {course_id}, User: {request.user.id}, Amount: {amount}")
            
            # Check if user is already enrolled
            if course.students.filter(id=request.user.id).exists():
                return Response({
                    'success': False,
                    'error': 'Sei già iscritto a questo corso'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Enroll student in course
                course.students.add(request.user)
                
                # Create enrollment record/transaction
                enrollment_data = {
                    'course_id': course_id,
                    'student_id': request.user.id,
                    'amount_paid': float(amount),
                    'payment_method': payment_method,
                    'discount_applied': discount_applied,
                    'discount_info': discount_info
                }
                
                logger.info(f"Student {request.user.id} successfully enrolled in course {course_id}")
                
                # Award TeoCoin reward if configured
                if course.teocoin_reward > 0:
                    try:
                        from services.hybrid_teocoin_service import hybrid_teocoin_service
                        reward_result = hybrid_teocoin_service.credit_user(
                            user=request.user,
                            amount=course.teocoin_reward,
                            reason=f'Course enrollment reward: {course.title}'
                        )
                        logger.info(f"TeoCoin reward granted: {course.teocoin_reward} TEO")
                    except Exception as e:
                        logger.error(f"Failed to grant TeoCoin reward: {e}")
                
                # Create discount absorption opportunity if discount was applied
                if discount_applied and discount_info and course.teacher:
                    try:
                        from services.teacher_discount_absorption_service import TeacherDiscountAbsorptionService
                        
                        absorption_data = {
                            'course_price_eur': float(course.price_eur),
                            'discount_percentage': discount_info.get('discount_percentage', 0),
                            'teo_used': discount_info.get('teo_used', 0),
                            'discount_amount_eur': discount_info.get('discount_amount_eur', 0)
                        }
                        
                        absorption = TeacherDiscountAbsorptionService.create_absorption_opportunity(
                            student=request.user,
                            teacher=course.teacher,
                            course=course,
                            discount_data=absorption_data
                        )
                        
                        logger.info(f"Discount absorption opportunity created: {absorption.pk}")
                        
                    except Exception as e:
                        logger.error(f"Failed to create discount absorption opportunity: {e}")
                        # Don't fail the enrollment if this fails
                
                return Response({
                    'success': True,
                    'message': 'Iscrizione al corso completata con successo',
                    'enrollment': enrollment_data,
                    'course': {
                        'id': course.pk,
                        'title': course.title,
                        'description': course.description
                    }
                })
                
        except Exception as e:
            logger.error(f"Error in course enrollment: {e}")
            return Response({
                'success': False,
                'error': 'Errore durante l\'iscrizione al corso'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
