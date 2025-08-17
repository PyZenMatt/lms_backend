"""
Django API views for TeoCoin Discount System

Provides REST API endpoints for the gas-free discount system:
- Student discount requests and management
- Teacher approval/decline actions  
- Real-time status tracking
- Signature generation for pre-approval
"""

import logging
from decimal import Decimal
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import json

from services.teocoin_discount_service import teocoin_discount_service
from blockchain.blockchain import TeoCoinService


logger = logging.getLogger(__name__)


class BaseDiscountView(APIView):
    """Base view for discount system with common functionality"""
    permission_classes = [IsAuthenticated]
    
    def get_request_data(self, request):
        """Parse JSON request data"""
        return request.data if hasattr(request, 'data') else {}
    
    def json_response(self, data, status_code=200):
        """Return JSON response"""
        return Response(data, status=status_code)
    
    def error_response(self, message, status_code=400, status=None):
        """Return error response"""
        # Accept both status_code and status for compatibility
        final_status = status if status is not None else status_code
        return Response({'error': message, 'success': False}, status=final_status)


class SignatureDataView(BaseDiscountView):
    """Generate signature data for student pre-approval"""
    
    def post(self, request):
        try:
            data = self.get_request_data(request)
            
            # Extract and validate parameters with null-safe handling
            student_address = (data.get('student_address') or '').strip()
            course_id = data.get('course_id')
            course_price = data.get('course_price')
            discount_percent = data.get('discount_percent')
            
            if not all([student_address, course_id, course_price, discount_percent]):
                return self.error_response('Missing required parameters')
            
            # Validate student address format
            try:
                from web3 import Web3
                if not Web3.is_address(student_address):
                    return self.error_response('Invalid student address format')
            except Exception:
                return self.error_response('Invalid student address')
            
            # Calculate TEO cost
            try:
                course_price_decimal = Decimal(str(course_price))
                teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                    course_price_decimal, int(discount_percent)
                )
            except (ValueError, TypeError) as e:
                return self.error_response(f'Invalid price or discount percentage: {e}')
            
            # Generate signature data with proper error handling
            try:
                signature_data = teocoin_discount_service.generate_student_signature_data(
                    student_address, int(course_id), teo_cost
                )
                
                # Check if there was an error in signature generation
                if 'error' in signature_data:
                    return self.error_response(f'Signature generation failed: {signature_data["error"]}')
                
                return self.json_response({
                    'success': True,
                    'signature_data': signature_data,
                    'teo_cost': teo_cost,
                    'teacher_bonus': teacher_bonus,
                    'discount_value': float(course_price_decimal * int(discount_percent) / 100)
                })
                
            except UnicodeDecodeError as e:
                logger.error(f"UTF-8 encoding error in signature generation: {e}")
                return self.error_response('Encoding error in signature generation. Please check wallet address format.')
            except Exception as e:
                logger.error(f"Unexpected error in signature generation: {e}")
                return self.error_response(f'Signature generation error: {str(e)}')
            
        except UnicodeDecodeError as e:
            logger.error(f"UTF-8 encoding error in request data: {e}")
            return self.error_response('Invalid character encoding in request data')
        except Exception as e:
            logger.error(f"Error generating signature data: {e}")
            return self.error_response(str(e), status=500)


class CreateDiscountRequestView(BaseDiscountView):
    """Create a new discount request"""
    
    def post(self, request):
        try:
            data = self.get_request_data(request)
            
            # DEBUG: Log the received data
            logger.info(f"Received discount request data: {data}")
            
            # Extract and validate parameters with null-safe handling
            student_address = (data.get('student_address') or '').strip()
            teacher_address = (data.get('teacher_address') or '').strip()
            course_id = data.get('course_id')
            course_price = data.get('course_price')
            discount_percent = data.get('discount_percent')
            student_signature = (data.get('student_signature') or '').strip()
            
            # DEBUG: Log each parameter with raw values
            logger.info(f"Raw parameters - student_address: {repr(data.get('student_address'))}, teacher_address: {repr(data.get('teacher_address'))}, course_id: {repr(data.get('course_id'))}")
            logger.info(f"Parsed parameters - student_address: '{student_address}', teacher_address: '{teacher_address}', course_id: {course_id}, course_price: {course_price}, discount_percent: {discount_percent}, student_signature: '{student_signature[:20]}...' if student_signature else 'None'")
            
            if not all([student_address, teacher_address, course_id, course_price, discount_percent, student_signature]):
                missing_params = []
                if not student_address: missing_params.append('student_address')
                if not teacher_address: missing_params.append('teacher_address') 
                if not course_id: missing_params.append('course_id')
                if not course_price: missing_params.append('course_price')
                if not discount_percent: missing_params.append('discount_percent')
                if not student_signature: missing_params.append('student_signature')
                
                logger.error(f"Missing required parameters: {missing_params}")
                return self.error_response(f'Missing required parameters: {", ".join(missing_params)}')
            
            # Convert types
            try:
                course_price_decimal = Decimal(str(course_price))
                course_id_int = int(course_id)
                discount_percent_int = int(discount_percent)
            except (ValueError, TypeError):
                return self.error_response('Invalid parameter types')
            
            # Create discount request via service
            result = teocoin_discount_service.create_discount_request(
                student_address=student_address,
                teacher_address=teacher_address,
                course_id=course_id_int,
                course_price=course_price_decimal,
                discount_percent=discount_percent_int,
                student_signature=student_signature
            )
            
            if result['success']:
                logger.info(f"Discount request created successfully: {result['request_id']}")
                
                # 🚀 CRUCIAL FIX: Create Django model record for persistence and teacher notifications
                try:
                    from blockchain.models import TeoCoinDiscountRequest
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    # Calculate TEO amounts
                    teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                        course_price_decimal, discount_percent_int
                    )
                    
                    # Create Django model record
                    django_request = TeoCoinDiscountRequest.objects.create(
                        student_address=student_address,
                        teacher_address=teacher_address,
                        course_id=course_id_int,
                        course_price=int(course_price_decimal * 100),  # Convert to cents
                        discount_percent=discount_percent_int * 100,  # Convert to basis points (10% = 1000)
                        teo_cost=int(teo_cost),  # TEO in wei
                        teacher_bonus=int(teacher_bonus),  # TEO in wei
                        expires_at=timezone.now() + timedelta(hours=2),  # 2 hour expiration
                        blockchain_tx_hash=result.get('transaction_hash', ''),
                        status=0  # Pending
                    )
                    
                    logger.info(f"✅ Django model record created: TeoCoinDiscountRequest ID {django_request.id}")
                    
                    # 🔔 Send teacher notification
                    try:
                        from courses.models import Course
                        from users.models import User
                        from notifications.models import Notification
                        
                        course = Course.objects.get(id=course_id_int)
                        teacher = course.teacher
                        
                        # Create notification for teacher
                        Notification.objects.create(
                            user=teacher,
                            message=f"🪙 New TeoCoin discount request for your course '{course.title}'. Student wants {discount_percent_int}% discount ({teo_cost / 10**18:.2f} TEO). Choose to accept TEoCoin or receive full EUR payment.",
                            notification_type='teocoin_discount_request',
                            related_object_id=str(django_request.id)
                        )
                        
                        logger.info(f"✅ Teacher notification sent to {teacher.email}")
                        
                        # Update result with Django record info
                        result['django_request_id'] = django_request.id
                        result['teacher_notified'] = True
                        result['expires_at'] = django_request.expires_at.isoformat()
                        
                    except Exception as notification_error:
                        logger.error(f"⚠️ Teacher notification failed: {notification_error}")
                        result['teacher_notified'] = False
                        result['notification_error'] = str(notification_error)
                        
                except Exception as django_error:
                    logger.error(f"⚠️ Django model creation failed: {django_error}")
                    # Don't fail the entire request for Django model issues
                    result['django_created'] = False
                    result['django_error'] = str(django_error)
                
                return self.json_response(result)
            else:
                return self.error_response(result.get('error', 'Failed to create request'), status=400)
            
        except Exception as e:
            logger.error(f"Error creating discount request: {e}")
            return self.error_response(str(e), status=500)


class ApproveDiscountRequestView(BaseDiscountView):
    """Approve a discount request"""
    
    def post(self, request):
        try:
            data = self.get_request_data(request)
            
            # Extract parameters with null-safe handling
            request_id = data.get('request_id')
            approver_address = (data.get('approver_address') or '').strip()
            
            if not all([request_id, approver_address]):
                return self.error_response('Missing required parameters')
            
            # Convert request_id to int
            try:
                request_id_int = int(request_id)
            except (ValueError, TypeError):
                return self.error_response('Invalid request ID')
            
            # Approve request via service
            result = teocoin_discount_service.approve_discount_request(
                request_id=request_id_int,
                approver_address=approver_address
            )
            
            if result['success']:
                logger.info(f"Discount request {request_id_int} approved by {approver_address}")
                return self.json_response(result)
            else:
                return self.error_response(result.get('error', 'Failed to approve request'), status=400)
            
        except Exception as e:
            logger.error(f"Error approving discount request: {e}")
            return self.error_response(str(e), status=500)


class DeclineDiscountRequestView(BaseDiscountView):
    """Decline a discount request"""
    
    def post(self, request):
        try:
            data = self.get_request_data(request)
            
            # Extract parameters with null-safe handling
            request_id = data.get('request_id')
            decliner_address = (data.get('decliner_address') or '').strip()
            reason = (data.get('reason') or '').strip()
            
            if not all([request_id, decliner_address, reason]):
                return self.error_response('Missing required parameters')
            
            # Convert request_id to int
            try:
                request_id_int = int(request_id)
            except (ValueError, TypeError):
                return self.error_response('Invalid request ID')
            
            # Decline request via service
            result = teocoin_discount_service.decline_discount_request(
                request_id=request_id_int,
                decliner_address=decliner_address,
                reason=reason
            )
            
            if result['success']:
                logger.info(f"Discount request {request_id_int} declined by {decliner_address}")
                return self.json_response(result)
            else:
                return self.error_response(result.get('error', 'Failed to decline request'), status=400)
            
        except Exception as e:
            logger.error(f"Error declining discount request: {e}")
            return self.error_response(str(e), status=500)


class DiscountRequestDetailView(BaseDiscountView):
    """Get details of a specific discount request"""
    
    def get(self, request, request_id):
        try:
            # Convert request_id to int
            try:
                request_id_int = int(request_id)
            except (ValueError, TypeError):
                return self.error_response('Invalid request ID')
            
            # Get request details
            request_data = teocoin_discount_service.get_discount_request(request_id_int)
            
            if request_data:
                return self.json_response({
                    'success': True,
                    'request': request_data
                })
            else:
                return self.error_response('Request not found', status=404)
            
        except Exception as e:
            logger.error(f"Error getting discount request {request_id}: {e}")
            return self.error_response(str(e), status=500)


class StudentRequestsView(BaseDiscountView):
    """Get all discount requests for a student"""
    
    def get(self, request, student_address):
        try:
            if not student_address:
                return self.error_response('Student address required')
            
            # Get student requests
            requests = teocoin_discount_service.get_student_requests(student_address)
            
            return self.json_response({
                'success': True,
                'requests': requests,
                'count': len(requests)
            })
            
        except Exception as e:
            logger.error(f"Error getting student requests for {student_address}: {e}")
            return self.error_response(str(e), status=500)


class TeacherRequestsView(BaseDiscountView):
    """Get all discount requests for a teacher"""
    
    def get(self, request, teacher_address):
        try:
            if not teacher_address:
                return self.error_response('Teacher address required')
            
            # Get teacher requests
            requests = teocoin_discount_service.get_teacher_requests(teacher_address)
            
            return self.json_response({
                'success': True,
                'requests': requests,
                'count': len(requests)
            })
            
        except Exception as e:
            logger.error(f"Error getting teacher requests for {teacher_address}: {e}")
            return self.error_response(str(e), status=500)


class DiscountStatsView(BaseDiscountView):
    """Get discount system statistics"""
    
    def get(self, request):
        try:
            # This would typically come from a database aggregation
            # For now, we'll return basic stats
            
            stats = {
                'success': True,
                'stats': {
                    'total_requests': 0,  # Would be calculated from database
                    'total_approved': 0,
                    'total_declined': 0,
                    'total_teo_transferred': 0,
                    'total_teacher_bonuses': 0,
                    'approval_rate': 0.0,
                    'average_discount_percent': 0.0,
                    'average_teo_cost': 0.0
                },
                'generated_at': timezone.now().isoformat()
            }
            
            return self.json_response(stats)
            
        except Exception as e:
            logger.error(f"Error getting discount stats: {e}")
            return self.error_response(str(e), status=500)


class CalculateDiscountCostView(BaseDiscountView):
    """Calculate TEO cost for a given course price and discount percentage"""
    
    def post(self, request):
        try:
            data = self.get_request_data(request)
            
            course_price = data.get('course_price')
            discount_percent = data.get('discount_percent')
            
            if not all([course_price, discount_percent]):
                return self.error_response('Course price and discount percentage required')
            
            try:
                course_price_decimal = Decimal(str(course_price))
                discount_percent_int = int(discount_percent)
            except (ValueError, TypeError):
                return self.error_response('Invalid price or discount percentage')
            
            # Calculate costs
            teo_cost, teacher_bonus = teocoin_discount_service.calculate_teo_cost(
                course_price_decimal, discount_percent_int
            )
            
            discount_value = course_price_decimal * discount_percent_int / 100
            
            return self.json_response({
                'success': True,
                'calculation': {
                    'course_price': float(course_price_decimal),
                    'discount_percent': discount_percent_int,
                    'discount_value': float(discount_value),
                    'teo_cost': teo_cost,
                    'teo_cost_formatted': f"{teo_cost / 10**18:.4f} TEO",
                    'teacher_bonus': teacher_bonus,
                    'teacher_bonus_formatted': f"{teacher_bonus / 10**18:.4f} TEO",
                    'total_teacher_receives': teo_cost + teacher_bonus,
                    'total_teacher_receives_formatted': f"{(teo_cost + teacher_bonus) / 10**18:.4f} TEO"
                }
            })
            
        except Exception as e:
            logger.error(f"Error calculating discount cost: {e}")
            return self.error_response(str(e), status=500)


class SystemStatusView(BaseDiscountView):
    """Get discount system status and health check"""
    
    def get(self, request):
        try:
            # Check if the discount service is properly initialized
            service_status = {
                'contract_initialized': teocoin_discount_service.discount_contract is not None,
                'platform_account_initialized': teocoin_discount_service.platform_account is not None,
                'web3_connected': teocoin_discount_service.w3.is_connected() if teocoin_discount_service.w3 else False
            }
            
            # Get TeoCoin service status
            teocoin_service = TeoCoinService()
            teocoin_status = {
                'teocoin_service_available': True,
                'reward_pool_balance': float(teocoin_service.get_reward_pool_balance()) if teocoin_service else 0
            }
            
            return self.json_response({
                'success': True,
                'status': 'operational' if all(service_status.values()) else 'limited',
                'service_status': service_status,
                'teocoin_status': teocoin_status,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return self.json_response({
                'success': False,
                'status': 'error',
                'error': str(e),
                'timestamp': timezone.now().isoformat()
            }, status=500)
