import pytest
from decimal import Decimal

from django.contrib.auth import get_user_model

from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from rewards.models import BlockchainTransaction
from rewards.services.wallet_services import mint_teo, burn_teo
from rewards import constants

User = get_user_model()


@pytest.mark.django_db
def test_mint_decreases_db_and_writes_chain_once_idempotent(monkeypatch):
    user = User.objects.create_user(username="teacher1", email="teacher@example.com", password="pass", role="teacher")
    # seed DB balance
    bal = DBTeoCoinBalance.objects.create(user=user, available_balance=Decimal("100.00"))

    # mock adapter
    monkeypatch.setattr("blockchain.adapter.send_mint", lambda u, a: "0xFAKEHASH")

    res1 = mint_teo(user=user, amount=Decimal("10.00"), idem_key="idem-123")
    res2 = mint_teo(user=user, amount=Decimal("10.00"), idem_key="idem-123")

    assert res1["status"] == constants.STATUS_COMPLETED
    assert res1["tx_hash"] == "0xFAKEHASH"
    assert res2["status"] == constants.STATUS_COMPLETED
    # Only one chain tx exists
    assert BlockchainTransaction.objects.filter(transaction_type=constants.TX_MINT, related_object_id="idem-123").count() == 1
    # DB balance decreased once
    bal.refresh_from_db()
    assert bal.available_balance == Decimal("90.00")


@pytest.mark.django_db
def test_burn_increases_db_and_writes_chain_once_idempotent(monkeypatch):
    user = User.objects.create_user(username="user2", email="user2@example.com", password="pass", role="teacher")
    bal = DBTeoCoinBalance.objects.create(user=user, available_balance=Decimal("0.00"))

    monkeypatch.setattr("blockchain.adapter.send_burn", lambda u, a: "0xFAKEHASH")

    res1 = burn_teo(user=user, amount=Decimal("7.00"), idem_key="idem-777")
    res2 = burn_teo(user=user, amount=Decimal("7.00"), idem_key="idem-777")

    assert res1["status"] == constants.STATUS_COMPLETED
    assert res1["tx_hash"] == "0xFAKEHASH"
    # chain tx only once
    assert BlockchainTransaction.objects.filter(transaction_type=constants.TX_BURN, related_object_id="idem-777").count() == 1
    # DB credited once
    bal.refresh_from_db()
    assert bal.available_balance == Decimal("7.00")


@pytest.mark.django_db
def test_mint_rolls_back_on_chain_error(monkeypatch):
    user = User.objects.create_user(username="user3", email="user3@example.com", password="pass", role="teacher")
    bal = DBTeoCoinBalance.objects.create(user=user, available_balance=Decimal("50.00"))

    def raise_exc(u, a):
        raise RuntimeError("chain down")

    monkeypatch.setattr("blockchain.adapter.send_mint", raise_exc)

    with pytest.raises(RuntimeError):
        mint_teo(user=user, amount=Decimal("10.00"), idem_key="idem-fail")

    # Ensure DB balance rolled back
    bal.refresh_from_db()
    assert bal.available_balance == Decimal("50.00")
    # chain tx marked failed (exists)
    tx = BlockchainTransaction.objects.filter(transaction_type=constants.TX_MINT, related_object_id="idem-fail").first()
    if tx:
        assert tx.status == constants.STATUS_FAILED
