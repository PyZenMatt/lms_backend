#!/usr/bin/env python

import os
import sys
import django
from decimal import Decimal

# Add Django path and configure settings
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from services.discount_calc import compute_discount_breakdown

def test_flat_vs_percentage():
    """Test flat discount vs percentage discount calculation"""
    
    price_eur = Decimal("1250.00")  # High price course
    discount_percent = Decimal("15")  # 15%
    discount_amount_eur = Decimal("15.00")  # 15 EUR flat
    
    # Test with default Bronze tier
    tier = {
        "teacher_split_percent": Decimal("50.00"),
        "platform_split_percent": Decimal("50.00"),
        "max_accept_discount_ratio": Decimal("1.00"),
        "teo_bonus_multiplier": Decimal("1.25"),
        "name": "Bronze",
    }
    
    print("=== Testing Flat Discount vs Percentage Discount ===")
    print(f"Course Price: €{price_eur}")
    print(f"Tier: {tier['name']}")
    print(f"TEO Bonus Multiplier: {tier['teo_bonus_multiplier']}")
    print()
    
    # Test percentage-based calculation (OLD WAY)
    print("--- Percentage-based calculation (OLD) ---")
    breakdown_pct = compute_discount_breakdown(
        price_eur=price_eur,
        discount_percent=discount_percent,
        tier=tier,
        accept_teo=True,
        accept_ratio=Decimal("1.0")
    )
    print(f"Discount: {discount_percent}% of €{price_eur} = €{price_eur * discount_percent / 100}")
    print(f"Teacher TEO offered: {breakdown_pct['teacher_teo']}")
    print(f"Platform TEO liability: {breakdown_pct['platform_teo']}")
    print()
    
    # Test flat amount calculation (NEW WAY)
    print("--- Flat amount calculation (NEW) ---")
    breakdown_flat = compute_discount_breakdown(
        price_eur=price_eur,
        discount_amount_eur=discount_amount_eur,
        tier=tier,
        accept_teo=True,
        accept_ratio=Decimal("1.0")
    )
    print(f"Discount: €{discount_amount_eur} flat")
    print(f"Teacher TEO offered: {breakdown_flat['teacher_teo']}")
    print(f"Platform TEO liability: {breakdown_flat['platform_teo']}")
    print()
    
    # Verification
    expected_teo = discount_amount_eur * tier['teo_bonus_multiplier']  # 15 * 1.25 = 18.75
    print("--- Verification ---")
    print(f"Expected teacher TEO (15 EUR * 1.25 bonus): {expected_teo}")
    print(f"Actual teacher TEO: {breakdown_flat['teacher_teo']}")
    print(f"✅ Match: {abs(breakdown_flat['teacher_teo'] - expected_teo) < Decimal('0.01')}")
    print()
    
    print(f"OLD WAY (percentage): {breakdown_pct['teacher_teo']} TEO ❌")
    print(f"NEW WAY (flat): {breakdown_flat['teacher_teo']} TEO ✅")

if __name__ == "__main__":
    test_flat_vs_percentage()
