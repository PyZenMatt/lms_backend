"""
Standardized API response utilities and error handling for TeoArt School Platform.

This module provides a consistent API response format across the entire platform,
ensuring standardized error handling, success responses, and exception management.

Classes:
    APIResponse: Utility class for creating standardized API responses
    
Functions:
    custom_exception_handler: Custom DRF exception handler for consistent error formatting
"""
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import exception_handler
import logging

logger = logging.getLogger('api_responses')


class APIResponse:
    """
    Standardized API response format utility.
    
    This class provides static methods for creating consistent API responses
    across the platform, ensuring uniform structure for success and error cases.
    
    Response Format:
        {
            "success": bool,
            "message": str,
            "status_code": int,
            "data": any (optional),
            "errors": dict (optional for errors)
        }
    """
    
    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """
        Create a standardized success response.
        
        Args:
            data: The response data (any JSON-serializable type)
            message: Success message (default: "Success")
            status_code: HTTP status code (default: 200)
            
        Returns:
            Response: DRF Response object with standardized success format
        """
        response_data = {
            "success": True,
            "message": message,
            "status_code": status_code
        }
        
        if data is not None:
            response_data["data"] = data
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def error(message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Create a standardized error response.
        
        Args:
            message: Error message describing what went wrong
            errors: Detailed error information (dict or list)
            status_code: HTTP status code (default: 400)
            
        Returns:
            Response: DRF Response object with standardized error format
        """
        response_data = {
            "success": False,
            "message": message,
            "status_code": status_code
        }
        
        if errors is not None:
            response_data["errors"] = errors
            
        return Response(response_data, status=status_code)
    
    @staticmethod
    def validation_error(errors, message="Validation failed"):
        """
        Create a standardized validation error response.
        
        Args:
            errors: Validation errors from serializers or forms
            message: Validation error message (default: "Validation failed")
            
        Returns:
            Response: DRF Response object with 422 status code
        """
        return APIResponse.error(
            message=message,
            errors=errors,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    def not_found(message="Resource not found"):
        """
        Create a standardized not found response.
        
        Args:
            message: Not found message (default: "Resource not found")
            
        Returns:
            Response: DRF Response object with 404 status code
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def unauthorized(message="Authentication required"):
        """
        Create a standardized unauthorized response.
        
        Args:
            message: Unauthorized message (default: "Authentication required")
            
        Returns:
            Response: DRF Response object with 401 status code
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden(message="Permission denied"):
        """
        Create a standardized forbidden response.
        
        Args:
            message: Forbidden message (default: "Permission denied")
            
        Returns:
            Response: DRF Response object with 403 status code
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def server_error(message="Internal server error"):
        """
        Create a standardized server error response.
        
        Args:
            message: Server error message (default: "Internal server error")
            
        Returns:
            Response: DRF Response object with 500 status code
        """
        return APIResponse.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def custom_exception_handler(exc, context):
    """
    Custom exception handler for standardized error responses.
    
    This function provides consistent error formatting across the entire API,
    replacing Django REST Framework's default exception handler.
    
    Args:
        exc: The exception that was raised
        context: Context information about the exception
        
    Returns:
        Response: Standardized error response or None if not handled
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Log the exception with context
        request = context.get('request')
        view = context.get('view')
        
        logger.error(
            f"API Exception in {view.__class__.__name__ if view else 'Unknown'}: {exc}",
            extra={
                'path': request.path if request else 'Unknown',
                'method': request.method if request else 'Unknown',
                'user': request.user.username if request and hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
            },
            exc_info=True
        )
        
        # Standardize the error response format
        custom_response_data = {
            'success': False,
            'message': 'An error occurred',
            'status_code': response.status_code,
            'errors': response.data
        }
        
        # Customize message based on status code
        status_messages = {
            status.HTTP_400_BAD_REQUEST: 'Bad request',
            status.HTTP_401_UNAUTHORIZED: 'Authentication required',
            status.HTTP_403_FORBIDDEN: 'Permission denied',
            status.HTTP_404_NOT_FOUND: 'Resource not found',
            status.HTTP_422_UNPROCESSABLE_ENTITY: 'Validation failed',
            status.HTTP_429_TOO_MANY_REQUESTS: 'Too many requests',
        }
        
        if response.status_code in status_messages:
            custom_response_data['message'] = status_messages[response.status_code]
        elif response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            custom_response_data['message'] = 'Internal server error'
        
        response.data = custom_response_data
    
    return response


class StandardizedAPIView:
    """
    Mixin class for views to use standardized API responses.
    
    This mixin provides convenience methods for creating consistent API responses
    across all views in the platform. Inherit from this class in your API views
    to access standardized response methods.
    
    Example:
        class MyAPIView(StandardizedAPIView, APIView):
            def get(self, request):
                data = {"message": "Hello World"}
                return self.handle_success(data, "Data retrieved successfully")
    """
    
    def handle_success(self, data=None, message="Success", status_code=status.HTTP_200_OK):
        """
        Handle successful operations with standardized response.
        
        Args:
            data: The response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Response: Standardized success response
        """
        return APIResponse.success(data, message, status_code)
    
    def handle_error(self, message="An error occurred", errors=None, status_code=status.HTTP_400_BAD_REQUEST):
        """
        Handle error cases with standardized response.
        
        Args:
            message: Error message
            errors: Detailed error information
            status_code: HTTP status code
            
        Returns:
            Response: Standardized error response
        """
        return APIResponse.error(message, errors, status_code)
    
    def handle_validation_error(self, serializer):
        """
        Handle serializer validation errors.
        
        Args:
            serializer: DRF serializer with validation errors
            
        Returns:
            Response: Standardized validation error response
        """
        return APIResponse.validation_error(serializer.errors)
    
    def handle_not_found(self, resource="Resource"):
        """
        Handle not found cases.
        
        Args:
            resource: Name of the resource that was not found
            
        Returns:
            Response: Standardized not found response
        """
        return APIResponse.not_found(f"{resource} not found")
    
    def handle_permission_denied(self, message=None):
        """
        Handle permission denied cases.
        
        Args:
            message: Custom permission denied message
            
        Returns:
            Response: Standardized permission denied response
        """
        if message is None:
            message = "Permission denied"
        return APIResponse.forbidden(message)
        
    def handle_server_error(self, exception=None):
        """
        Handle server errors.
        
        Args:
            exception: The exception that caused the server error
            
        Returns:
            Response: Standardized server error response
        """
        if exception:
            logger.error(f"Server error: {exception}", exc_info=True)
        return APIResponse.server_error()


class PaginatedResponse:
    """
    Utility class for creating standardized paginated API responses.
    
    This class provides methods for formatting paginated data in a consistent
    way across the platform, including pagination metadata.
    """
    
    @staticmethod
    def create(data, page_info, message="Data retrieved successfully"):
        """
        Create a standardized paginated response.
        
        Args:
            data: The paginated data results
            page_info: Pagination information dictionary containing:
                - count: Total number of items
                - next: URL for next page (if any)
                - previous: URL for previous page (if any)
                - page_size: Number of items per page
                - current_page: Current page number
                - total_pages: Total number of pages
            message: Success message
            
        Returns:
            Response: Standardized paginated response
            
        Example:
            page_info = {
                'count': 100,
                'next': 'http://api.example.com/data/?page=3',
                'previous': 'http://api.example.com/data/?page=1',
                'page_size': 20,
                'current_page': 2,
                'total_pages': 5
            }
            return PaginatedResponse.create(data, page_info)
        """
        response_data = {
            "results": data,
            "pagination": {
                "count": page_info.get('count', 0),
                "next": page_info.get('next'),
                "previous": page_info.get('previous'),
                "page_size": page_info.get('page_size', 20),
                "current_page": page_info.get('current_page', 1),
                "total_pages": page_info.get('total_pages', 1)
            }
        }
        
        return APIResponse.success(
            data=response_data,
            message=message
        )
