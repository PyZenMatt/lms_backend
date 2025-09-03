from decimal import Decimal
from services.discount_calc import compute_discount_breakdown


def test_case_1_no_discount():
    r = compute_discount_breakdown(Decimal("100"), Decimal("0"))
    assert r["student_pay_eur"] == Decimal("100.00")
    assert r["teacher_eur"] == Decimal("50.00")
    assert r["platform_eur"] == Decimal("50.00")
    assert r["teacher_teo"] == Decimal("0E-8")


def test_case_2_platform_absorbs():
    r = compute_discount_breakdown(Decimal("100"), Decimal("10"), None, accept_teo=False)
    assert r["student_pay_eur"] == Decimal("90.00")
    assert r["teacher_eur"] == Decimal("50.00")
    assert r["platform_eur"] == Decimal("40.00")
    # platform_teo should equal discount amount (10 EUR -> 10 TEO accounting)
    assert r["platform_teo"] == Decimal("10.00000000")


def test_case_3_teacher_accepts_full():
    r = compute_discount_breakdown(Decimal("100"), Decimal("10"), None, accept_teo=True, accept_ratio=Decimal("1"))
    assert r["student_pay_eur"] == Decimal("90.00")
    assert r["teacher_eur"] == Decimal("40.00")
    assert r["platform_eur"] == Decimal("50.00")
    assert r["teacher_teo"] == Decimal("12.50000000")


def test_case_4_ratio_clamping():
    # ratio > max -> clamp
    tier = {"teacher_split_percent": Decimal("50"), "platform_split_percent": Decimal("50"), "max_accept_discount_ratio": Decimal("1.00"), "teo_bonus_multiplier": Decimal("1.25")}
    r = compute_discount_breakdown(Decimal("100"), Decimal("15"), tier, accept_teo=True, accept_ratio=Decimal("1.5"))
    # discount amount 15 => teacher_gross 50 - 15 = 35 -> teacher_eur 35.00
    assert r["teacher_eur"] == Decimal("35.00")
    assert r["teacher_teo"] == Decimal("18.75000000")


def test_case_5_edge_full_discount():
    # 100% discount - student pays 0; ensure no negative payouts
    r_false = compute_discount_breakdown(Decimal("100"), Decimal("100"), None, accept_teo=False)
    assert r_false["student_pay_eur"] == Decimal("0.00")
    # teacher still gets their gross 50, platform_eur = 50 - 100 => clamped to 0
    assert r_false["teacher_eur"] == Decimal("50.00")
    assert r_false["platform_eur"] == Decimal("0.00")

    r_true = compute_discount_breakdown(Decimal("100"), Decimal("100"), None, accept_teo=True, accept_ratio=Decimal("1"))
    # teacher gives up 100*1 => teacher_eur = 50 - 100 = -50 -> clamped to 0
    assert r_true["teacher_eur"] == Decimal("0.00")
    # teacher_teo = 100 * 1 * 1.25 = 125 TEO
    assert r_true["teacher_teo"] == Decimal("125.00000000")


def test_case_6_custom_split():
    tier = {"teacher_split_percent": Decimal("70"), "platform_split_percent": Decimal("30"), "max_accept_discount_ratio": Decimal("1.00"), "teo_bonus_multiplier": Decimal("1.00")}
    r = compute_discount_breakdown(Decimal("200"), Decimal("10"), tier, accept_teo=False)
    # price 200, discount 20 -> student 180
    assert r["student_pay_eur"] == Decimal("180.00")
    # teacher_gross = 200 * 0.7 = 140
    assert r["teacher_eur"] == Decimal("140.00")
    # platform_gross = 60 - discount 20 = 40
    assert r["platform_eur"] == Decimal("40.00")
