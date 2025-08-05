"""
Debug endpoint to test Stripe configuration
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import stripe
import logging

logger = logging.getLogger(__name__)

class DebugStripeView(APIView):
    """Debug endpoint to test Stripe configuration"""
    
    def get(self, request):
        try:
            # Check settings
            stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', 'NOT_SET')
            stripe_publishable = getattr(settings, 'STRIPE_PUBLISHABLE_KEY', 'NOT_SET')
            
            # Test Stripe API
            stripe.api_key = stripe_secret
            
            # Create a test payment intent
            test_intent = stripe.PaymentIntent.create(
                amount=1000,  # $10.00
                currency='eur',
                metadata={'test': 'debug_endpoint'}
            )
            
            return Response({
                'success': True,
                'stripe_secret_key_prefix': stripe_secret[:15] if stripe_secret else 'NOT_SET',
                'stripe_publishable_key_prefix': stripe_publishable[:15] if stripe_publishable else 'NOT_SET',
                'test_payment_intent_id': test_intent.id,
                'stripe_api_key_set': stripe.api_key[:15] if stripe.api_key else 'NOT_SET'
            })
            
        except Exception as e:
            logger.error(f"Stripe debug error: {e}")
            return Response({
                'success': False,
                'error': str(e),
                'stripe_secret_key_prefix': getattr(settings, 'STRIPE_SECRET_KEY', 'NOT_SET')[:15],
                'stripe_api_key_set': getattr(stripe, 'api_key', 'NOT_SET')[:15] if hasattr(stripe, 'api_key') else 'NO_ATTR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
