"""
Custom Exceptions for TeoArt School Platform Services

These exceptions provide specific error handling for business logic
operations in the service layer.
"""


class TeoArtServiceException(Exception):
    """
    Base exception for all service-related errors.
    
    Attributes:
        message: Human-readable error message
        code: Error code for frontend handling
        status_code: HTTP status code for API responses
    """
    
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        self.message = message
        self.code = code or self.__class__.__name__
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundError(TeoArtServiceException):
    """Raised when a user is not found"""
    
    def __init__(self, user_id: int = None, email: str = None):
        if user_id:
            message = f"User with ID {user_id} not found"
        elif email:
            message = f"User with email {email} not found"
        else:
            message = "User not found"
        
        super().__init__(message, "USER_NOT_FOUND", 404)


class UserAlreadyExistsError(TeoArtServiceException):
    """Raised when trying to create a user that already exists"""
    
    def __init__(self, email: str):
        message = f"User with email {email} already exists"
        super().__init__(message, "USER_ALREADY_EXISTS", 400)


class InvalidUserRoleError(TeoArtServiceException):
    """Raised when an invalid user role is provided"""
    
    def __init__(self, role: str):
        message = f"Invalid user role: {role}"
        super().__init__(message, "INVALID_USER_ROLE", 400)


class UserNotApprovedError(TeoArtServiceException):
    """Raised when a user is not approved for an operation"""
    
    def __init__(self, user_id: int):
        message = f"User {user_id} is not approved for this operation"
        super().__init__(message, "USER_NOT_APPROVED", 403)


class CourseNotFoundError(TeoArtServiceException):
    """Raised when a course is not found"""
    
    def __init__(self, course_id: int):
        message = f"Course with ID {course_id} not found"
        super().__init__(message, "COURSE_NOT_FOUND", 404)


class InsufficientTeoCoinsError(TeoArtServiceException):
    """Raised when user doesn't have enough TeoCoins"""
    
    def __init__(self, required: float, available: float):
        message = f"Insufficient TeoCoins. Required: {required}, Available: {available}"
        super().__init__(message, "INSUFFICIENT_TEOCOINS", 400)


class BlockchainTransactionError(TeoArtServiceException):
    """Raised when a blockchain transaction fails"""
    
    def __init__(self, message: str, code: str = None, status_code: int = 500):
        super().__init__(message, code or "BLOCKCHAIN_TRANSACTION_ERROR", status_code)


class EmailVerificationError(TeoArtServiceException):
    """Raised when email verification fails"""
    
    def __init__(self, email: str):
        message = f"Email verification failed for {email}"
        super().__init__(message, "EMAIL_VERIFICATION_ERROR", 400)


class WalletNotFoundError(TeoArtServiceException):
    """Raised when a wallet is not found for a user"""
    
    def __init__(self, user_id: int):
        message = f"Wallet not found for user {user_id}"
        super().__init__(message, "WALLET_NOT_FOUND", 404)


class InvalidWalletAddressError(TeoArtServiceException):
    """Raised when an invalid wallet address is provided"""
    
    def __init__(self, address: str):
        message = f"Invalid wallet address: {address}"
        super().__init__(message, "INVALID_WALLET_ADDRESS", 400)


class TokenTransferError(TeoArtServiceException):
    """Raised when a token transfer fails"""
    
    def __init__(self, reason: str = None):
        message = "Token transfer failed"
        if reason:
            message += f": {reason}"
        super().__init__(message, "TOKEN_TRANSFER_ERROR", 500)


class MintingError(TeoArtServiceException):
    """Raised when token minting fails"""
    
    def __init__(self, amount: float, reason: str = None):
        message = f"Failed to mint {amount} tokens"
        if reason:
            message += f": {reason}"
        super().__init__(message, "MINTING_ERROR", 500)


class InvalidAmountError(TeoArtServiceException):
    """Raised when an invalid amount is provided for blockchain operations"""
    
    def __init__(self, amount: float):
        message = f"Invalid amount: {amount}. Amount must be positive"
        super().__init__(message, "INVALID_AMOUNT", 400)


class PaymentError(TeoArtServiceException):
    """Raised when a payment operation fails"""
    
    def __init__(self, message: str, code: str = None, status_code: int = 400):
        super().__init__(message, code or "PAYMENT_ERROR", status_code)


class TransactionAlreadyProcessedError(TeoArtServiceException):
    """Raised when trying to process a transaction that was already processed"""
    
    def __init__(self, transaction_hash: str):
        message = f"Transaction {transaction_hash} has already been processed"
        super().__init__(message, "TRANSACTION_ALREADY_PROCESSED", 400)


class TransactionVerificationError(TeoArtServiceException):
    """Raised when blockchain transaction verification fails"""
    
    def __init__(self, transaction_hash: str, reason: str = None):
        message = f"Transaction verification failed for {transaction_hash}"
        if reason:
            message += f": {reason}"
        super().__init__(message, "TRANSACTION_VERIFICATION_FAILED", 400)
