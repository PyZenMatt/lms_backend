import json
from decimal import Decimal

from django.urls import reverse
from rest_framework.test import APIClient


def test_teocoin_compat_tiers_match_canonical(db, django_user_model):
    # Create a teacher user and authenticate
    user = django_user_model.objects.create_user(username="tcompat", password="pass", role="teacher")
    client = APIClient()
    client.force_authenticate(user=user)

    compat_url = reverse("rewards:staking_overview") if False else "/api/v1/rewards/staking/overview/"
    tiers_url = "/api/v1/services/staking/tiers/"

    # Hit canonical tiers
    r_canonical = client.get(tiers_url)
    assert r_canonical.status_code == 200
    canonical = r_canonical.json()["tiers"]

    # Hit compat tiers
    r_compat = client.get("/api/v1/rewards/staking/tiers/")
    assert r_compat.status_code == 200
    compat = r_compat.json()["tiers"]

    # Compare keys and values for each tier
    assert set(k.lower() for k in compat.keys()) == set(k.lower() for k in canonical.keys())
    for name, cval in canonical.items():
        compat_val = compat.get(name.title())
        assert compat_val is not None
        # compare min_stake and commission/teacher earnings
        assert float(cval["min_stake"]) == float(compat_val["min_stake"])
        assert float(cval["commission_rate"]) == float(compat_val["commission_rate"])
        assert float(cval["teacher_earnings"]) == float(compat_val["teacher_earnings"])
