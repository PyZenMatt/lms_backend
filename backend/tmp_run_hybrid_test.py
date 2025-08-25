from services.payment_service import payment_service
from users.models import User
from services.db_teocoin_service import db_teocoin_service
from rewards.models import BlockchainTransaction
import stripe

# Monkeypatch Stripe retrieve to simulate succeeded payment
class _R:
    status = 'succeeded'
    # amount in cents
    amount = 10300

stripe.PaymentIntent.retrieve = lambda pid: _R()

user = User.objects.get(pk=7)
print('BAL_BEFORE:', db_teocoin_service.get_available_balance(user))
res = payment_service.process_successful_hybrid_payment('pi_3RzzAh1ION4Zwx6o0UsUvFaT', 2, 7)
print('PROCESS_RESULT:', res)
# show most recent tx for course 2
tx = BlockchainTransaction.objects.filter(user=user, related_object_id='2').order_by('-created_at').first()
print('TX_AFTER:', {'id': tx.id, 'status': tx.status, 'amount': str(tx.amount), 'notes': tx.notes})
print('BAL_AFTER:', db_teocoin_service.get_available_balance(user))
