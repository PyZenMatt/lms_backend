from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, getcontext
from django.conf import settings
from typing import Dict, Optional

# Set a high precision for intermediate calculations
getcontext().prec = 28

EUR_QUANT = Decimal("0.01")
TEO_QUANT = Decimal("0.00000001")


def clamp_decimal(value: Decimal, min_v: Decimal, max_v: Decimal) -> Decimal:
    if value < min_v:
        return min_v
    if value > max_v:
        return max_v
    return value


def quantize_eur(d: Decimal) -> Decimal:
    return d.quantize(EUR_QUANT, rounding=ROUND_HALF_UP)


def quantize_teo(d: Decimal) -> Decimal:
    return d.quantize(TEO_QUANT, rounding=ROUND_HALF_UP)


def compute_discount_breakdown(
    price_eur: Decimal,
    discount_percent: Decimal,
    tier: Optional[Dict] = None,
    accept_teo: bool = False,
    accept_ratio: Optional[Decimal] = None,
) -> Dict:
    """
    Pure function to compute discount/payout breakdown.

    Inputs:
      - price_eur: Decimal
      - discount_percent: Decimal (e.g., Decimal('10') for 10%)
      - tier: optional dict with keys:
          - teacher_split_percent (0..100)
          - platform_split_percent (0..100)
          - max_accept_discount_ratio (0..1)
          - teo_bonus_multiplier (>=1)
      - accept_teo: whether teacher accepts TEO
      - accept_ratio: fraction (0..max_accept_discount_ratio) of discount teacher accepts as TEO

    Returns dict with fields:
      student_pay_eur, teacher_eur, platform_eur, teacher_teo, platform_teo, absorption_policy
    """
    # Normalize inputs
    price = Decimal(price_eur)
    discount_pct = Decimal(discount_percent) / Decimal("100")

    if tier is None:
        # Default Bronze
        tier = {
            "teacher_split_percent": Decimal("50.00"),
            "platform_split_percent": Decimal("50.00"),
            "max_accept_discount_ratio": Decimal("1.00"),
            "teo_bonus_multiplier": Decimal("1.25"),
            "name": "Bronze",
        }

    teacher_split_pct = Decimal(str(tier.get("teacher_split_percent", Decimal("50.00")))) / Decimal("100")
    platform_split_pct = Decimal(str(tier.get("platform_split_percent", Decimal("50.00")))) / Decimal("100")
    max_ratio = Decimal(str(tier.get("max_accept_discount_ratio", Decimal("1.00"))))
    teo_bonus = Decimal(str(tier.get("teo_bonus_multiplier", Decimal("1.25"))))

    # Calculate gross splits on gross price
    teacher_gross_eur = (price * teacher_split_pct)
    platform_gross_eur = (price * platform_split_pct)

    # Discount amount (always applied to student)
    discount_amount = (price * discount_pct)
    # Student pays net
    student_pay = price - discount_amount

    # Absorption logic
    absorption_policy = "none"
    teacher_teo = Decimal("0")
    platform_teo = Decimal("0")

    # Default: platform absorbs discount (teacher EUR unchanged => teacher gets full teacher_gross_eur)
    teacher_eur = teacher_gross_eur
    platform_eur = platform_gross_eur - discount_amount

    # TEO conversion rate (TEO per 1 EUR). Default 1 if not configured.
    teo_rate = Decimal(str(getattr(settings, "TEOCOIN_EUR_RATE", 1)))

    # When platform absorbs entirely, platform owes equivalent TEO of the discount
    teacher_teo = Decimal("0")
    platform_teo = Decimal("0")

    if accept_teo:
        # determine actual accept_ratio
        if accept_ratio is None:
            accept_ratio = max_ratio
        accept_ratio = clamp_decimal(Decimal(accept_ratio), Decimal("0"), max_ratio)

        # Teacher accepts a portion r of the discount_amount as TEO
        r = accept_ratio
        # teacher gives up r*discount_amount EUR from their EUR payout
        eur_to_convert = discount_amount * r

        # teacher_eur reduces by eur_to_convert
        teacher_eur = teacher_gross_eur - eur_to_convert
        # platform gets rest of discount (discount_amount * (1 - r)) added to platform_eur
        platform_eur = platform_gross_eur - (discount_amount * (Decimal("1") - r))

        # Teacher receives TEO equal to r * discount_amount * teo_bonus (convert EUR->TEO)
        teacher_teo = discount_amount * r * teo_bonus * teo_rate
        # Platform TEO liability is remaining discount portion converted to TEO
        platform_teo = discount_amount * (Decimal("1") - r) * teo_rate
        absorption_policy = "teacher"
    else:
        # Platform absorbs full discount; platform owes TEO equal to discount_amount
        platform_teo = discount_amount * teo_rate

    # Prevent negative EUR outcomes (no negative payouts)
    if teacher_eur < Decimal("0"):
        teacher_eur = Decimal("0")
    if platform_eur < Decimal("0"):
        platform_eur = Decimal("0")

    # Quantize outputs
    student_pay_q = quantize_eur(student_pay)
    teacher_eur_q = quantize_eur(teacher_eur)
    platform_eur_q = quantize_eur(platform_eur)
    teacher_teo_q = quantize_teo(teacher_teo)
    platform_teo_q = quantize_teo(platform_teo)

    return {
        "student_pay_eur": student_pay_q,
        "teacher_eur": teacher_eur_q,
        "platform_eur": platform_eur_q,
        "teacher_teo": teacher_teo_q,
        "platform_teo": platform_teo_q,
        "absorption_policy": absorption_policy,
        "tier": tier,
        "raw": {
            "teacher_gross_eur": teacher_gross_eur,
            "platform_gross_eur": platform_gross_eur,
            "discount_amount": discount_amount,
            "accept_ratio": str(accept_ratio),
        },
    }
