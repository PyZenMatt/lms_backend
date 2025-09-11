import json
import pytest
from django.urls import reverse
from django.test import Client
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

User = get_user_model()

client = Client()


def make_checkout_event(session_id, event_id="evt_test"):
    return {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {"object": {"id": session_id, "metadata": {}}}
    }


def test_webhook_settle_happy_path(db):
    # Skeleton test: create a pending snapshot and POST a mocked checkout event
    # TODO: adapt model fields if names differ in your codebase
    from rewards.models import PaymentDiscountSnapshot
    user = User.objects.create(username="webhook_user")
    snap = PaymentDiscountSnapshot.objects.create(user=user, order_id="sess_123", status="pending", amount=100)

    # Use legacy handler (no signature verification) for tests
    payload = make_checkout_event("sess_123", event_id="evt_1")
    url = '/api/v1/payments/webhooks/stripe/legacy/'

    resp = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 200

    snap.refresh_from_db()
    assert snap.status == 'confirmed'
    # ledger check TODO: assert ledger entries reflect settlement


def test_webhook_replay_idempotent(db):
    from rewards.models import PaymentDiscountSnapshot
    user = User.objects.create(username="webhook_user2")
    snap = PaymentDiscountSnapshot.objects.create(user=user, order_id="sess_456", status="pending", amount=50)

    payload = make_checkout_event("sess_456", event_id="evt_99")
    url = '/api/v1/payments/webhooks/stripe/legacy/'

    resp1 = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert resp1.status_code == 200
    # second replay
    resp2 = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert resp2.status_code == 200

    # assert only one settlement applied (ledger/assertions TODO)


def test_webhook_unknown_order_noop(db):
    payload = make_checkout_event("sess_not_exists", event_id="evt_unknown")
    url = '/api/v1/payments/webhooks/stripe/legacy/'
    resp = client.post(url, data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 200

