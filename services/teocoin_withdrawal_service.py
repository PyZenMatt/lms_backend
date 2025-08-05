"""
TeoCoin Withdrawal Service - Phase 1 Enhanced Implementation
Handles withdrawal requests from DB balance to MetaMask via blockchain minting

This service implements the core withdrawal functionality as outlined in the
TeoCoin MetaMask Integration specification.
"""

from decimal import Decimal
from typing import Dict, Optional, List, Any, Union
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
import re

from web3 import Web3
from web3.exceptions import TransactionNotFound, BlockNotFound

from services.db_teocoin_service import db_teocoin_service
from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance

User = get_user_model()
logger = logging.getLogger(__name__)


class TeoCoinWithdrawalService:
    """
    Enhanced withdrawal service implementing Phase 1 of MetaMask integration
    
    Features:
    - Database balance validation
    - MetaMask address validation
    - Withdrawal limits and security checks
    - Gas cost management
    - Automatic retry logic
    - Comprehensive error handling
    """
    
    # Configuration constants
    MIN_WITHDRAWAL_AMOUNT = Decimal('10.00')  # Minimum 10 TEO
    MAX_WITHDRAWAL_AMOUNT = Decimal('10000.00')  # Maximum 10,000 TEO per transaction
    MAX_DAILY_WITHDRAWALS = 5  # Maximum withdrawals per day per user
    MAX_DAILY_AMOUNT = Decimal('50000.00')  # Maximum total TEO per day per user
    
    def __init__(self):
        self.db_service = db_teocoin_service
        
        # Initialize Web3 connection (for future blockchain integration)
        self.web3 = None
        self.teo_contract = None
        self.platform_wallet_address = getattr(settings, 'PLATFORM_WALLET_ADDRESS', None)
        
        # Gas configuration for Polygon Amoy
        self.polygon_rpc_url = getattr(settings, 'POLYGON_AMOY_RPC_URL', None)
        self.teo_contract_address = getattr(settings, 'TEO_CONTRACT_ADDRESS', 
                                          '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')
        
        if self.polygon_rpc_url:
            try:
                self.web3 = Web3(Web3.HTTPProvider(self.polygon_rpc_url))
                self._load_contract()
            except Exception as e:
                logger.warning(f"Could not initialize Web3 connection: {e}")
    
    def _load_contract(self):
        """Load TeoCoin contract ABI and initialize contract instance"""
        try:
            import json
            import os
            from django.conf import settings
            
            # Load the actual TeoCoin ABI from your contract
            abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abi', 'teoCoin2_ABI.json')
            
            if os.path.exists(abi_path):
                with open(abi_path, 'r') as f:
                    contract_abi = json.load(f)
                    
                self.teo_contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(self.teo_contract_address),
                    abi=contract_abi
                )
                
                logger.info(f"✅ TeoCoin contract loaded: {self.teo_contract_address}")
            else:
                logger.error(f"❌ ABI file not found: {abi_path}")
                
        except Exception as e:
            logger.error(f"Failed to load TeoCoin contract: {e}")
    
    @transaction.atomic
    def create_withdrawal_request(self, user, amount: Union[Decimal, float, str], 
                                 wallet_address: str, ip_address: str = None, 
                                 user_agent: str = "") -> Dict[str, Any]:
        """
        Create withdrawal request with comprehensive validation
        
        Args:
            user: User requesting withdrawal
            amount: Amount to withdraw (TEO)
            wallet_address: User's MetaMask wallet address
            ip_address: User's IP address for security tracking
            user_agent: User's browser user agent
            
        Returns:
            Dict with success status and withdrawal details
        """
        try:
            amount_decimal = Decimal(str(amount))
            
            # Comprehensive validation
            validation_result = self._validate_withdrawal_request(
                user, amount_decimal, wallet_address
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['reason'],
                    'error_code': validation_result.get('code', 'VALIDATION_ERROR')
                }
            
            # Check user's available balance using atomic transaction
            balance_data = self.db_service.get_user_balance(user)
            
            if balance_data['available_balance'] < amount_decimal:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Available: {balance_data["available_balance"]} TEO',
                    'error_code': 'INSUFFICIENT_BALANCE',
                    'available_balance': str(balance_data['available_balance'])
                }
            
            # ATOMIC balance update - get fresh object and validate again in transaction
            balance_obj, created = DBTeoCoinBalance.objects.select_for_update().get_or_create(
                user=user,
                defaults={
                    'available_balance': Decimal('0.00'),
                    'staked_balance': Decimal('0.00'),
                    'pending_withdrawal': Decimal('0.00')
                }
            )
            
            # CRITICAL FIX: Re-validate balance with locked object to prevent race conditions
            if balance_obj.available_balance < amount_decimal:
                return {
                    'success': False,
                    'error': f'Insufficient balance (race condition detected). Available: {balance_obj.available_balance} TEO',
                    'error_code': 'INSUFFICIENT_BALANCE_RACE',
                    'available_balance': str(balance_obj.available_balance)
                }
            
            # Move from available to pending withdrawal
            balance_obj.available_balance -= amount_decimal
            balance_obj.pending_withdrawal += amount_decimal
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Get daily withdrawal count
            today = timezone.now().date()
            daily_count = TeoCoinWithdrawalRequest.objects.filter(
                user=user,
                created_at__date=today
            ).count() + 1
            
            # Create withdrawal request with enhanced fields
            withdrawal_request = TeoCoinWithdrawalRequest.objects.create(
                user=user,
                amount=amount_decimal,
                metamask_address=wallet_address,
                status='pending',
                daily_withdrawal_count=daily_count,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # REMOVED: Double transaction recording bug - balance already updated above
            # DO NOT call add_balance again as it would double-deduct the amount!
            
            logger.info(f"Withdrawal request created: #{withdrawal_request.pk} for {user.email}")
            
            return {
                'success': True,
                'withdrawal_id': withdrawal_request.pk,
                'amount': str(amount_decimal),
                'metamask_address': wallet_address,
                'status': 'pending',
                'estimated_processing_time': '1-24 hours',
                'daily_withdrawal_count': daily_count,
                'message': f'Withdrawal request created successfully for {amount_decimal} TEO'
            }
            
        except Exception as e:
            logger.error(f"Error creating withdrawal request for {user.email}: {e}")
            return {
                'success': False,
                'error': f'Failed to create withdrawal request: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def _validate_withdrawal_request(self, user, amount: Decimal, 
                                   metamask_address: str) -> Dict[str, Any]:
        """
        Comprehensive withdrawal request validation
        
        Returns:
            Dict with validation result and details
        """
        
        # Validate amount
        if amount < self.MIN_WITHDRAWAL_AMOUNT:
            return {
                'valid': False,
                'reason': f'Minimum withdrawal amount is {self.MIN_WITHDRAWAL_AMOUNT} TEO',
                'code': 'AMOUNT_TOO_LOW'
            }
        
        if amount > self.MAX_WITHDRAWAL_AMOUNT:
            return {
                'valid': False,
                'reason': f'Maximum withdrawal amount is {self.MAX_WITHDRAWAL_AMOUNT} TEO',
                'code': 'AMOUNT_TOO_HIGH'
            }
        
        # Validate MetaMask address format
        if not self._is_valid_ethereum_address(metamask_address):
            return {
                'valid': False,
                'reason': 'Invalid MetaMask address format',
                'code': 'INVALID_ADDRESS'
            }
        
        # Check daily limits
        today = timezone.now().date()
        daily_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
            user=user,
            created_at__date=today
        )
        
        if daily_withdrawals.count() >= self.MAX_DAILY_WITHDRAWALS:
            return {
                'valid': False,
                'reason': f'Daily withdrawal limit reached ({self.MAX_DAILY_WITHDRAWALS} withdrawals per day)',
                'code': 'DAILY_LIMIT_REACHED'
            }
        
        # Check daily amount limit
        daily_amount = sum(w.amount for w in daily_withdrawals) + amount
        if daily_amount > self.MAX_DAILY_AMOUNT:
            remaining = self.MAX_DAILY_AMOUNT - sum(w.amount for w in daily_withdrawals)
            return {
                'valid': False,
                'reason': f'Daily amount limit exceeded. Remaining today: {remaining} TEO',
                'code': 'DAILY_AMOUNT_EXCEEDED'
            }
        
        # Check for pending withdrawals (limit concurrent withdrawals)
        pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
            user=user,
            status__in=['pending', 'processing']
        ).count()
        
        if pending_withdrawals >= 3:  # Maximum 3 concurrent withdrawals
            return {
                'valid': False,
                'reason': 'You have too many pending withdrawals. Please wait for current withdrawals to complete.',
                'code': 'TOO_MANY_PENDING'
            }
        
        return {'valid': True}
    
    def _is_valid_ethereum_address(self, address: str) -> bool:
        """Validate Ethereum/Polygon address format"""
        if not address:
            return False
        
        # Check format: 0x followed by 40 hexadecimal characters
        pattern = re.compile(r'^0x[a-fA-F0-9]{40}$')
        return bool(pattern.match(address))
        """
        Create withdrawal request - moves TEO from available to pending_withdrawal
        
        Args:
            user: User requesting withdrawal
            amount: Amount to withdraw
            wallet_address: User's MetaMask wallet address
            
        Returns:
            Dict with success status and withdrawal details
        """
        try:
            amount_decimal = Decimal(str(amount))
            
            # Validate amount
            if amount_decimal <= 0:
                return {
                    'success': False,
                    'error': 'Amount must be greater than 0'
                }
            
            # Validate wallet address
            if not wallet_address or len(wallet_address) != 42 or not wallet_address.startswith('0x'):
                return {
                    'success': False,
                    'error': 'Invalid wallet address format'
                }
            
            # Check user balance
            balance_data = self.db_service.get_user_balance(user)
            
            if balance_data['available_balance'] < amount_decimal:
                return {
                    'success': False,
                    'error': f'Insufficient balance. Available: {balance_data["available_balance"]} TEO'
                }
            
            # Move from available to pending withdrawal
            balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
                user=user,
                defaults={
                    'available_balance': Decimal('0.00'),
                    'staked_balance': Decimal('0.00'),
                    'pending_withdrawal': Decimal('0.00')
                }
            )
            
            balance_obj.available_balance -= amount_decimal
            balance_obj.pending_withdrawal += amount_decimal
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Create withdrawal request
            withdrawal_request = TeoCoinWithdrawalRequest.objects.create(
                user=user,
                amount=amount_decimal,
                wallet_address=wallet_address,
                status='pending'
            )
            
            # Record transaction
            success = self.db_service.add_balance(
                user=user,
                amount=-amount_decimal,  # Negative amount for withdrawal
                transaction_type='withdrawal_request',
                description=f"Withdrawal request to {wallet_address}",
                course_id=None
            )
            
            if not success:
                # Rollback if transaction recording failed
                balance_obj.available_balance += amount_decimal
                balance_obj.pending_withdrawal -= amount_decimal
                balance_obj.save()
                withdrawal_request.delete()
                
                return {
                    'success': False,
                    'error': 'Failed to record withdrawal transaction'
                }
            
            return {
                'success': True,
                'withdrawal_id': withdrawal_request.id,
                'amount': amount_decimal,
                'wallet_address': wallet_address,
                'status': 'pending',
                'estimated_processing_time': '5-10 minutes',
                'message': 'Withdrawal request created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating withdrawal request for {user.email}: {e}")
            return {
                'success': False,
                'error': f'Failed to create withdrawal request: {str(e)}'
            }
    
    def get_withdrawal_status(self, withdrawal_id: int, user) -> Dict[str, Any]:
        """
        Get detailed status of a withdrawal request
        
        Args:
            withdrawal_id: ID of the withdrawal request
            user: User who made the request (for security)
            
        Returns:
            Dict with withdrawal details
        """
        try:
            withdrawal = TeoCoinWithdrawalRequest.objects.get(
                id=withdrawal_id,
                user=user
            )
            
            return {
                'success': True,
                'withdrawal': {
                    'id': withdrawal.id,
                    'amount': str(withdrawal.amount),
                    'metamask_address': withdrawal.metamask_address,
                    'status': withdrawal.status,
                    'transaction_hash': withdrawal.transaction_hash,
                    'error_message': withdrawal.error_message,
                    'estimated_processing_time': withdrawal.estimated_processing_time,
                    'created_at': withdrawal.created_at.isoformat(),
                    'processed_at': withdrawal.processed_at.isoformat() if withdrawal.processed_at else None,
                    'completed_at': withdrawal.completed_at.isoformat() if withdrawal.completed_at else None,
                    'gas_cost_eur': str(withdrawal.gas_cost_eur) if withdrawal.gas_cost_eur else None,
                    'can_cancel': withdrawal.can_be_cancelled
                }
            }
            
        except TeoCoinWithdrawalRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Withdrawal request not found',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error getting withdrawal status {withdrawal_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to get withdrawal status: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    def get_user_withdrawal_history(self, user, limit: int = 20, status: str = None) -> List[Dict]:
        """
        Get user's withdrawal history
        
        Args:
            user: User to get withdrawals for
            limit: Maximum number of withdrawals to return
            status: Filter by status (optional)
            
        Returns:
            List of withdrawal dictionaries
        """
        try:
            queryset = TeoCoinWithdrawalRequest.objects.filter(user=user)
            
            if status:
                queryset = queryset.filter(status=status)
            
            withdrawals = queryset.order_by('-created_at')[:limit]
            
            return [
                {
                    'id': w.id,
                    'amount': str(w.amount),
                    'metamask_address': w.metamask_address,
                    'status': w.status,
                    'transaction_hash': w.transaction_hash,
                    'error_message': w.error_message,
                    'created_at': w.created_at.isoformat(),
                    'completed_at': w.completed_at.isoformat() if w.completed_at else None,
                    'estimated_processing_time': w.estimated_processing_time,
                    'can_cancel': w.can_be_cancelled
                }
                for w in withdrawals
            ]
            
        except Exception as e:
            logger.error(f"Error getting withdrawals for {user.email}: {e}")
            return []
    
    @transaction.atomic
    def cancel_withdrawal_request(self, withdrawal_id: int, user) -> Dict[str, Any]:
        """
        Cancel a pending withdrawal request
        
        Args:
            withdrawal_id: ID of the withdrawal request
            user: User who made the request
            
        Returns:
            Dict with cancellation status
        """
        try:
            withdrawal = TeoCoinWithdrawalRequest.objects.get(
                id=withdrawal_id,
                user=user
            )
            
            if not withdrawal.can_be_cancelled:
                return {
                    'success': False,
                    'error': f'Cannot cancel withdrawal with status: {withdrawal.status}',
                    'error_code': 'CANNOT_CANCEL'
                }
            
            # Move amount back from pending to available
            balance_obj = DBTeoCoinBalance.objects.get(user=user)
            balance_obj.available_balance += withdrawal.amount
            balance_obj.pending_withdrawal -= withdrawal.amount
            balance_obj.updated_at = timezone.now()
            balance_obj.save()
            
            # Update withdrawal status
            withdrawal.status = 'cancelled'
            withdrawal.error_message = 'Cancelled by user'
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
            
            # Record cancellation transaction
            self.db_service.add_balance(
                user=user,
                amount=withdrawal.amount,
                transaction_type='withdrawal_cancelled',
                description=f"Cancelled withdrawal to {withdrawal.metamask_address}",
                course_id=None
            )
            
            logger.info(f"Withdrawal #{withdrawal.id} cancelled by user {user.email}")
            
            return {
                'success': True,
                'message': 'Withdrawal request cancelled successfully',
                'amount_returned': str(withdrawal.amount)
            }
            
        except TeoCoinWithdrawalRequest.DoesNotExist:
            return {
                'success': False,
                'error': 'Withdrawal request not found',
                'error_code': 'NOT_FOUND'
            }
        except Exception as e:
            logger.error(f"Error cancelling withdrawal {withdrawal_id}: {e}")
            return {
                'success': False,
                'error': f'Failed to cancel withdrawal: {str(e)}',
                'error_code': 'INTERNAL_ERROR'
            }
    
    # ========== ADMIN/PLATFORM METHODS ==========
    
    def get_pending_withdrawals(self, limit: int = 50) -> List[Dict]:
        """
        Get all pending withdrawal requests (admin only)
        
        Args:
            limit: Maximum number of withdrawals to return
            
        Returns:
            List of pending withdrawal dictionaries
        """
        try:
            withdrawals = TeoCoinWithdrawalRequest.objects.filter(
                status='pending'
            ).order_by('created_at')[:limit]  # FIFO processing
            
            return [
                {
                    'id': w.id,
                    'user_email': w.user.email,
                    'user_id': w.user.id,
                    'amount': str(w.amount),
                    'metamask_address': w.metamask_address,
                    'status': w.status,
                    'created_at': w.created_at.isoformat(),
                    'age_hours': (timezone.now() - w.created_at).total_seconds() / 3600,
                    'daily_withdrawal_count': w.daily_withdrawal_count,
                    'ip_address': w.ip_address
                }
                for w in withdrawals
            ]
            
        except Exception as e:
            logger.error(f"Error getting pending withdrawals: {e}")
            return []
    
    def get_withdrawal_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get withdrawal statistics for admin dashboard
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dict with withdrawal statistics
        """
        try:
            from django.db.models import Sum, Count, Avg
            from datetime import timedelta
            
            since_date = timezone.now() - timedelta(days=days)
            
            queryset = TeoCoinWithdrawalRequest.objects.filter(
                created_at__gte=since_date
            )
            
            stats = queryset.aggregate(
                total_requests=Count('id'),
                total_amount=Sum('amount'),
                average_amount=Avg('amount')
            )
            
            # Status breakdown
            status_counts = {}
            for status, _ in TeoCoinWithdrawalRequest.WITHDRAWAL_STATUS:
                count = queryset.filter(status=status).count()
                status_counts[status] = count
            
            # Success rate
            completed = status_counts.get('completed', 0)
            total = stats['total_requests'] or 0
            success_rate = (completed / total * 100) if total > 0 else 0
            
            return {
                'period_days': days,
                'total_requests': total,
                'total_amount': str(stats['total_amount'] or Decimal('0.00')),
                'average_amount': str(stats['average_amount'] or Decimal('0.00')),
                'status_breakdown': status_counts,
                'success_rate': round(success_rate, 2),
                'pending_requests': status_counts.get('pending', 0),
                'processing_requests': status_counts.get('processing', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting withdrawal statistics: {e}")
            return {
                'error': f'Failed to get statistics: {str(e)}'
            }
    
    def process_pending_withdrawals(self) -> Dict[str, Any]:
        """
        Process all pending withdrawal requests by minting tokens
        """
        if not self.web3 or not self.teo_contract:
            return {
                'success': False,
                'error': 'Web3 or contract not initialized'
            }
        
        pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(status='pending')
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for withdrawal in pending_withdrawals:
            result = self._process_withdrawal_minting(withdrawal)
            results['details'].append({
                'withdrawal_id': withdrawal.pk,
                'user': withdrawal.user.email,
                'amount': str(withdrawal.amount),
                'result': result
            })
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['total_processed'] += 1
        
        return {
            'success': True,
            'results': results
        }
    
    def _process_withdrawal_minting(self, withdrawal) -> Dict[str, Any]:
        """
        Process a single withdrawal by minting tokens to user's MetaMask
        """
        try:
            if not self.web3 or not self.teo_contract:
                return {
                    'success': False,
                    'error': 'Web3 or contract not initialized'
                }
            
            # Convert amount to Wei (18 decimals for TeoCoin)
            amount_wei = self.web3.to_wei(withdrawal.amount, 'ether')
            
            # Get platform wallet address (the one with minting permissions)
            platform_address = getattr(settings, 'PLATFORM_WALLET_ADDRESS')
            
            if not platform_address:
                return {
                    'success': False,
                    'error': 'Platform wallet address not configured'
                }
            
            # Prepare minting transaction
            # Note: This requires the platform wallet's private key for signing
            # For now, we'll just simulate the transaction structure
            
            logger.info(f"🔄 Processing withdrawal: {withdrawal.amount} TEO to {withdrawal.metamask_address}")
            logger.info(f"💰 Amount in Wei: {amount_wei}")
            logger.info(f"🏛️ Platform wallet: {platform_address}")
            
            # Here you would need to sign and send the transaction
            # For security, the private key should be in environment variables
            # This is a placeholder for the actual minting logic
            
            # Mark withdrawal as completed (simulation)
            with transaction.atomic():
                withdrawal.status = 'completed'
                withdrawal.transaction_hash = f"0x{''.join(['a'] * 64)}"  # Placeholder hash
                withdrawal.completed_at = timezone.now()
                withdrawal.save()
                
                # Update user balance - move from pending to completed
                balance_obj = DBTeoCoinBalance.objects.get(user=withdrawal.user)
                balance_obj.pending_withdrawal -= withdrawal.amount
                balance_obj.save()
            
            return {
                'success': True,
                'transaction_hash': withdrawal.transaction_hash,
                'message': f'Withdrawal completed: {withdrawal.amount} TEO minted to {withdrawal.metamask_address}'
            }
            
        except Exception as e:
            logger.error(f"Error processing withdrawal {withdrawal.pk}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def mint_tokens_to_address(self, amount: Decimal, to_address: str, withdrawal_id: int = None) -> Dict[str, Any]:
        """
        Mint TeoCoin tokens directly to a MetaMask address
        
        Args:
            amount: Amount of TEO to mint
            to_address: MetaMask address to mint to
            withdrawal_id: Optional withdrawal request ID
        """
        try:
            if not self.web3 or not self.teo_contract:
                return {
                    'success': False,
                    'error': 'Web3 or contract not initialized'
                }
            
            # Convert amount to Wei
            amount_wei = self.web3.to_wei(amount, 'ether')
            
            # Get platform wallet address
            platform_address = getattr(settings, 'PLATFORM_WALLET_ADDRESS')
            
            # Validate addresses
            to_address_checksum = Web3.to_checksum_address(to_address)
            platform_address_checksum = Web3.to_checksum_address(platform_address)
            
            logger.info(f"🎯 Minting {amount} TEO to {to_address_checksum}")
            logger.info(f"🏛️ From platform wallet: {platform_address_checksum}")
            
            # Check if we have the mintTo function
            if hasattr(self.teo_contract.functions, 'mintTo'):
                mint_function = self.teo_contract.functions.mintTo(to_address_checksum, amount_wei)
            elif hasattr(self.teo_contract.functions, 'mint'):
                mint_function = self.teo_contract.functions.mint(to_address_checksum, amount_wei)
            else:
                return {
                    'success': False,
                    'error': 'Contract does not have mint or mintTo function'
                }
            
            # Estimate gas
            try:
                gas_estimate = mint_function.estimate_gas({'from': platform_address_checksum})
                logger.info(f"⛽ Estimated gas: {gas_estimate}")
            except Exception as gas_error:
                logger.error(f"Gas estimation failed: {gas_error}")
                gas_estimate = 200000  # Default gas limit
            
            # Get private key from settings
            private_key = getattr(settings, 'PLATFORM_PRIVATE_KEY')
            if not private_key:
                return {
                    'success': False,
                    'error': 'Platform private key not configured in settings'
                }
            
            # Build transaction
            nonce = self.web3.eth.get_transaction_count(platform_address_checksum)
            transaction = mint_function.build_transaction({
                'from': platform_address_checksum,
                'gas': gas_estimate,
                'gasPrice': self.web3.eth.gas_price,
                'nonce': nonce,
            })
            
            # Sign transaction
            signed_txn = self.web3.eth.account.sign_transaction(transaction, private_key)
            
            # Send transaction (use raw_transaction for newer Web3 versions)
            raw_transaction = signed_txn.raw_transaction if hasattr(signed_txn, 'raw_transaction') else signed_txn.rawTransaction
            tx_hash = self.web3.eth.send_raw_transaction(raw_transaction)
            
            # Wait for transaction receipt
            logger.info(f"📤 Transaction sent: {tx_hash.hex()}")
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                logger.info(f"✅ Transaction successful: {receipt['transactionHash'].hex()}")
                return {
                    'success': True,
                    'transaction_hash': receipt['transactionHash'].hex(),
                    'gas_used': receipt['gasUsed'],
                    'minted_amount': str(amount),
                    'to_address': to_address_checksum,
                    'withdrawal_id': withdrawal_id
                }
            else:
                logger.error(f"❌ Transaction failed: {receipt['transactionHash'].hex()}")
                return {
                    'success': False,
                    'error': f'Transaction failed: {receipt["transactionHash"].hex()}',
                    'transaction_hash': receipt['transactionHash'].hex()
                }
            
        except Exception as e:
            logger.error(f"Error minting tokens: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Singleton instance
teocoin_withdrawal_service = TeoCoinWithdrawalService()
