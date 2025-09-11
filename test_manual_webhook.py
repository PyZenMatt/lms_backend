#!/usr/bin/env python
"""
Simula un webhook Stripe con i metadata corretti per testare il settle
"""
import requests
import json

# Simula un webhook payload con i metadata che ora dovrebbero essere presenti
webhook_payload = {
    "id": "evt_test_webhook",
    "object": "event",
    "api_version": "2023-10-16",
    "created": 1234567890,
    "data": {
        "object": {
            "id": "cs_test_checkout_session",
            "object": "checkout.session",
            "payment_intent": "pi_test_payment_intent",
            "payment_status": "paid",
            "status": "complete",
            "metadata": {
                # QUESTI sono i metadata che Issue-04A ora aggiunge!
                "discount_snapshot_id": "143",
                "hold_id": "143",
                "order_id": "checkout_session_1757587313075_gu9xea7gtsk",
                "course_id": "1",
                "user_id": "1",
                "use_teocoin_discount": "True"
            }
        }
    },
    "livemode": False,
    "pending_webhooks": 1,
    "request": {
        "id": "req_test",
        "idempotency_key": None
    },
    "type": "checkout.session.completed"
}

def test_webhook():
    """Invia il webhook al nostro endpoint"""
    
    url = "http://127.0.0.1:8000/api/v1/payments/webhooks/stripe/"
    headers = {
        "Content-Type": "application/json",
        "Stripe-Signature": "t=1234567890,v1=test_signature"  # Fake signature
    }
    
    print("🧪 TESTING WEBHOOK WITH METADATA")
    print("=" * 40)
    print()
    print("📨 Payload:")
    print(json.dumps(webhook_payload, indent=2))
    print()
    
    try:
        response = requests.post(url, json=webhook_payload, headers=headers)
        print(f"📡 Response Status: {response.status_code}")
        print(f"📝 Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook processed successfully!")
            return True
        else:
            print(f"❌ Webhook failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Django server. Is it running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_webhook()
