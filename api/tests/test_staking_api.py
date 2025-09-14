from decimal import Decimal

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from core.economics import PlatformEconomics as PE


def make_teacher(client):
    User = get_user_model()
    user = User.objects.create_user(username="teacher_api", password="pass", role="teacher")
    client.force_authenticate(user=user)
    return user


def test_get_staking_tiers_matches_sot(db):
    client = APIClient()
    make_teacher(client)

    r = client.get("/api/v1/services/staking/tiers/")
    assert r.status_code == 200
    tiers = r.json()["tiers"]

    # Validate canonical ordering and values
    canonical = PE.STAKING_TIERS
    for name, cfg in canonical.items():
        key = name.title()
        assert key in tiers
        t = tiers[key]
        assert float(t["min_stake"]) == float(cfg["teo_required"])
        assert float(t["commission_rate"]) == float(cfg["commission_rate"] * 100)
        assert float(t["teacher_earnings"]) == float(cfg["teacher_rate"] * 100)


def test_get_staking_info_various_stakes(db):
    client = APIClient()
    user = make_teacher(client)

    # Create balance record for user
    from blockchain.models import DBTeoCoinBalance

    for stake in [0, 125, 250, 500, 1000]:
        DBTeoCoinBalance.objects.update_or_create(user=user, defaults={"available_balance": Decimal("0"), "staked_balance": Decimal(str(stake))})
        r = client.get("/api/v1/services/staking/info/")
        assert r.status_code == 200
        payload = r.json()
        expected = PE.get_teacher_tier(Decimal(str(stake)))
        assert payload["tier"] == expected["tier_name"].title()
        # commission percent
        assert float(payload["commission_rate"]) == float(Decimal(str(expected["commission_rate"])) * 100)


def test_calculate_commission_endpoint(db):
    client = APIClient()
    make_teacher(client)

    for stake in [0, 125, 250, 500, 1000]:
        r = client.get(f"/api/v1/services/staking/calculator/?current_stake={stake}")
        assert r.status_code == 200
        payload = r.json()
        expected = PE.get_teacher_tier(Decimal(str(stake)))
        assert payload["current_tier"] == expected["tier_name"].title()
        assert float(payload["current_commission_rate"]) == float(Decimal(str(expected["commission_rate"])) * 100)
