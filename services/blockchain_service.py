"""
Blockchain Service - Business Logic for Blockchain Operations

Handles all blockchain-related operations including wallet management,
token operations, balance queries, and transaction tracking.
"""

from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings
import logging
import time
import uuid

from services.base import TransactionalService
from services.exceptions import (
    TeoArtServiceException,
    WalletNotFoundError,
    InvalidWalletAddressError, 
    TokenTransferError,
    MintingError,
    InvalidAmountError,
    BlockchainTransactionError,
)

# Import blockchain models
from rewards.models import BlockchainTransaction, TokenBalance
from blockchain.blockchain import TeoCoinService

User = get_user_model()


class BlockchainService(TransactionalService):
    """
    Service for managing blockchain operations.
    
    Handles wallet linking, token operations, balance queries,
    and transaction tracking for the TeoCoin system.
    """
    
    def __init__(self):
        super().__init__()
        self.teocoin_service = TeoCoinService()
        self.test_mode = getattr(settings, 'DEBUG', False)
    
    def get_user_wallet_balance(self, user: User) -> Dict[str, Any]:
        """
        Get wallet balance for a user.
        
        Args:
            user: User instance
            
        Returns:
            Dict containing balance information
            
        Raises:
            BlockchainTransactionError: If wallet not linked or query fails
        """
        try:
            self.log_info(f"Getting wallet balance for user {user.id}")
            start_time = time.time()
            
            if not user.wallet_address:
                raise WalletNotFoundError(user.id)
            
            # Query blockchain for current balance
            if self.test_mode:
                # Mock balance for testing
                balance = Decimal('100.0')
                self.log_debug(f"Using test mode balance: {balance}")
            else:
                balance = self.teocoin_service.get_balance(user.wallet_address)
            
            # Update cached balance
            token_balance, created = TokenBalance.objects.get_or_create(
                user=user,
                defaults={'balance': balance}
            )
            if not created:
                token_balance.balance = balance
                token_balance.save(update_fields=['balance', 'updated_at'])
            
            query_time = time.time() - start_time
            self.log_info(f"Balance query completed in {query_time:.3f}s for user {user.id}")
            
            return {
                'balance': str(balance),
                'wallet_address': user.wallet_address,
                'user_id': user.id,
                'username': user.username,
                'query_time': f"{query_time:.3f}s",
                'token_info': {
                    'name': 'TeoCoin',
                    'symbol': 'TEO',
                    'decimals': 18
                }
            }
            
        except BlockchainTransactionError:
            raise
        except Exception as e:
            self.log_error(f"Error getting balance for user {user.id}: {str(e)}")
            raise BlockchainTransactionError(f"Failed to get wallet balance: {str(e)}")
    
    def link_wallet_to_user(self, user: User, wallet_address: str) -> Dict[str, Any]:
        """
        Link a wallet address to a user account.
        
        Args:
            user: User instance
            wallet_address: Ethereum/Polygon wallet address
            
        Returns:
            Dict with linking result
            
        Raises:
            BlockchainTransactionError: If validation fails or address already used
        """
        def _link_operation():
            self.log_info(f"Linking wallet {wallet_address} to user {user.id}")
            
            # Validate wallet address format
            if not self._is_valid_wallet_address(wallet_address):
                raise BlockchainTransactionError(
                    "Invalid wallet address format",
                    code="INVALID_WALLET_FORMAT",
                    status_code=400
                )
            
            # Check if address is already used
            existing_user = User.objects.filter(wallet_address=wallet_address).first()
            if existing_user and existing_user != user:
                raise BlockchainTransactionError(
                    f"Wallet address already linked to user {existing_user.username}",
                    code="WALLET_ALREADY_LINKED",
                    status_code=400
                )
            
            # Link wallet to user
            user.wallet_address = wallet_address
            user.save(update_fields=['wallet_address'])
            
            # Get initial balance
            try:
                balance_info = self.get_user_wallet_balance(user)
                initial_balance = balance_info['balance']
            except Exception as e:
                self.log_error(f"Failed to get initial balance: {str(e)}")
                initial_balance = "0"
            
            self.log_info(f"Successfully linked wallet {wallet_address} to user {user.id}")
            
            return {
                'message': 'Wallet successfully linked',
                'wallet_address': wallet_address,
                'balance': initial_balance,
                'user_id': user.id
            }
        
        try:
            return self.execute_in_transaction(_link_operation)
        except BlockchainTransactionError:
            raise
        except Exception as e:
            self.log_error(f"Error linking wallet for user {user.id}: {str(e)}")
            raise BlockchainTransactionError(f"Failed to link wallet: {str(e)}")
    
    def mint_tokens_to_user(self, user: User, amount: Union[Decimal, float, str], reason: str = "System reward") -> Dict[str, Any]:
        """
        Mint tokens to a user's wallet.
        
        Args:
            user: User instance
            amount: Amount of tokens to mint
            reason: Reason for minting
            
        Returns:
            Dict with minting result
            
        Raises:
            BlockchainTransactionError: If minting fails
        """
        def _mint_operation():
            amount_decimal = Decimal(str(amount))
            
            self.log_info(f"Minting {amount_decimal} tokens to user {user.id} for: {reason}")
            
            if not user.wallet_address:
                raise BlockchainTransactionError(
                    "User does not have a linked wallet address",
                    code="WALLET_NOT_LINKED",
                    status_code=400
                )
            
            if amount_decimal <= 0:
                raise BlockchainTransactionError(
                    "Amount must be positive",
                    code="INVALID_AMOUNT",
                    status_code=400
                )
            
            # Mint tokens
            if self.test_mode:
                # Mock transaction for testing with more randomness
                tx_hash = f"0xtest_mint_{user.id}_{uuid.uuid4().hex[:8]}"
                self.log_debug(f"Using test mode transaction hash: {tx_hash}")
            else:
                tx_hash = self.teocoin_service.mint_tokens(user.wallet_address, amount_decimal)
            
            # Record transaction
            blockchain_tx = BlockchainTransaction.objects.create(
                user=user,
                transaction_type='mint',
                amount=amount_decimal,
                to_address=user.wallet_address,
                tx_hash=tx_hash,
                status='completed',
                notes=reason
            )
            
            # Update cached balance
            self._update_user_token_balance(user, amount_decimal, add=True)
            
            self.log_info(f"Successfully minted {amount_decimal} tokens to user {user.id}")
            
            return {
                'transaction_hash': tx_hash,
                'amount': str(amount_decimal),
                'recipient': user.wallet_address,
                'user_id': user.id,
                'reason': reason,
                'blockchain_transaction_id': blockchain_tx.id
            }
        
        try:
            return self.execute_in_transaction(_mint_operation)
        except BlockchainTransactionError:
            raise
        except Exception as e:
            self.log_error(f"Error minting tokens for user {user.id}: {str(e)}")
            raise BlockchainTransactionError(f"Failed to mint tokens: {str(e)}")
    
    def get_user_transaction_history(self, user: User, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get transaction history for a user.
        
        Args:
            user: User instance
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction data
        """
        try:
            self.log_info(f"Getting transaction history for user {user.id}")
            
            transactions = BlockchainTransaction.objects.filter(
                user=user
            ).order_by('-created_at')[:limit]
            
            tx_list = []
            for tx in transactions:
                tx_data = {
                    'id': tx.id,
                    'transaction_type': tx.transaction_type,
                    'amount': str(tx.amount),
                    'status': tx.status,
                    'tx_hash': tx.tx_hash,
                    'from_address': tx.from_address,
                    'to_address': tx.to_address,
                    'created_at': tx.created_at.isoformat(),
                    'notes': tx.notes,
                }
                tx_list.append(tx_data)
            
            self.log_info(f"Retrieved {len(tx_list)} transactions for user {user.id}")
            
            return tx_list
            
        except Exception as e:
            self.log_error(f"Error getting transaction history for user {user.id}: {str(e)}")
            raise BlockchainTransactionError(f"Failed to get transaction history: {str(e)}")
    
    def transfer_tokens_between_users(self, from_user: User, to_user: User, amount: Union[Decimal, float, str], reason: str = "Transfer") -> Dict[str, Any]:
        """
        Transfer tokens between two users.
        
        Args:
            from_user: Sender user
            to_user: Recipient user
            amount: Amount to transfer
            reason: Reason for transfer
            
        Returns:
            Dict with transfer result
            
        Raises:
            BlockchainTransactionError: If transfer fails
        """
        def _transfer_operation():
            amount_decimal = Decimal(str(amount))
            
            self.log_info(f"Transferring {amount_decimal} tokens from user {from_user.id} to user {to_user.id}")
            
            # Validate both users have wallets
            if not from_user.wallet_address:
                raise BlockchainTransactionError(
                    "Sender does not have a linked wallet address",
                    code="SENDER_WALLET_NOT_LINKED",
                    status_code=400
                )
            
            if not to_user.wallet_address:
                raise BlockchainTransactionError(
                    "Recipient does not have a linked wallet address",
                    code="RECIPIENT_WALLET_NOT_LINKED",
                    status_code=400
                )
            
            if amount_decimal <= 0:
                raise BlockchainTransactionError(
                    "Amount must be positive",
                    code="INVALID_AMOUNT",
                    status_code=400
                )
            
            # Check sender balance
            sender_balance_info = self.get_user_wallet_balance(from_user)
            sender_balance = Decimal(sender_balance_info['balance'])
            
            if sender_balance < amount_decimal:
                raise BlockchainTransactionError(
                    f"Insufficient balance. Required: {amount_decimal}, Available: {sender_balance}",
                    code="INSUFFICIENT_BALANCE",
                    status_code=400
                )
            
            # Execute transfer
            if self.test_mode:
                tx_hash = f"0xtest_transfer_{from_user.id}_{to_user.id}_{uuid.uuid4().hex[:8]}"
                self.log_debug(f"Using test mode transaction hash: {tx_hash}")
            else:
                tx_hash = self.teocoin_service.transfer_tokens(
                    from_user.wallet_address,
                    to_user.wallet_address,
                    amount_decimal
                )
            
            # Record transaction for sender
            BlockchainTransaction.objects.create(
                user=from_user,
                transaction_type='transfer',
                amount=amount_decimal,
                from_address=from_user.wallet_address,
                to_address=to_user.wallet_address,
                tx_hash=tx_hash,
                status='completed',
                notes=f"Transfer to {to_user.username}: {reason}"
            )
            
            # Record transaction for recipient
            BlockchainTransaction.objects.create(
                user=to_user,
                transaction_type='transfer',
                amount=amount_decimal,
                from_address=from_user.wallet_address,
                to_address=to_user.wallet_address,
                tx_hash=tx_hash,
                status='completed',
                notes=f"Transfer from {from_user.username}: {reason}"
            )
            
            # Update cached balances
            self._update_user_token_balance(from_user, amount_decimal, add=False)
            self._update_user_token_balance(to_user, amount_decimal, add=True)
            
            self.log_info(f"Successfully transferred {amount_decimal} tokens from user {from_user.id} to user {to_user.id}")
            
            return {
                'transaction_hash': tx_hash,
                'amount': str(amount_decimal),
                'from_user': from_user.username,
                'to_user': to_user.username,
                'from_address': from_user.wallet_address,
                'to_address': to_user.wallet_address,
                'reason': reason
            }
        
        try:
            return self.execute_in_transaction(_transfer_operation)
        except BlockchainTransactionError:
            raise
        except Exception as e:
            self.log_error(f"Error transferring tokens: {str(e)}")
            raise BlockchainTransactionError(f"Failed to transfer tokens: {str(e)}")
    
    def _is_valid_wallet_address(self, address: str) -> bool:
        """Validate Ethereum/Polygon wallet address format."""
        if not address or not isinstance(address, str):
            return False
        
        # Basic validation: starts with 0x and is 42 characters long
        return address.startswith('0x') and len(address) == 42 and all(
            c in '0123456789abcdefABCDEF' for c in address[2:]
        )
    
    def _update_user_token_balance(self, user: User, amount: Decimal, add: bool = True):
        """Update cached token balance for user."""
        try:
            token_balance, created = TokenBalance.objects.get_or_create(
                user=user,
                defaults={'balance': Decimal('0')}
            )
            
            if add:
                token_balance.balance += amount
            else:
                token_balance.balance -= amount
                if token_balance.balance < 0:
                    token_balance.balance = Decimal('0')
            
            token_balance.save(update_fields=['balance', 'updated_at'])
            
        except Exception as e:
            self.log_error(f"Error updating cached balance for user {user.id}: {str(e)}")


# Singleton instance for easy access
blockchain_service = BlockchainService()
