"""
Base Service Class and Common Utilities

Provides base functionality for all service classes in the platform.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from django.db import transaction
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Abstract base class for all services.
    
    Provides common functionality like logging, error handling,
    and transaction management.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with service context"""
        self.logger.info(f"[{self.__class__.__name__}] {message}", extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with service context"""
        self.logger.error(f"[{self.__class__.__name__}] {message}", extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with service context"""
        self.logger.debug(f"[{self.__class__.__name__}] {message}", extra=kwargs)


class TransactionalService(BaseService):
    """
    Service class with database transaction support.
    
    Use for services that need atomic database operations.
    """
    
    def execute_in_transaction(self, operation_func, *args, **kwargs):
        """
        Execute operation in database transaction with rollback on error.
        
        Args:
            operation_func: Function to execute in transaction
            *args, **kwargs: Arguments for the function
        
        Returns:
            Result of operation_func
        
        Raises:
            Exception from operation_func if it fails
        """
        try:
            with transaction.atomic():
                self.log_debug(f"Starting transaction for {operation_func.__name__}")
                result = operation_func(*args, **kwargs)
                self.log_debug(f"Transaction completed successfully for {operation_func.__name__}")
                return result
        except Exception as e:
            self.log_error(f"Transaction failed for {operation_func.__name__}: {str(e)}")
            raise
