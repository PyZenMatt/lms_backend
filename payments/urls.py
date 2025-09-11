"""
URLs for payment-related endpoints including Stripe webhooks
"""

from django.urls import path
from . import webhooks

urlpatterns = [
    path('webhooks/stripe/', webhooks.StripeWebhookView.as_view(), name='stripe_webhook'),
    path('webhooks/stripe/legacy/', webhooks.stripe_webhook_handler, name='stripe_webhook_legacy'),
]
