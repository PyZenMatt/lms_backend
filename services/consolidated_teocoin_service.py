"""
Consolidated TeoCoin Blockchain Service

This service provides essential blockchain functionality for the DB-based TeoCoin system:
- Token minting (for withdrawals to MetaMask)
- Balance queries (for burn deposit verification)
- Transaction verification (for burn deposits)
- Address validation

All core operations (rewards, discounts, transfers) use the DB-based system.
"""
import time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from django.conf import settings

logger = logging.getLogger(__name__)


class ConsolidatedTeoCoinService:
    """
    Simplified blockchain service for essential operations only.
    
    Used for:
    - Withdrawals: Minting tokens to user MetaMask wallets
    - Burn deposits: Verifying transactions from MetaMask to platform
    - Balance queries: For verification and display purposes
    """
    
    def __init__(self):
        """Initialize Web3 connection and contract."""
        # Configuration
        self.rpc_url = getattr(settings, 'POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', None)
        self.admin_private_key = getattr(settings, 'ADMIN_PRIVATE_KEY', None)
        
        if not self.contract_address:
            raise ValueError("TEOCOIN_CONTRACT_ADDRESS must be configured")
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add PoA middleware for Polygon
        try:
            from web3.middleware import ExtraDataToPOAMiddleware
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        except ImportError:
            logger.warning("Could not load PoA middleware")
        
        # Verify connection
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Polygon Amoy network")
        
        # Load contract ABI
        self._load_contract()
        
        logger.info(f"ConsolidatedTeoCoinService initialized - Contract: {self.contract_address}")
    
    def _load_contract(self):
        """Load TeoCoin contract with ABI."""
        try:
            # Try to load from blockchain/teocoin_abi.py first
            try:
                from blockchain.teocoin_abi import TEOCOIN_ABI
                contract_abi = TEOCOIN_ABI
            except ImportError:
                # Fallback to JSON file
                import json
                import os
                abi_path = os.path.join(settings.BASE_DIR, 'blockchain', 'abi', 'teoCoin2_ABI.json')
                with open(abi_path, 'r') as f:
                    contract_abi = json.load(f)
            
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=contract_abi
            )
            
        except Exception as e:
            logger.error(f"Failed to load contract: {e}")
            raise
    
    def mint_tokens(self, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Mint TeoCoin tokens to MetaMask wallet (for withdrawals).
        
        Args:
            to_address: Recipient wallet address
            amount: Amount of TEO to mint
            
        Returns:
            Transaction hash if successful, None if failed
        """
        if not self.admin_private_key:
            logger.error("Admin private key not configured")
            return None
        
        try:
            admin_account = self.w3.eth.account.from_key(self.admin_private_key)
            amount_wei = Web3.to_wei(amount, 'ether')
            checksum_to = Web3.to_checksum_address(to_address)
            
            # Get gas price
            gas_price = self._get_gas_price()
            
            # Build transaction (try both mint and mintTo functions)
            try:
                # Try mint function first
                transaction = self.contract.functions.mint(
                    checksum_to,
                    amount_wei
                ).build_transaction({
                    'from': admin_account.address,
                    'gas': 150000,
                    'gasPrice': gas_price,
                    'nonce': self.w3.eth.get_transaction_count(admin_account.address, 'pending'),
                })
            except Exception:
                # Fallback to mintTo function
                transaction = self.contract.functions.mintTo(
                    checksum_to,
                    amount_wei
                ).build_transaction({
                    'from': admin_account.address,
                    'gas': 150000,
                    'gasPrice': gas_price,
                    'nonce': self.w3.eth.get_transaction_count(admin_account.address, 'pending'),
                })
            
            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            logger.info(f"✅ Minted {amount} TEO to {to_address} - TX: {tx_hash.hex()}")
            return tx_hash.hex()
            
        except Exception as e:
            logger.error(f"❌ Failed to mint {amount} TEO to {to_address}: {e}")
            return None
    
    def get_balance(self, wallet_address: str) -> Decimal:
        """
        Get TeoCoin balance for a wallet address.
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Balance in TEO tokens
        """
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.contract.functions.balanceOf(checksum_address).call()
            balance_teo = Web3.from_wei(balance_wei, 'ether')
            return Decimal(str(balance_teo))
        except Exception as e:
            logger.error(f"Error getting balance for {wallet_address}: {e}")
            return Decimal('0')
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt for verification.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction receipt or None
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'status': receipt['status'],
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex(),
                'from': receipt['from'],
                'to': receipt['to'],
                'logs': receipt['logs']
            }
        except Exception as e:
            logger.error(f"Error getting receipt for {tx_hash}: {e}")
            return None
    
    def validate_address(self, address: str) -> bool:
        """
        Validate Ethereum address format.
        
        Args:
            address: Address to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            Web3.to_checksum_address(address)
            return True
        except ValueError:
            return False
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get basic token information.
        
        Returns:
            Token details dictionary
        """
        try:
            return {
                'name': self.contract.functions.name().call(),
                'symbol': self.contract.functions.symbol().call(),
                'decimals': self.contract.functions.decimals().call(),
                'contract_address': self.contract_address,
                'total_supply': str(Web3.from_wei(self.contract.functions.totalSupply().call(), 'ether'))
            }
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return {}
    
    def get_reward_pool_info(self) -> Dict[str, Any]:
        """
        Get reward pool info (legacy compatibility).
        Note: Reward pool operations now use DB-based system.
        """
        logger.warning("get_reward_pool_info called - reward operations now use DB system")
        return {
            'teo_balance': '0',
            'matic_balance': '0', 
            'status': 'db_based',
            'message': 'Reward operations now use DB-based system'
        }
    
    def _get_gas_price(self) -> int:
        """Get optimized gas price for the network."""
        try:
            gas_price = self.w3.eth.gas_price
            # Add 10% buffer
            gas_price = int(gas_price * 1.1)
            
            # Set reasonable limits
            min_gas_price = self.w3.to_wei('25', 'gwei')
            max_gas_price = self.w3.to_wei('50', 'gwei')
            
            if gas_price < min_gas_price:
                gas_price = min_gas_price
            elif gas_price > max_gas_price:
                gas_price = max_gas_price
                
            return gas_price
        except:
            return self.w3.to_wei('30', 'gwei')


# Global service instance
try:
    consolidated_teocoin_service = ConsolidatedTeoCoinService()
    logger.info("✅ ConsolidatedTeoCoinService initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize ConsolidatedTeoCoinService: {e}")
    # Create a fallback dummy service to prevent import errors
    class DummyTeoCoinService:
        def __init__(self):
            self.w3 = None
            
        def mint_tokens(self, *args, **kwargs):
            logger.error("TeoCoin service not available - mint_tokens failed")
            return None
            
        def get_balance(self, *args, **kwargs):
            logger.error("TeoCoin service not available - get_balance failed")
            return Decimal('0')
            
        def get_transaction_receipt(self, *args, **kwargs):
            logger.error("TeoCoin service not available - get_transaction_receipt failed")
            return None
            
        def validate_address(self, *args, **kwargs):
            logger.error("TeoCoin service not available - validate_address failed")
            return False
            
        def get_token_info(self, *args, **kwargs):
            logger.error("TeoCoin service not available - get_token_info failed")
            return {}
            
        def get_reward_pool_info(self, *args, **kwargs):
            logger.error("TeoCoin service not available - get_reward_pool_info failed")
            return {}
    
    consolidated_teocoin_service = DummyTeoCoinService()


# Legacy compatibility - this will be the main service
teocoin_service = consolidated_teocoin_service
