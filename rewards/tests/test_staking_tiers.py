import pytest
from decimal import Decimal

from core.economics import PlatformEconomics as PE


@pytest.mark.parametrize("staked,expected_teacher_rate,expected_tier", [
    (0, Decimal("0.40"), "wood"),
    (125, Decimal("0.50"), "bronze"),
    (250, Decimal("0.55"), "silver"),
    (500, Decimal("0.65"), "gold"),
    (1000, Decimal("0.70"), "diamond"),
])
def test_get_teacher_tier_returns_expected_rates(staked, expected_teacher_rate, expected_tier):
    tier = PE.get_teacher_tier(staked)
    assert tier["tier_name"] == expected_tier
    # Compare as Decimal strings to avoid floating point surprises
    assert Decimal(str(tier["teacher_rate"])) == expected_teacher_rate
