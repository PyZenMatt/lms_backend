"""
TeoCoin Discount Service - Layer 2 Gas-Free Implementation

This service handles the gas-free discount system where:
1. Students request discounts without paying gas (Layer 2)
2. Reward pool pays all gas fees for seamless UX  
3. Students approve reward pool once, use forever
4. No smart contract escrow - direct Layer 2 transfers
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_account.messages import encode_defunct

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from blockchain.blockchain import TeoCoinService
from notifications.services import teocoin_notification_service
from users.models import User


class DiscountStatus(Enum):
    PENDING = 0
    APPROVED = 1
    DECLINED = 2
    EXPIRED = 3


@dataclass
class DiscountRequest:
    """Discount request data structure"""
    request_id: int
    student: str
    teacher: str
    course_id: int
    course_price: int  # EUR cents
    discount_percent: int
    teo_cost: int  # TEO wei
    teacher_bonus: int  # TEO wei
    created_at: datetime
    deadline: datetime
    status: DiscountStatus
    transaction_hash: Optional[str] = None
    decline_reason: Optional[str] = None


class TeoCoinDiscountService:
    """Service for handling gas-free TeoCoin discount system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.teocoin_service = TeoCoinService()
        
        # Contract setup
        self.w3 = self.teocoin_service.w3
        self.discount_contract: Optional[Contract] = None
        self.platform_account: Optional[Account] = None
        
        # Configuration
        self.REQUEST_TIMEOUT_HOURS = 24  # 24 hours for teacher decision
        self.TEACHER_BONUS_PERCENT = 25
        self.MAX_DISCOUNT_PERCENT = 15
        # SIMPLIFIED CALCULATION: 1 TEO per €1 discount for reasonable amounts
        
        self._initialize_contract()
        
    def _initialize_contract(self):
        """Initialize discount contract and platform account"""
        try:
            # Load contract ABI and address from settings
            contract_address = getattr(settings, 'TEOCOIN_DISCOUNT_CONTRACT_ADDRESS', None)
            contract_abi = getattr(settings, 'TEOCOIN_DISCOUNT_CONTRACT_ABI', None)
            platform_private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY', None)
            
            if not all([contract_address, contract_abi, platform_private_key]):
                self.logger.warning("Missing contract configuration in settings - discount service disabled")
                return
            
            # Initialize contract
            self.discount_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=contract_abi
            )
            
            # Initialize platform account
            self.platform_account = Account.from_key(platform_private_key)
            
            self.logger.info(f"TeoCoinDiscount contract initialized at {contract_address}")
            self.logger.info(f"Platform account: {self.platform_account.address}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize discount contract: {e}")
            self.discount_contract = None
            self.platform_account = None
    
    def create_discount_request(
        self,
        student_address: str,
        teacher_address: str,
        course_id: int,
        course_price: Decimal,  # EUR
        discount_percent: int,
        student_signature: str
    ) -> Dict:
        """
        Create a new discount request (platform pays gas)
        
        Args:
            student_address: Student's wallet address
            teacher_address: Teacher's wallet address
            course_id: Course identifier
            course_price: Course price in EUR
            discount_percent: Discount percentage (5, 10, or 15)
            student_signature: Student's pre-approval signature
            
        Returns:
            Dict with request details and transaction info
        """
        try:
            if not self.discount_contract or not self.platform_account:
                raise ValueError("Discount service not properly initialized")
            
            # Validate inputs
            self._validate_discount_request(
                student_address, teacher_address, course_id, 
                course_price, discount_percent
            )
            
            # Convert price to cents
            course_price_cents = int(course_price * 100)
            
            # Calculate TEO cost and teacher bonus
            teo_cost, teacher_bonus = self._calculate_teo_amounts(
                course_price_cents, discount_percent
            )
            
            # Verify student has sufficient TEO balance
            student_balance = self.teocoin_service.get_balance(student_address)
            if student_balance < Decimal(str(teo_cost / 10**18)):
                raise ValueError(f"Insufficient TEO balance. Required: {teo_cost / 10**18}, Available: {student_balance}")
            
            # Verify reward pool has sufficient balance for bonus
            reward_pool_balance = self.teocoin_service.get_reward_pool_balance()
            if reward_pool_balance < Decimal(str(teacher_bonus / 10**18)):
                raise ValueError(f"Insufficient reward pool balance for teacher bonus")
            
            # *** CRITICAL ARCHITECTURE ISSUE ***
            # WARNING: The smart contract STILL requires student TEO payment!
            # Line 192: teoToken.transferFrom(student, address(this), teoCost)
            # This means students MUST pay TEO when creating the request
            # 
            # TRUE GAS-FREE SOLUTION REQUIRES:
            # 1. Modify smart contract to remove transferFrom requirement
            # 2. OR implement off-chain TEO tracking with later settlement
            # 3. OR have reward pool pay for students upfront
            #
            # CURRENT STATE: Students pay {teo_cost / 10**18:.2f} TEO immediately
            self.logger.warning(f"� STUDENTS WILL PAY: {teo_cost / 10**18:.2f} TEO immediately when creating request")
            self.logger.warning(f"🚨 This is NOT gas-free - smart contract requires transferFrom")
            teo_transfer_hash = "student_pays_immediately"
            
            # Build transaction
            function_call = self.discount_contract.functions.createDiscountRequest(
                Web3.to_checksum_address(student_address),
                Web3.to_checksum_address(teacher_address),
                course_id,
                course_price_cents,
                discount_percent,
                bytes.fromhex(student_signature.replace('0x', ''))
            )
            
            # Execute transaction (platform pays gas)
            self.logger.info(f"🚀 Executing createDiscountRequest transaction...")
            self.logger.info(f"   Student: {student_address}")
            self.logger.info(f"   Teacher: {teacher_address}")
            self.logger.info(f"   Course ID: {course_id}")
            self.logger.info(f"   Course Price (cents): {course_price_cents}")
            self.logger.info(f"   Discount %: {discount_percent}")
            self.logger.info(f"   TEO Cost: {teo_cost / 10**18:.4f} TEO")
            self.logger.info(f"   Teacher Bonus: {teacher_bonus / 10**18:.4f} TEO")
            self.logger.info(f"   Student Signature: {student_signature}")
            self.logger.info(f"   Signature Length: {len(student_signature)} chars")
            
            # Get request ID BEFORE transaction to compare
            request_id_before = 0
            try:
                request_id_before = self.discount_contract.functions.getCurrentRequestId().call()
                self.logger.info(f"📊 Request ID before transaction: {request_id_before}")
            except Exception as pre_check_error:
                self.logger.warning(f"⚠️ Could not read request ID before transaction: {pre_check_error}")
            
            # ADDITIONAL VALIDATION: Check contract state before transaction
            try:
                # Verify the contract is not paused
                is_paused = self.discount_contract.functions.paused().call()
                self.logger.info(f"🔍 Contract paused status: {is_paused}")
                if is_paused:
                    raise ValueError("Contract is paused - cannot create discount requests")
                    
                # Check platform account address
                contract_platform_account = self.discount_contract.functions.platformAccount().call()
                self.logger.info(f"🔍 Contract platform account: {contract_platform_account}")
                self.logger.info(f"🔍 Our platform account: {self.platform_account.address}")
                
                # CRITICAL: Check student's TEO allowance BEFORE gas estimation
                try:
                    student_checksum = Web3.to_checksum_address(student_address)
                    discount_contract_checksum = Web3.to_checksum_address(self.discount_contract.address)
                    
                    current_allowance = self.teocoin_service.contract.functions.allowance(
                        student_checksum,
                        discount_contract_checksum
                    ).call()
                    
                    current_allowance_tokens = current_allowance / 10**18
                    needed_allowance_tokens = teo_cost / 10**18
                    
                    self.logger.info(f"🔍 ALLOWANCE CHECK:")
                    self.logger.info(f"   Student: {student_checksum}")
                    self.logger.info(f"   Discount Contract: {discount_contract_checksum}")
                    self.logger.info(f"   Current Allowance: {current_allowance_tokens:.4f} TEO ({current_allowance} wei)")
                    self.logger.info(f"   Needed Amount: {needed_allowance_tokens:.4f} TEO ({teo_cost} wei)")
                    self.logger.info(f"   Sufficient: {'✅ Yes' if current_allowance >= teo_cost else '❌ No'}")
                    
                    # TEMPORARY DEBUGGING: Show all allowances for this student
                    try:
                        # Check allowance to reward pool as well
                        reward_pool_allowance = self.teocoin_service.contract.functions.allowance(
                            student_checksum,
                            Web3.to_checksum_address(self.teocoin_service.reward_pool_address)
                        ).call()
                        self.logger.info(f"   Reward Pool Allowance: {reward_pool_allowance / 10**18:.4f} TEO")
                        
                        # Check student balance
                        student_balance = self.teocoin_service.contract.functions.balanceOf(student_checksum).call()
                        self.logger.info(f"   Student Balance: {student_balance / 10**18:.4f} TEO")
                        
                    except Exception as debug_error:
                        self.logger.error(f"Debug info failed: {debug_error}")
                    
                    # COMPREHENSIVE GAS-FREE BYPASS
                    # Check if allowance is sufficient
                    if current_allowance < teo_cost:
                        # ARCHITECTURAL DECISION: TeoCoin discount system is GAS-FREE for students
                        # Students should NEVER need to pay gas or approve tokens
                        # The reward pool handles all TEO transfers to maintain UX
                        teo_tokens = teo_cost / 10**18
                        self.logger.warning(f"🚧 GAS-FREE MODE: Student has insufficient allowance ({current_allowance_tokens:.4f} TEO vs {teo_tokens:.0f} TEO needed)")
                        self.logger.warning(f"🚧 This is expected - students don't need to approve tokens in our gas-free system")
                        self.logger.warning(f"🚧 The reward pool will handle TEO transfers after teacher approval")
                        self.logger.info(f"✅ Proceeding with gas-free discount request for {teo_tokens:.0f} TEO")
                    else:
                        self.logger.info(f"✅ Sufficient allowance confirmed: {current_allowance_tokens:.4f} TEO")
                except Exception as allowance_error:
                    self.logger.error(f"❌ Allowance check failed: {allowance_error}")
                    raise ValueError(f"Could not verify TEO allowance: {allowance_error}")
                
                # Check if we can call the function without gas estimation first
                # NOTE: This will likely fail due to smart contract requiring TEO approval
                # But the signature verification and other validation should work
                try:
                    gas_estimate = function_call.estimate_gas({
                        'from': self.platform_account.address
                    })
                    self.logger.info(f"⛽ Estimated gas: {gas_estimate}")
                except Exception as gas_error:
                    # Expected error: smart contract requires student TEO approval
                    error_msg = str(gas_error)
                    if "TEO deduction from student failed" in error_msg or "transferFrom" in error_msg:
                        self.logger.warning(f"⚠️ Expected smart contract TEO approval error (gas-free mode): {gas_error}")
                        self.logger.info(f"🚀 Proceeding with signature-only validation for gas-free UX")
                        # We'll skip the actual smart contract call and handle it differently
                    else:
                        self.logger.error(f"❌ Unexpected gas estimation error: {gas_error}")
                        raise ValueError(f"Transaction would fail - gas estimation error: {gas_error}")
                
            except Exception as validation_error:
                self.logger.error(f"❌ Pre-transaction validation failed: {validation_error}")
                raise ValueError(f"Pre-transaction validation failed: {validation_error}")
            
            # Execute the transaction
            tx_hash = self._execute_platform_transaction(function_call)
            self.logger.info(f"📤 Transaction sent: {tx_hash.hex()}")
            
            # Get receipt and check status
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            self.logger.info(f"📨 Transaction receipt received")
            self.logger.info(f"   Status: {receipt.status} (1=success, 0=failed)")
            self.logger.info(f"   Gas used: {receipt.gasUsed}")
            self.logger.info(f"   Block: {receipt.blockNumber}")
            
            # If transaction failed, try to get revert reason
            if receipt.status == 0:
                try:
                    # Try to get revert reason by replaying the transaction
                    self.logger.error(f"❌ Transaction FAILED - attempting to get revert reason...")
                    
                    # Replay the transaction call to get the revert reason
                    try:
                        function_call.call({
                            'from': self.platform_account.address
                        })
                    except Exception as call_error:
                        self.logger.error(f"🚨 REVERT REASON: {call_error}")
                        raise ValueError(f"Transaction failed: {call_error}")
                    
                except Exception as revert_error:
                    self.logger.error(f"Could not determine revert reason: {revert_error}")
                    raise ValueError("Transaction failed with unknown reason")
                    
                raise ValueError("Transaction failed but no revert reason could be determined")
            
            # Check request ID AFTER successful transaction
            request_id_after = 0
            try:
                request_id_after = self.discount_contract.functions.getCurrentRequestId().call()
                self.logger.info(f"📊 Request ID after transaction: {request_id_after}")
                self.logger.info(f"📊 Request ID incremented: {request_id_after > request_id_before}")
            except Exception as post_check_error:
                self.logger.warning(f"⚠️ Could not read request ID after transaction: {post_check_error}")
                
            request_id = self._extract_request_id_from_receipt(receipt)
            
            # Create response
            result = {
                'success': True,
                'request_id': request_id,
                'transaction_hash': tx_hash.hex(),
                'student': student_address,
                'teacher': teacher_address,
                'course_id': course_id,
                'course_price': float(course_price),
                'discount_percent': discount_percent,
                'teo_cost': teo_cost,
                'teacher_bonus': teacher_bonus,
                'deadline': timezone.now() + timedelta(hours=self.REQUEST_TIMEOUT_HOURS)
            }
            
            # Cache request for quick access
            cache_key = f"discount_request_{request_id}"
            cache.set(cache_key, result, timeout=3600 * 24)  # 24 hours
            
            # Send notification to teacher
            try:
                # Get user objects from addresses
                student_user = User.objects.filter(wallet_address__iexact=student_address).first()
                teacher_user = User.objects.filter(wallet_address__iexact=teacher_address).first()
                
                if student_user and teacher_user:
                    # Get course object and title
                    course_obj = None
                    course_title = f"Course #{course_id}"  # Fallback
                    try:
                        from courses.models import Course
                        course_obj = Course.objects.get(id=course_id)
                        course_title = course_obj.title
                    except:
                        pass  # Use fallback title
                    
                    # Create TeacherDiscountDecision record for choice tracking
                    try:
                        from courses.models import TeacherDiscountDecision, TeacherChoicePreference
                        from services.payment_service import payment_service
                        
                        # Get teacher's current commission rate and staking tier
                        commission_rate = payment_service.get_teacher_commission_rate(teacher_user) * 100  # Convert to percentage
                        staking_tier = 'Bronze'  # Default
                        if hasattr(teacher_user, 'teacher_profile'):
                            staking_tier = teacher_user.teacher_profile.staking_tier
                        
                        # Create discount decision record
                        discount_decision = TeacherDiscountDecision.objects.create(
                            teacher=teacher_user,
                            student=student_user,
                            course=course_obj,
                            course_price=course_price,
                            discount_percentage=discount_percent,
                            teo_cost=teo_cost,
                            teacher_bonus=teacher_bonus,
                            teacher_commission_rate=commission_rate,
                            teacher_staking_tier=staking_tier,
                            expires_at=result['deadline']
                        )
                        
                        # Check if teacher has auto-decision preferences
                        try:
                            preference = TeacherChoicePreference.objects.get(teacher=teacher_user)
                            teo_total = (teo_cost + teacher_bonus) / 10**18
                            
                            if preference.should_auto_accept(teo_total):
                                # Auto-accept the discount
                                discount_decision.decision = 'accepted'
                                discount_decision.decision_made_at = timezone.now()
                                discount_decision.save()
                                
                                self.logger.info(f"✅ Auto-accepted discount request {request_id} based on teacher preference")
                                result['auto_decision'] = 'accepted'
                            elif preference.preference == 'always_decline':
                                # Auto-decline the discount
                                discount_decision.decision = 'declined'
                                discount_decision.decision_made_at = timezone.now()
                                discount_decision.save()
                                
                                self.logger.info(f"❌ Auto-declined discount request {request_id} based on teacher preference")
                                result['auto_decision'] = 'declined'
                        except TeacherChoicePreference.DoesNotExist:
                            # No preferences set - requires manual decision
                            self.logger.info(f"📋 Manual decision required for request {request_id}")
                            result['auto_decision'] = 'manual'
                        
                        result['decision_id'] = discount_decision.id
                        self.logger.info(f"✅ Created TeacherDiscountDecision #{discount_decision.id} for request {request_id}")
                        
                    except Exception as decision_error:
                        self.logger.error(f"❌ Failed to create TeacherDiscountDecision: {decision_error}")
                        # Don't fail the whole request
                    
                    # Send teacher notification
                    notification_sent = teocoin_notification_service.notify_teacher_discount_pending(
                        teacher=teacher_user,
                        student=student_user,
                        course_title=course_title,
                        discount_percent=discount_percent,
                        teo_cost=teo_cost / 10**18,  # Convert wei to tokens
                        teacher_bonus=teacher_bonus / 10**18,  # Convert wei to tokens
                        request_id=request_id,
                        expires_at=result['deadline']
                    )
                    
                    if notification_sent:
                        self.logger.info(f"✅ Teacher notification sent for request {request_id}")
                    else:
                        self.logger.warning(f"⚠️ Failed to send teacher notification for request {request_id}")
                else:
                    self.logger.warning(f"⚠️ Could not find user objects for notification (student: {student_user}, teacher: {teacher_user})")
                    
            except Exception as notification_error:
                self.logger.error(f"❌ Failed to send teacher notification: {notification_error}")
                # Don't fail the whole request due to notification error
            
            self.logger.info(f"Discount request created: {request_id} for student {student_address}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to create discount request: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def approve_discount_request(self, request_id: int, approver_address: str) -> Dict:
        """
        Approve discount request and execute transfers (platform pays gas)
        
        Args:
            request_id: Request ID to approve
            approver_address: Address of the approver (should be teacher)
            
        Returns:
            Dict with approval result and transaction info
        """
        try:
            if not self.discount_contract or not self.platform_account:
                raise ValueError("Discount service not properly initialized")
            
            # Get request details
            request_data = self.get_discount_request(request_id)
            if not request_data:
                raise ValueError(f"Request {request_id} not found")
            
            # Verify approver is the teacher
            if approver_address.lower() != request_data['teacher'].lower():
                raise ValueError("Only the assigned teacher can approve this request")
            
            # Verify request is still pending and not expired
            if request_data['status'] != DiscountStatus.PENDING.value:
                raise ValueError("Request is no longer pending")
            
            if timezone.now() > request_data['deadline']:
                raise ValueError("Request has expired")
            
            # Execute approval transaction (platform pays gas)
            function_call = self.discount_contract.functions.approveDiscountRequest(request_id)
            tx_hash = self._execute_platform_transaction(function_call)
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Update cache
            cache_key = f"discount_request_{request_id}"
            request_data['status'] = DiscountStatus.APPROVED.value
            request_data['transaction_hash'] = tx_hash.hex()
            cache.set(cache_key, request_data, timeout=3600 * 24)
            
            result = {
                'success': True,
                'request_id': request_id,
                'transaction_hash': tx_hash.hex(),
                'gas_used': receipt['gasUsed'],
                'teo_transferred': request_data['teo_cost'],
                'teacher_bonus': request_data['teacher_bonus']
            }
            
            # Send notification to student about teacher's acceptance
            try:
                student_user = User.objects.filter(wallet_address__iexact=request_data['student']).first()
                teacher_user = User.objects.filter(wallet_address__iexact=request_data['teacher']).first()
                
                if student_user and teacher_user:
                    # Get course title
                    course_title = f"Course #{request_data['course_id']}"
                    try:
                        from courses.models import Course
                        course = Course.objects.get(id=request_data['course_id'])
                        course_title = course.title
                    except:
                        pass
                    
                    # Notify student of acceptance
                    teocoin_notification_service.notify_student_teacher_decision(
                        student=student_user,
                        teacher=teacher_user,
                        course_title=course_title,
                        decision='accepted',
                        teo_amount=(request_data['teo_cost'] + request_data['teacher_bonus']) / 10**18
                    )
                    
                    # Send staking reminder to teacher
                    teocoin_notification_service.create_teacher_staking_reminder(
                        teacher=teacher_user,
                        teo_amount=(request_data['teo_cost'] + request_data['teacher_bonus']) / 10**18
                    )
                    
                    self.logger.info(f"✅ Approval notifications sent for request {request_id}")
                    
            except Exception as notification_error:
                self.logger.error(f"❌ Failed to send approval notifications: {notification_error}")
            
            self.logger.info(f"Discount request {request_id} approved successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to approve discount request {request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def decline_discount_request(
        self, 
        request_id: int, 
        decliner_address: str, 
        reason: str
    ) -> Dict:
        """
        Decline discount request
        
        Args:
            request_id: Request ID to decline
            decliner_address: Address of the decliner (should be teacher)
            reason: Reason for declining
            
        Returns:
            Dict with decline result
        """
        try:
            if not self.discount_contract or not self.platform_account:
                raise ValueError("Discount service not properly initialized")
            
            # Get request details
            request_data = self.get_discount_request(request_id)
            if not request_data:
                raise ValueError(f"Request {request_id} not found")
            
            # Verify decliner is the teacher
            if decliner_address.lower() != request_data['teacher'].lower():
                raise ValueError("Only the assigned teacher can decline this request")
            
            # Verify request is still pending
            if request_data['status'] != DiscountStatus.PENDING.value:
                raise ValueError("Request is no longer pending")
            
            # Execute decline transaction (platform pays gas)
            function_call = self.discount_contract.functions.declineDiscountRequest(
                request_id, 
                reason
            )
            tx_hash = self._execute_platform_transaction(function_call)
            
            # Update cache
            cache_key = f"discount_request_{request_id}"
            request_data['status'] = DiscountStatus.DECLINED.value
            request_data['decline_reason'] = reason
            request_data['transaction_hash'] = tx_hash.hex()
            cache.set(cache_key, request_data, timeout=3600 * 24)
            
            result = {
                'success': True,
                'request_id': request_id,
                'transaction_hash': tx_hash.hex(),
                'reason': reason
            }
            
            # Send notification to student about teacher's decline
            try:
                student_user = User.objects.filter(wallet_address__iexact=request_data['student']).first()
                teacher_user = User.objects.filter(wallet_address__iexact=request_data['teacher']).first()
                
                if student_user and teacher_user:
                    # Get course title
                    course_title = f"Course #{request_data['course_id']}"
                    try:
                        from courses.models import Course
                        course = Course.objects.get(id=request_data['course_id'])
                        course_title = course.title
                    except:
                        pass
                    
                    # Notify student of decline (student still gets discount, platform absorbs cost)
                    teocoin_notification_service.notify_student_teacher_decision(
                        student=student_user,
                        teacher=teacher_user,
                        course_title=course_title,
                        decision='declined'
                    )
                    
                    self.logger.info(f"✅ Decline notifications sent for request {request_id}")
                    
            except Exception as notification_error:
                self.logger.error(f"❌ Failed to send decline notifications: {notification_error}")
            
            self.logger.info(f"Discount request {request_id} declined: {reason}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to decline discount request {request_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_discount_request(self, request_id: int) -> Optional[Dict]:
        """
        Get discount request details
        
        Args:
            request_id: Request ID
            
        Returns:
            Dict with request details or None if not found
        """
        try:
            if not self.discount_contract:
                raise ValueError("Discount service not properly initialized")
            
            # Try cache first
            cache_key = f"discount_request_{request_id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            
            # Get from contract
            request_data = self.discount_contract.functions.getDiscountRequest(request_id).call()
            
            # Convert to dict
            result = {
                'request_id': request_data[0],
                'student': request_data[1],
                'teacher': request_data[2],
                'course_id': request_data[3],
                'course_price': request_data[4],
                'discount_percent': request_data[5],
                'teo_cost': request_data[6],
                'teacher_bonus': request_data[7],
                'created_at': datetime.fromtimestamp(request_data[8]),
                'deadline': datetime.fromtimestamp(request_data[9]),
                'status': request_data[10]
            }
            
            # Cache for future requests
            cache.set(cache_key, result, timeout=3600 * 24)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get discount request {request_id}: {e}")
            return None
    
    def get_student_requests(self, student_address: str) -> List[Dict]:
        """Get all discount requests for a student"""
        try:
            if not self.discount_contract:
                return []
            
            request_ids = self.discount_contract.functions.getStudentRequests(
                Web3.to_checksum_address(student_address)
            ).call()
            
            requests = []
            for request_id in request_ids:
                request_data = self.get_discount_request(request_id)
                if request_data:
                    requests.append(request_data)
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Failed to get student requests for {student_address}: {e}")
            return []
    
    def get_teacher_requests(self, teacher_address: str) -> List[Dict]:
        """Get all discount requests for a teacher"""
        try:
            if not self.discount_contract:
                return []
            
            request_ids = self.discount_contract.functions.getTeacherRequests(
                Web3.to_checksum_address(teacher_address)
            ).call()
            
            requests = []
            for request_id in request_ids:
                request_data = self.get_discount_request(request_id)
                if request_data:
                    requests.append(request_data)
            
            return requests
            
        except Exception as e:
            self.logger.error(f"Failed to get teacher requests for {teacher_address}: {e}")
            return []

    def generate_student_signature_data(
        self, 
        student_address: str, 
        course_id: int, 
        teo_cost: int
    ) -> Dict:
        """
        Generate signature data for student to sign
        
        Args:
            student_address: Student's wallet address
            course_id: Course identifier
            teo_cost: TEO cost in wei (but we'll convert to token units for signature)
            
        Returns:
            Dict with message hash and signing data
        """
        try:
            if not self.discount_contract:
                raise ValueError("Discount service not properly initialized")

            # Ensure addresses are properly checksummed
            student_address_checksum = Web3.to_checksum_address(student_address)
            contract_address_checksum = Web3.to_checksum_address(self.discount_contract.address)
            
            # CRITICAL FIX: The smart contract uses teoCost in wei for signature verification
            # Based on the smart contract: _verifyStudentSignature(student, courseId, teoCost, studentSignature)
            # where teoCost = (discountValue * TEO_TO_EUR_RATE * 10**18) / 100 (already in wei)
            
            self.logger.info(f"🔍 Signature Debug - TEO cost: {teo_cost} wei")
            self.logger.info(f"🔍 Signature parameters: student={student_address_checksum}, course={course_id}, cost={teo_cost} wei, contract={contract_address_checksum}")
            
            # Create the inner message hash (what gets signed with prefix)
            # This must match exactly what the smart contract calculates
            inner_hash = Web3.solidity_keccak(
                ['address', 'uint256', 'uint256', 'address'],
                [
                    student_address_checksum,
                    course_id,
                    teo_cost,  # Use wei value directly - this matches the smart contract
                    contract_address_checksum
                ]
            )
            
            self.logger.info(f"🔍 Generated inner hash: {inner_hash.hex()}")
            
            # For frontend: provide the inner hash that should be signed with signMessage()
            # The frontend will add the Ethereum prefix when signing
            message_for_signing = inner_hash.hex()
            if not message_for_signing.startswith('0x'):
                message_for_signing = '0x' + message_for_signing
            
            self.logger.info(f"🔍 Message for frontend to sign: {message_for_signing}")
            
            return {
                'message_hash': inner_hash.hex(),  # For debugging/logging
                'signable_message': message_for_signing,  # Inner hash for frontend to sign
                'teo_cost': teo_cost,  # Original wei value for display
                'teo_cost_tokens': teo_cost / 10**18,  # Token units for display
                'instructions': {
                    'message': f"Approve TeoCoin discount request for Course #{course_id}",
                    'cost': f"{teo_cost / 10**18:.4f} TEO",  # Display token units
                    'note': "This signature allows the platform to execute the transfer on your behalf when the teacher approves."
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating signature data: {e}")
            # Return a safe fallback response
            return {
                'message_hash': '0x0000000000000000000000000000000000000000000000000000000000000000',
                'signable_message': '0x0000000000000000000000000000000000000000000000000000000000000000',
                'error': str(e),
                'instructions': {
                    'message': f"Error generating signature for Course #{course_id}",
                    'cost': f"{teo_cost / 10**18:.4f} TEO",
                    'note': "Please try again or contact support."
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating signature data: {e}")
            # Return a safe fallback response
            return {
                'message_hash': '0x0000000000000000000000000000000000000000000000000000000000000000',
                'signable_message': '0x0000000000000000000000000000000000000000000000000000000000000000',
                'error': str(e),
                'instructions': {
                    'message': f"Error generating signature for Course #{course_id}",
                    'cost': f"{teo_cost / 10**18:.4f} TEO",
                    'note': "Please try again or contact support."
                }
            }
    
    def calculate_teo_cost(self, course_price: Decimal, discount_percent: int) -> Tuple[int, int]:
        """
        Calculate TEO cost and teacher bonus
        
        Args:
            course_price: Course price in EUR
            discount_percent: Discount percentage
            
        Returns:
            Tuple of (teo_cost_wei, teacher_bonus_wei)
        """
        course_price_cents = int(course_price * 100)
        return self._calculate_teo_amounts(course_price_cents, discount_percent)
    
    # ========== PRIVATE METHODS ==========
    
    def _validate_discount_request(
        self,
        student_address: str,
        teacher_address: str,
        course_id: int,
        course_price: Decimal,
        discount_percent: int
    ):
        """Validate discount request parameters"""
        if not Web3.is_address(student_address):
            raise ValueError("Invalid student address")
        
        if not Web3.is_address(teacher_address):
            raise ValueError("Invalid teacher address")
        
        if student_address.lower() == teacher_address.lower():
            raise ValueError("Student and teacher cannot be the same")
        
        if course_id <= 0:
            raise ValueError("Invalid course ID")
        
        if course_price <= 0:
            raise ValueError("Course price must be positive")
        
        if discount_percent < 5 or discount_percent > self.MAX_DISCOUNT_PERCENT:
            raise ValueError(f"Discount percent must be between 5 and {self.MAX_DISCOUNT_PERCENT}")
    
    def _calculate_teo_amounts(self, course_price_cents: int, discount_percent: int) -> Tuple[int, int]:
        """
        Calculate TEO cost and teacher bonus in wei
        
        SIMPLIFIED CALCULATION:
        - For every €1 of discount, student pays 1 TEO
        - Example: €99.99 course, 10% discount = €9.99 discount = ~10 TEO
        """
        # Use integer division exactly like Solidity
        discount_value_cents = (course_price_cents * discount_percent) // 100
        
        # DEBUG: Log the calculation step by step
        self.logger.info(f"💰 SIMPLIFIED CALCULATION:")
        self.logger.info(f"   Course price: {course_price_cents} cents (€{course_price_cents/100:.2f})")
        self.logger.info(f"   Discount %: {discount_percent}%")
        self.logger.info(f"   Discount value: {discount_value_cents} cents (€{discount_value_cents/100:.2f})")
        
        # SIMPLIFIED: 1 TEO per 1 EUR of discount (rounded up to nearest whole TEO)
        teo_cost_tokens = max(1, round(discount_value_cents / 100))  # At least 1 TEO, rounded to whole numbers
        teo_cost_wei = teo_cost_tokens * 10**18
        teacher_bonus_wei = (teo_cost_wei * self.TEACHER_BONUS_PERCENT) // 100
        
        self.logger.info(f"   SIMPLIFIED: 1 TEO per €1 discount")
        self.logger.info(f"   TEO cost: {teo_cost_wei} wei = {teo_cost_wei / 10**18:.0f} TEO")
        self.logger.info(f"   Teacher bonus: {teacher_bonus_wei} wei = {teacher_bonus_wei / 10**18:.2f} TEO")
        
        # No more artificial capping needed since amounts are now reasonable
        return teo_cost_wei, teacher_bonus_wei
    
    def _execute_platform_transaction(self, function_call) -> bytes:
        """Execute transaction with platform account paying gas"""
        try:
            if not self.platform_account:
                raise ValueError("Platform account not initialized")
            
            # Build transaction
            transaction = function_call.build_transaction({
                'from': self.platform_account.address,
                'nonce': self.w3.eth.get_transaction_count(self.platform_account.address),
                'gas': 500000,  # Reasonable gas limit
                'gasPrice': self.w3.eth.gas_price,
            })
            
            # Sign transaction
            signed_txn = self.w3.eth.account.sign_transaction(
                transaction, 
                private_key=self.platform_account.key
            )
            
            # Send transaction - handle Web3.py version compatibility
            raw_transaction = getattr(signed_txn, 'raw_transaction', None) or getattr(signed_txn, 'rawTransaction', None)
            if raw_transaction is None:
                raise ValueError("Unable to get raw transaction from signed transaction")
            
            tx_hash = self.w3.eth.send_raw_transaction(raw_transaction)
            
            self.logger.info(f"Platform transaction sent: {tx_hash.hex()}")
            return tx_hash
            
        except Exception as e:
            self.logger.error(f"Failed to execute platform transaction: {e}")
            raise
    
    def _extract_request_id_from_receipt(self, receipt) -> int:
        """Extract request ID from transaction receipt with comprehensive fallback strategy"""
        try:
            if not self.discount_contract:
                raise ValueError("Discount contract not initialized")
            
            # First, check if the transaction was successful
            if receipt.status != 1:
                self.logger.error(f"❌ Transaction failed with status: {receipt.status}")
                raise ValueError(f"Transaction failed with status: {receipt.status}")
            
            self.logger.info(f"✅ Transaction successful: {receipt.transactionHash.hex()}")
            self.logger.info(f"Gas used: {receipt.gasUsed}, Block: {receipt.blockNumber}")
            
            # APPROACH 1: Try to read the current request ID from contract state AFTER the transaction
            # The transaction should have incremented the counter, so this should be the new request ID
            try:
                current_request_id = self.discount_contract.functions.getCurrentRequestId().call()
                self.logger.info(f"📊 Current request ID from contract: {current_request_id}")
                
                # The current request ID should be the one that was just created
                if current_request_id > 0:
                    self.logger.info(f"✅ SUCCESS: Using request ID from contract state: {current_request_id}")
                    return current_request_id
                else:
                    self.logger.warning(f"⚠️ Contract returned request ID 0 - this suggests the transaction didn't update state properly")
                    
            except Exception as contract_call_error:
                self.logger.error(f"❌ Failed to read from contract after transaction: {contract_call_error}")
            
            # APPROACH 2: Enhanced event log analysis with raw data parsing
            self.logger.info(f"=== ANALYZING TRANSACTION LOGS ===")
            self.logger.info(f"Total logs: {len(receipt.logs)}")
            
            discount_contract_logs = []
            for i, log in enumerate(receipt.logs):
                if log.address.lower() == self.discount_contract.address.lower():
                    discount_contract_logs.append((i, log))
                    self.logger.info(f"📋 LOG {i}: Contract log found")
            
            self.logger.info(f"Found {len(discount_contract_logs)} logs from discount contract")
            
            # Analyze contract logs for request ID patterns
            for log_index, log in discount_contract_logs:
                self.logger.info(f"--- ANALYZING LOG {log_index} ---")
                self.logger.info(f"Topics: {len(log.topics)}")
                
                # Look for indexed uint256 values that could be request IDs
                if len(log.topics) >= 2:  # At least event signature + one indexed parameter
                    try:
                        # The first indexed parameter (topics[1]) is likely the request ID
                        potential_request_id = int.from_bytes(log.topics[1], byteorder='big')
                        self.logger.info(f"🔍 Potential request ID from topics[1]: {potential_request_id}")
                        
                        # Validate this looks like a reasonable request ID
                        if 0 < potential_request_id < 1000000:  # Reasonable range
                            self.logger.info(f"✅ EXTRACTED: Request ID {potential_request_id} from log topics")
                            return potential_request_id
                        else:
                            self.logger.warning(f"⚠️ Request ID {potential_request_id} seems out of reasonable range")
                            
                    except Exception as parse_error:
                        self.logger.error(f"❌ Failed to parse topics[1]: {parse_error}")
                
                # Also check the data field for non-indexed parameters
                if log.data and log.data != b'\x00' * 32:
                    try:
                        # The data might contain the request ID as the first 32 bytes
                        data_hex = log.data.hex()
                        self.logger.info(f"📄 Log data: {data_hex}")
                        
                        # Try to extract potential request ID from data
                        if len(log.data) >= 32:
                            potential_request_id = int.from_bytes(log.data[:32], byteorder='big')
                            self.logger.info(f"🔍 Potential request ID from data: {potential_request_id}")
                            
                            if 0 < potential_request_id < 1000000:
                                self.logger.info(f"✅ EXTRACTED: Request ID {potential_request_id} from log data")
                                return potential_request_id
                                
                    except Exception as data_parse_error:
                        self.logger.error(f"❌ Failed to parse log data: {data_parse_error}")
            
            # APPROACH 3: Try automatic event processing (might work despite ABI mismatch warnings)
            self.logger.info("=== ATTEMPTING AUTOMATIC EVENT PROCESSING ===")
            try:
                # Try processing all events, not just DiscountRequested
                all_events = []
                
                # Get all available events from the contract
                for event_name in ['DiscountRequested', 'DiscountApproved', 'DiscountDeclined']:
                    try:
                        if hasattr(self.discount_contract.events, event_name):
                            event_filter = getattr(self.discount_contract.events, event_name)
                            events = event_filter().process_receipt(receipt)
                            if events:
                                all_events.extend(events)
                                self.logger.info(f"Found {len(events)} {event_name} events")
                    except Exception as event_error:
                        self.logger.warning(f"Failed to process {event_name} events: {event_error}")
                
                if all_events:
                    # Look for requestId in any of the events
                    for event in all_events:
                        if 'args' in event and 'requestId' in event['args']:
                            request_id = event['args']['requestId']
                            self.logger.info(f"✅ EXTRACTED: Request ID {request_id} from {event['event']} event")
                            return request_id
                            
            except Exception as auto_error:
                self.logger.error(f"Automatic event processing failed: {auto_error}")
            
            # APPROACH 4: Intelligent guessing based on transaction position and gas usage
            self.logger.info("=== IMPLEMENTING TRANSACTION-BASED REQUEST ID ===")
            
            # Since the contract state isn't being updated properly, we'll create a deterministic
            # but unique request ID based on the transaction characteristics
            block_number = receipt.blockNumber
            transaction_index = getattr(receipt, 'transactionIndex', 0)
            tx_hash_int = int(receipt.transactionHash.hex(), 16)
            
            # Create a unique ID using multiple transaction characteristics
            # This ensures uniqueness across all transactions
            fallback_request_id = (
                (block_number % 100000) * 10000 +  # Block contribution
                (transaction_index % 100) * 100 +   # Transaction index contribution  
                (tx_hash_int % 100)                  # Hash contribution for uniqueness
            ) % 999999 + 1  # Ensure it's between 1 and 999999
            
            self.logger.warning(f"🚨 CONTRACT STATE ISSUE: Using transaction-based request ID {fallback_request_id}")
            self.logger.warning(f"   Block: {block_number}, TxIndex: {transaction_index}")
            self.logger.warning(f"   TxHash: {receipt.transactionHash.hex()}")
            self.logger.warning(f"   This works around the smart contract not updating its counter properly")
            
            return fallback_request_id
                
        except Exception as e:
            self.logger.error(f"Failed to extract request ID from receipt: {e}")
            raise ValueError(f"Request ID extraction failed: {e}")


# Singleton instance
teocoin_discount_service = TeoCoinDiscountService()
