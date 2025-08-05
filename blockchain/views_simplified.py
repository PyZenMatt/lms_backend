"""
Simplified Blockchain API Views for TeoCoin System

This module provides essential REST API endpoints for blockchain operations:
- Wallet balance queries (for MetaMask integration)
- Token information (for frontend display)  
- Transaction status checking (for burn deposit verification)

All complex course payment, staking, and reward pool functionality has been
moved to the DB-based TeoCoin system for improved performance and reliability.

Security Note: This implementation is for educational/testnet use only.
Production deployments should implement additional security measures.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from decimal import Decimal
import json
import logging
import time

from services.consolidated_teocoin_service import teocoin_service
from services.blockchain_service import blockchain_service
from rewards.models import BlockchainTransaction, TokenBalance

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    """
    Get the TeoCoin balance for the authenticated user.
    
    Returns the current token balance for the user's linked wallet address.
    Also updates the cached balance in the database.
    
    Returns:
        JSON response with:
        - balance: Current token balance as string
        - wallet_address: User's linked wallet address
        - token_info: General token information
        - user_id: User ID for frontend verification
        - username: Username for debugging
        
    Errors:
        - 400: Wallet not linked to user account
        - 500: Blockchain query error
    """
    import time
    start_time = time.time()
    
    user = request.user
    
    try:
        # Use BlockchainService to get wallet balance
        result = blockchain_service.get_user_wallet_balance(user)
        
        response_time = time.time() - start_time
        logger.info(f"Balance API completed in {response_time:.3f}s via BlockchainService")
        if response_time > 1.0:
            logger.warning(f"Slow Balance API: {response_time:.3f}s for user {user.username}")
            
        return Response(result)
        
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Error retrieving balance for {user.email}: {e}")
        
        # Fallback to old logic for safety during transition
        if not user.wallet_address:
            response_time = time.time() - start_time
            logger.info(f"Balance API (no wallet) completed in {response_time:.3f}s")
            return Response({
                'error': 'Wallet not linked',
                'balance': '0',
                'wallet_address': None
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # First check if we have a cached balance that's recent enough
            token_balance, created = TokenBalance.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('0')}
            )
            
            # Only query blockchain if:
            # 1. We've just created the balance record OR
            # 2. The cached balance is stale (older than 5 minutes)
            if created or token_balance.is_stale(minutes=5):
                balance = teocoin_service.get_balance(user.wallet_address)
                token_balance.balance = balance
                token_balance.save()
                logger.info(f"Updated blockchain balance for {user.username} from RPC call")
            else:
                balance = token_balance.balance
                logger.info(f"Using cached blockchain balance for {user.username} (last updated: {token_balance.last_updated})")
            
            return Response({
                'balance': str(balance),
                'wallet_address': user.wallet_address,
                'token_info': teocoin_service.get_token_info(),
                'user_id': user.id,  # Add user ID for frontend verification
                'username': user.username,  # Add username for debugging
                'cached': not created and not token_balance.is_stale(minutes=5)  # Indicate if we used the cache
            })
        
        except Exception as e2:
            logger.error(f"Error retrieving balance for {user.email}: {e2}")
            return Response({
                'error': 'Error retrieving wallet balance',
                'balance': '0'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            response_time = time.time() - start_time
            logger.info(f"Balance API completed in {response_time:.3f}s")
            if response_time > 1.0:
                logger.warning(f"Slow Balance API: {response_time:.3f}s for user {user.username}")


@api_view(['GET'])
def get_token_info(request):
    """
    Get general information about the TeoCoin token.
    
    This endpoint provides public information about the TeoCoin token
    including contract details, symbol, decimals, etc. No authentication required.
    
    Returns:
        JSON response with token information:
        - name: Token name
        - symbol: Token symbol
        - decimals: Number of decimal places
        - contract_address: Smart contract address
        - network: Blockchain network name
        
    Errors:
        - 500: Blockchain query error
    """
    try:
        token_info = teocoin_service.get_token_info()
        return Response(token_info)
    except Exception as e:
        logger.error(f"Error retrieving token info: {e}")
        return Response({
            'error': 'Error retrieving token information'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_transaction_status(request):
    """
    Check the status of a blockchain transaction.
    
    Queries the blockchain for transaction receipt and updates the local
    database record if the transaction has been confirmed or failed.
    
    Request Body:
        tx_hash (str): Blockchain transaction hash to check
        
    Returns:
        JSON response with:
        - status: Transaction status (confirmed, failed, pending)
        - block_number: Block number (if confirmed)
        - gas_used: Gas used by transaction (if confirmed)
        - transaction_hash: Transaction hash
        - message: Status message (if pending)
        
    Errors:
        - 400: Missing tx_hash parameter
        - 500: Blockchain query error
    """
    tx_hash = request.data.get('tx_hash')
    
    if not tx_hash:
        return Response({
            'error': 'tx_hash is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        receipt = teocoin_service.get_transaction_receipt(tx_hash)
        
        if receipt:
            # Update transaction status in database if record exists
            try:
                blockchain_tx = BlockchainTransaction.objects.get(tx_hash=tx_hash)
                if receipt['status'] == 1:
                    blockchain_tx.status = 'confirmed'
                    blockchain_tx.block_number = receipt['block_number']
                    blockchain_tx.gas_used = receipt['gas_used']
                else:
                    blockchain_tx.status = 'failed'
                blockchain_tx.save()
            except BlockchainTransaction.DoesNotExist:
                # Transaction not found in our database - this is OK
                pass
            
            return Response({
                'status': 'confirmed' if receipt['status'] == 1 else 'failed',
                'block_number': receipt['block_number'],
                'gas_used': receipt['gas_used'],
                'transaction_hash': receipt['transaction_hash']
            })
        else:
            return Response({
                'status': 'pending',
                'message': 'Transaction still in progress'
            })
    
    except Exception as e:
        logger.error(f"Error checking transaction status {tx_hash}: {e}")
        return Response({
            'error': 'Error checking transaction status'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
