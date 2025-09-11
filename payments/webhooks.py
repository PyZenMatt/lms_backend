"""
Stripe Webhook Handlers for TEO Discount Hold Capture

This module handles Stripe webhooks to capture TEO holds when payment succeeds
and release holds when payment fails, implementing the complete flow for
"ISSUE A - Capture dell'hold TEO a pagamento riuscito"
"""

import logging
import stripe
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from rewards.models import PaymentDiscountSnapshot
from services.wallet_hold_service import WalletHoldService

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Handle Stripe webhooks for payment events
    
    Key events:
    - checkout.session.completed: Find application via stripe_checkout_session_id, capture hold
    - payment_intent.succeeded: Alternative capture trigger via stripe_payment_intent_id
    - payment_intent.payment_failed: Release hold on payment failure
    """
    
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        if not sig_header:
            logger.warning("Missing Stripe signature header")
            return HttpResponseBadRequest("Missing signature")
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            logger.error("Invalid payload")
            return HttpResponseBadRequest("Invalid payload")
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid signature")
            return HttpResponseBadRequest("Invalid signature")
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            return self._handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'payment_intent.succeeded':
            return self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            return self._handle_payment_failed(event['data']['object'])
        else:
            logger.info(f"Unhandled event type: {event['type']}")
            return HttpResponse(status=200)
    
    def _handle_checkout_completed(self, session):
        """
        Handle checkout.session.completed webhook
        
        Find PaymentDiscountSnapshot by stripe_checkout_session_id and capture the hold
        """
        checkout_session_id = session.get('id')
        payment_intent_id = session.get('payment_intent')
        
        logger.info(f"🔄 Processing checkout.session.completed: {checkout_session_id}")
        
        if not checkout_session_id:
            logger.error("Missing checkout session ID")
            return HttpResponseBadRequest("Missing checkout session ID")
        
        try:
            with transaction.atomic():
                # Find discount application by Stripe checkout session ID
                snapshot = PaymentDiscountSnapshot.objects.filter(
                    stripe_checkout_session_id=checkout_session_id,
                    status='applied'
                ).first()
                
                if not snapshot:
                    logger.warning(f"No discount application found for checkout session: {checkout_session_id}")
                    return HttpResponse(status=200)  # Not an error, just no discount applied
                
                # Update stripe_payment_intent_id if available
                if payment_intent_id and not snapshot.stripe_payment_intent_id:
                    snapshot.stripe_payment_intent_id = payment_intent_id
                    snapshot.save(update_fields=['stripe_payment_intent_id'])
                
                # Capture the TEO hold
                success = self._capture_teo_hold(snapshot)
                
                if success:
                    logger.info(f"✅ Successfully captured TEO hold for checkout session: {checkout_session_id}")
                    return HttpResponse(status=200)
                else:
                    logger.error(f"❌ Failed to capture TEO hold for checkout session: {checkout_session_id}")
                    return HttpResponse(status=500)
        
        except Exception as e:
            logger.error(f"Error processing checkout.session.completed: {e}", exc_info=True)
            return HttpResponse(status=500)
    
    def _handle_payment_succeeded(self, payment_intent):
        """
        Handle payment_intent.succeeded webhook
        
        Alternative capture method using payment_intent_id
        """
        payment_intent_id = payment_intent.get('id')
        
        logger.info(f"🔄 Processing payment_intent.succeeded: {payment_intent_id}")
        
        if not payment_intent_id:
            logger.error("Missing payment intent ID")
            return HttpResponseBadRequest("Missing payment intent ID")
        
        try:
            with transaction.atomic():
                # Find discount application by Stripe payment intent ID
                snapshot = PaymentDiscountSnapshot.objects.filter(
                    stripe_payment_intent_id=payment_intent_id,
                    status='applied'
                ).first()
                
                if not snapshot:
                    logger.warning(f"No discount application found for payment intent: {payment_intent_id}")
                    return HttpResponse(status=200)  # Not an error, just no discount applied
                
                # Capture the TEO hold
                success = self._capture_teo_hold(snapshot)
                
                if success:
                    logger.info(f"✅ Successfully captured TEO hold for payment intent: {payment_intent_id}")
                    return HttpResponse(status=200)
                else:
                    logger.error(f"❌ Failed to capture TEO hold for payment intent: {payment_intent_id}")
                    return HttpResponse(status=500)
        
        except Exception as e:
            logger.error(f"Error processing payment_intent.succeeded: {e}", exc_info=True)
            return HttpResponse(status=500)
    
    def _handle_payment_failed(self, payment_intent):
        """
        Handle payment_intent.payment_failed webhook
        
        Release TEO hold when payment fails
        """
        payment_intent_id = payment_intent.get('id')
        
        logger.info(f"🔄 Processing payment_intent.payment_failed: {payment_intent_id}")
        
        if not payment_intent_id:
            logger.error("Missing payment intent ID")
            return HttpResponseBadRequest("Missing payment intent ID")
        
        try:
            with transaction.atomic():
                # Find discount application by Stripe payment intent ID
                snapshot = PaymentDiscountSnapshot.objects.filter(
                    stripe_payment_intent_id=payment_intent_id,
                    status='applied'
                ).first()
                
                if not snapshot:
                    logger.warning(f"No discount application found for failed payment: {payment_intent_id}")
                    return HttpResponse(status=200)  # Not an error, just no discount applied
                
                # Release the TEO hold
                success = self._release_teo_hold(snapshot)
                
                if success:
                    logger.info(f"✅ Successfully released TEO hold for failed payment: {payment_intent_id}")
                    return HttpResponse(status=200)
                else:
                    logger.error(f"❌ Failed to release TEO hold for failed payment: {payment_intent_id}")
                    return HttpResponse(status=500)
        
        except Exception as e:
            logger.error(f"Error processing payment_intent.payment_failed: {e}", exc_info=True)
            return HttpResponse(status=500)
    
    def _capture_teo_hold(self, snapshot):
        """
        Capture TEO hold and update snapshot status
        
        Args:
            snapshot: PaymentDiscountSnapshot with wallet_hold_id
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not snapshot.wallet_hold_id:
            logger.error(f"No wallet hold ID for snapshot {snapshot.id}")
            return False
        
        try:
            wallet_hold_service = WalletHoldService()
            
            # Capture the hold (deduct TEO tokens)
            success = wallet_hold_service.capture_hold(
                hold_id=snapshot.wallet_hold_id,
                description=f"TEO discount captured for payment confirmation - snapshot {snapshot.id}"
            )
            
            if success:
                # Update snapshot status to confirmed
                snapshot.status = 'confirmed'
                snapshot.confirmed_at = timezone.now()
                snapshot.save(update_fields=['status', 'confirmed_at'])
                
                logger.info(f"🎉 TEO hold {snapshot.wallet_hold_id} captured successfully for snapshot {snapshot.id}")
                return True
            else:
                logger.error(f"Failed to capture TEO hold {snapshot.wallet_hold_id} for snapshot {snapshot.id}")
                return False
        
        except Exception as e:
            logger.error(f"Error capturing TEO hold {snapshot.wallet_hold_id}: {e}", exc_info=True)
            return False
    
    def _release_teo_hold(self, snapshot):
        """
        Release TEO hold and update snapshot status
        
        Args:
            snapshot: PaymentDiscountSnapshot with wallet_hold_id
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not snapshot.wallet_hold_id:
            logger.error(f"No wallet hold ID for snapshot {snapshot.id}")
            return False
        
        try:
            wallet_hold_service = WalletHoldService()
            
            # Release the hold (return TEO tokens to available balance)
            success = wallet_hold_service.release_hold(
                hold_id=snapshot.wallet_hold_id,
                description=f"TEO discount released due to payment failure - snapshot {snapshot.id}"
            )
            
            if success:
                # Update snapshot status to failed
                snapshot.status = 'failed'
                snapshot.save(update_fields=['status'])
                
                logger.info(f"🔄 TEO hold {snapshot.wallet_hold_id} released for failed payment - snapshot {snapshot.id}")
                return True
            else:
                logger.error(f"Failed to release TEO hold {snapshot.wallet_hold_id} for snapshot {snapshot.id}")
                return False
        
        except Exception as e:
            logger.error(f"Error releasing TEO hold {snapshot.wallet_hold_id}: {e}", exc_info=True)
            return False


# Legacy function-based view for backward compatibility
@csrf_exempt
@require_POST
def stripe_webhook_handler(request):
    """Legacy webhook handler - redirects to class-based view"""
    view = StripeWebhookView()
    return view.post(request)
