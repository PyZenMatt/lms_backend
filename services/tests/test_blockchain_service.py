"""
Unit tests for Blockchain Service

This module contains tests specifically for the BlockchainService,
ensuring all business logic methods work correctly in isolation.
"""

import unittest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from services.blockchain_service import BlockchainService
from services.exceptions import (
    WalletNotFoundError,
    InvalidWalletAddressError,
    TokenTransferError,
    MintingError,
    InvalidAmountError,
    BlockchainTransactionError,
)

User = get_user_model()


class BlockchainServiceTest(TestCase):
    """Test the BlockchainService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = BlockchainService()
        self.service.test_mode = True  # Set test mode after instantiation
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='student'  # Required field
        )
        # Simulate wallet_address attribute if it exists
        if hasattr(self.user, 'wallet_address'):
            self.user.wallet_address = '0x1234567890123456789012345678901234567890'
            self.user.save()
            
        self.user_no_wallet = User.objects.create_user(
            username='testusernowal',
            email='nowal@example.com',
            role='student'  # Required field
        )
    
    def test_get_user_wallet_balance_success(self):
        """Test successful wallet balance retrieval"""
        result = self.service.get_user_wallet_balance(self.user)
        
        self.assertIn('balance', result)
        self.assertIn('wallet_address', result)
        self.assertIn('user_id', result)
        self.assertEqual(result['user_id'], self.user.id)
        self.assertEqual(result['wallet_address'], self.user.wallet_address)
    
    def test_get_user_wallet_balance_no_wallet(self):
        """Test wallet balance retrieval for user without wallet"""
        with self.assertRaises(BlockchainTransactionError):
            self.service.get_user_wallet_balance(self.user_no_wallet)
    
    def test_link_wallet_to_user_success(self):
        """Test successful wallet linking"""
        wallet_address = '0x9876543210987654321098765432109876543210'
        
        result = self.service.link_wallet_to_user(self.user_no_wallet, wallet_address)
        
        self.assertIn('message', result)
        self.assertIn('wallet_address', result)
        self.assertIn('balance', result)
        self.assertEqual(result['wallet_address'], wallet_address)
        
        # Verify user was updated
        self.user_no_wallet.refresh_from_db()
        self.assertEqual(self.user_no_wallet.wallet_address, wallet_address)
    
    def test_link_wallet_invalid_address(self):
        """Test wallet linking with invalid address"""
        with patch.object(self.service.teocoin_service, 'validate_address', return_value=False):
            with self.assertRaises(BlockchainTransactionError):
                self.service.link_wallet_to_user(self.user_no_wallet, 'invalid_address')
    
    def test_link_wallet_already_used(self):
        """Test wallet linking with address already in use"""
        # User already has this wallet
        with self.assertRaises(BlockchainTransactionError):
            self.service.link_wallet_to_user(self.user_no_wallet, self.user.wallet_address)
    
    def test_mint_tokens_to_user_success(self):
        """Test successful token minting"""
        amount = Decimal('50.0')
        reason = 'Test reward'
        
        with patch.object(self.service.teocoin_service, 'mint_tokens', return_value='0xabcdef') as mock_mint:
            with patch.object(self.service, 'test_mode', False):  # Force real blockchain call
                result = self.service.mint_tokens_to_user(self.user, amount, reason)
                
                self.assertIn('transaction_hash', result)
                self.assertIn('amount', result)
                self.assertIn('recipient', result)
                self.assertEqual(result['amount'], '50.0')
                mock_mint.assert_called_once()
    
    def test_mint_tokens_no_wallet(self):
        """Test token minting for user without wallet"""
        with self.assertRaises(BlockchainTransactionError):
            self.service.mint_tokens_to_user(self.user_no_wallet, 50.0, 'Test')
    
    def test_mint_tokens_invalid_amount(self):
        """Test token minting with invalid amount"""
        with self.assertRaises(BlockchainTransactionError):
            self.service.mint_tokens_to_user(self.user, -10.0, 'Test')
        
        with self.assertRaises(InvalidAmountError):
            self.service.mint_tokens_to_user(self.user, 0, 'Test')
    
    def test_get_user_transaction_history_success(self):
        """Test successful transaction history retrieval"""
        # Create mock transaction
        with patch('rewards.models.BlockchainTransaction.objects') as mock_objects:
            mock_tx = Mock()
            mock_tx.transaction_type = 'mint'
            mock_tx.amount = Decimal('25.0')
            mock_tx.tx_hash = '0xabcdef'
            mock_tx.from_address = None
            mock_tx.to_address = self.user.wallet_address
            mock_tx.status = 'confirmed'
            mock_tx.created_at.isoformat.return_value = '2023-01-01T00:00:00'
            mock_tx.confirmed_at.isoformat.return_value = '2023-01-01T00:01:00'
            
            mock_objects.filter.return_value.order_by.return_value.__getitem__.return_value = [mock_tx]
            
            result = self.service.get_user_transaction_history(self.user, limit=10)
            
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['transaction_type'], 'mint')
            self.assertEqual(result[0]['amount'], '25.0')
    
    def test_transfer_tokens_between_users_success(self):
        """Test successful token transfer between users"""
        to_user = User.objects.create_user(
            username='touser',
            email='to@example.com',
            role='student',
            wallet_address='0x1111111111111111111111111111111111111111'
        )
        amount = Decimal('25.0')
        
        with patch.object(self.service.teocoin_service, 'get_balance', return_value=Decimal('100.0')):
            with patch.object(self.service.teocoin_service, 'transfer_tokens', return_value='0xabcdef'):
                result = self.service.transfer_tokens_between_users(self.user, to_user, amount, 'Test transfer')
                
                self.assertIn('message', result)
                self.assertIn('amount', result)
                self.assertIn('tx_hash', result)
                self.assertIn('from_user', result)
                self.assertIn('to_user', result)
                self.assertEqual(result['amount'], amount)
    
    def test_transfer_tokens_insufficient_balance(self):
        """Test token transfer with insufficient balance"""
        to_user = User.objects.create_user(
            username='touser',
            email='to@example.com',
            role='student',
            wallet_address='0x1111111111111111111111111111111111111111'
        )
        
        with patch.object(self.service.teocoin_service, 'get_balance', return_value=Decimal('10.0')):
            with self.assertRaises(BlockchainTransactionError):
                self.service.transfer_tokens_between_users(self.user, to_user, 50.0, 'Test transfer')
    
    def test_transfer_tokens_no_wallet(self):
        """Test token transfer with users without wallets"""
        with self.assertRaises(BlockchainTransactionError):
            self.service.transfer_tokens_between_users(self.user_no_wallet, self.user, 25.0, 'Test')
        
        with self.assertRaises(WalletNotFoundError):
            self.service.transfer_tokens_between_users(self.user, self.user_no_wallet, 25.0, 'Test')


if __name__ == '__main__':
    unittest.main()
