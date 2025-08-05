"""
Health Check System for TeoArt School Platform.

This module provides comprehensive health monitoring for the platform,
checking the status of critical services including database, cache,
and background task processing.

Classes:
    HealthCheckView: Main health check endpoint for monitoring systems
"""
from django.http import JsonResponse
from django.views import View
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger('health_check')

class HealthCheckView(View):
    """
    Comprehensive health check endpoint for monitoring and load balancers.
    
    This view performs health checks on all critical platform services
    and returns a standardized health status response.
    
    URL: /api/v1/health/
    Method: GET
    
    Response Format:
        {
            "status": "healthy" | "unhealthy",
            "checks": {
                "database": "healthy" | "unhealthy: <error>",
                "cache": "healthy" | "unhealthy: <error>",
                "celery": "healthy" | "unhealthy: <error>" (optional)
            }
        }
    
    HTTP Status Codes:
        - 200: All services are healthy
        - 503: One or more services are unhealthy
    """
    
    def get(self, request):
        """
        Perform comprehensive health check of all platform services.
        
        Args:
            request: HTTP request object
            
        Returns:
            JsonResponse: Health status of all services
        """
        health_status = {
            'status': 'healthy',
            'checks': {}
        }
        
        # Database connectivity check
        health_status['checks']['database'] = self._check_database()
        if 'unhealthy' in health_status['checks']['database']:
            health_status['status'] = 'unhealthy'
        
        # Redis cache check
        health_status['checks']['cache'] = self._check_cache()
        if 'unhealthy' in health_status['checks']['cache']:
            health_status['status'] = 'unhealthy'
        
        # Celery background task check (optional)
        celery_status = self._check_celery()
        if celery_status:
            health_status['checks']['celery'] = celery_status
        
        # Return appropriate HTTP status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return JsonResponse(health_status, status=status_code)
    
    def _check_database(self):
        """
        Check database connectivity and basic operations.
        
        Returns:
            str: 'healthy' if database is working, error message otherwise
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return 'healthy'
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return f'unhealthy: {str(e)}'
    
    def _check_cache(self):
        """
        Check Redis cache connectivity and basic operations.
        
        Returns:
            str: 'healthy' if cache is working, error message otherwise
        """
        try:
            # Test cache write and read operations
            test_key = 'health_check'
            test_value = 'ok'
            
            cache.set(test_key, test_value, timeout=30)
            cache_value = cache.get(test_key)
            
            if cache_value == test_value:
                return 'healthy'
            else:
                return 'unhealthy: cache value mismatch'
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return f'unhealthy: {str(e)}'
    
    def _check_celery(self):
        """
        Check Celery background task system status.
        
        Returns:
            str: Celery status or None if check fails
        """
        try:
            from celery import current_app
            
            # Try to get worker stats with timeout
            inspect = current_app.control.inspect()
            if hasattr(inspect, 'stats'):
                stats = inspect.stats()
                if stats:
                    return 'healthy'
                else:
                    return 'no workers available'
            else:
                return 'unhealthy: inspect object invalid'
        except ImportError:
            # Celery not installed or configured
            return None
        except Exception as e:
            logger.warning(f"Celery health check failed: {e}")
            # Don't return celery status for non-critical failures
            return None
