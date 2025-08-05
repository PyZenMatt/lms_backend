"""
TeoCoin Blockchain Service - Simplified for DB-based System

Provides essential blockchain functionality for:
- Token minting (withdrawals to MetaMask)
- Balance queries (burn deposit verification) 
- Transaction verification (burn deposits)
- Basic contract interaction

Note: Core TeoCoin operations (rewards, discounts, transfers) now use DB-based system.
"""
import time
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from web3 import Web3
from django.conf import settings
from .teocoin_abi import TEOCOIN_ABI

logger = logging.getLogger(__name__)


class TeoCoinService:
    """
    Simplified TeoCoin service for essential blockchain operations.
    
    Core operations (rewards, discounts) use DB-based system.
    Blockchain is used only for:
    - Minting tokens to MetaMask (withdrawals)
    - Verifying burn transactions from MetaMask
    - Balance queries for verification
    """
    
    def __init__(self):
        """Initialize the TeoCoin service with Web3 connection and contract setup."""
        # Web3 Configuration
        self.rpc_url = getattr(settings, 'POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
        self.contract_address = getattr(settings, 'TEOCOIN_CONTRACT_ADDRESS', None)
        self.admin_private_key = getattr(settings, 'ADMIN_PRIVATE_KEY', None)
        
        # Validate required configuration
        if not self.contract_address:
            raise ValueError("TEOCOIN_CONTRACT_ADDRESS must be set in environment variables")
        
        # Initialize Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Add middleware for PoA chains (Polygon Amoy)
        try:
            from web3.middleware import ExtraDataToPOAMiddleware
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        except ImportError:
            logger.warning("Could not load PoA middleware - using fallback")
        
        # Verify blockchain connection
        if not self.w3.is_connected():
            logger.error("Unable to connect to Polygon Amoy network")
            raise ConnectionError("Blockchain connection failed")
        
        # Initialize contract instance
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=TEOCOIN_ABI
        )
        
        logger.info(f"TeoCoinService initialized - Contract: {self.contract_address}")
    
    def get_balance(self, wallet_address: str) -> Decimal:
        """
        Get TeoCoin balance for a wallet address.
        
        Args:
            wallet_address: The wallet address to check balance for
            
        Returns:
            Decimal: Balance in TEO tokens (converted from wei)
        """
        start_time = time.time()
        try:
            checksum_address = Web3.to_checksum_address(wallet_address)
            balance_wei = self.contract.functions.balanceOf(checksum_address).call()
            balance_teo = Web3.from_wei(balance_wei, 'ether')
            execution_time = time.time() - start_time
            logger.info(f"Balance query for {wallet_address} completed in {execution_time:.3f}s")
            
            if execution_time > 1.0:
                logger.warning(f"⚠️ Slow balance query ({execution_time:.3f}s) for {wallet_address}")
                
            return Decimal(str(balance_teo))
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error retrieving balance for {wallet_address} after {execution_time:.3f}s: {e}")
            return Decimal('0')
    
    def mint_tokens(self, to_address: str, amount: Decimal) -> Optional[str]:
        """
        Mint TeoCoin tokens to a specific address (for withdrawals).
        
        Args:
            to_address: Recipient wallet address
            amount: Amount of TEO tokens to mint
            
        Returns:
            Optional[str]: Transaction hash if successful, None if failed
        """
        if not self.admin_private_key:
            logger.error("Admin private key not configured")
            return None
        
        max_retries = 3
        base_gas_price = self.get_optimized_gas_price()
        
        for attempt in range(max_retries):
            try:
                admin_account = self.w3.eth.account.from_key(self.admin_private_key)
                amount_wei = Web3.to_wei(amount, 'ether')
                checksum_to = Web3.to_checksum_address(to_address)
                
                # Dynamic gas price for each attempt
                gas_price = int(base_gas_price * (1.2 ** attempt))
                
                # Build transaction
                transaction = self.contract.functions.mint(
                    checksum_to,
                    amount_wei
                ).build_transaction({
                    'from': admin_account.address,
                    'gas': 150000,
                    'gasPrice': gas_price,
                    'nonce': self.w3.eth.get_transaction_count(admin_account.address, 'pending'),
                })
                
                # Sign and send transaction
                signed_txn = self.w3.eth.account.sign_transaction(transaction, self.admin_private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                
                logger.info(f"✅ Minted {amount} TEO to {to_address} - TX: {tx_hash.hex()}")
                return tx_hash.hex()
                
            except Exception as e:
                logger.error(f"Mint attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to mint {amount} TEO to {to_address} after {max_retries} attempts")
        return None
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get basic token information with caching.
        
        Returns:
            Dictionary with token name, symbol, decimals, etc.
        """
        try:
            info = {
                'name': self.contract.functions.name().call(),
                'symbol': self.contract.functions.symbol().call(),
                'decimals': self.contract.functions.decimals().call(),
                'contract_address': self.contract_address,
                'total_supply': str(Web3.from_wei(self.contract.functions.totalSupply().call(), 'ether'))
            }
            return info
        except Exception as e:
            logger.error(f"Error retrieving token info: {e}")
            return {}
    
    def get_transaction_receipt(self, tx_hash) -> Optional[Dict]:
        """
        Get transaction receipt for verification.
        
        Args:
            tx_hash: Transaction hash (string or bytes)
            
        Returns:
            Dictionary with transaction details
        """
        try:
            receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            return {
                'status': receipt['status'],
                'block_number': receipt['blockNumber'],
                'gas_used': receipt['gasUsed'],
                'transaction_hash': receipt['transactionHash'].hex(),
                'from': receipt['from'],
                'to': receipt['to']
            }
        except Exception as e:
            logger.error(f"Error retrieving receipt for {tx_hash}: {e}")
            return None
    
    def validate_address(self, address: str) -> bool:
        """
        Validate an Ethereum address.
        
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
    
    def get_optimized_gas_price(self) -> int:
        """
        Get optimized gas price for the network.
        
        Returns:
            int: Gas price in wei
        """
        try:
            gas_price = self.w3.eth.gas_price
            # Add 10% for reliability
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


# Global service instance for backward compatibility
teocoin_service = None

def get_teocoin_service():
    """Get or create the global TeoCoin service instance."""
    global teocoin_service
    if teocoin_service is None:
        teocoin_service = TeoCoinService()
    return teocoin_service

# Initialize service instance
try:
    teocoin_service = TeoCoinService()
except Exception as e:
    logger.error(f"Failed to initialize TeoCoin service: {e}")
    teocoin_service = None


# Legacy compatibility functions
def check_course_payment_prerequisites(student_address: str, course_price: Decimal):
    """
    Legacy compatibility function for course payment prerequisites.
    Note: Course payments now use DB-based system, this is kept for compatibility.
    """
    logger.warning("check_course_payment_prerequisites called - course payments now use DB system")
    return {
        'student_address': student_address,
        'course_price': str(course_price),
        'prerequisites_met': True,  # DB system handles this
        'message': 'Course payments now use DB-based system'
    }
