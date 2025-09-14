"""
Database-Only Staking API Views

Provides REST API endpoints for the new database-only staking system.
This replaces blockchain staking with an instant, platform-internal system.
"""

import logging
from decimal import Decimal

from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import TeacherProfile
from core.economics import PlatformEconomics as PE

User = get_user_model()
logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_staking_info(request):
    """
    Get complete staking information for the authenticated teacher

    Only teachers can access staking functionality.

    Returns:
        - current_balance: Available TEO balance
        - staked_amount: Currently staked TEO
        - tier: Current staking tier
        - commission_rate: Current commission rate
        - next_tier_requirement: TEO needed for next tier
    """
    try:
        user = request.user

        # Check if user is a teacher
        if user.role != "teacher":
            return Response(
                {
                    "success": False,
                    "error": "Staking is only available for teachers. Students cannot stake TEO tokens.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get or create DB TeoCoin balance
        teo_balance, created = DBTeoCoinBalance.objects.get_or_create(
            user=user,
            defaults={
                "available_balance": Decimal("0.00"),
                "staked_balance": Decimal("0.00"),
            },
        )

        # Use the canonical PlatformEconomics as source-of-truth for tiers
        staked = teo_balance.staked_balance or Decimal("0")
        tier_info = PE.get_teacher_tier(staked)

        # Build next tier info by scanning canonical tiers
        tiers = PE.STAKING_TIERS
        # Create sorted list of (name, teo_required) ascending
        ordered = sorted(
            [(k, v["teo_required"]) for k, v in tiers.items()], key=lambda x: x[1]
        )

        next_tier = None
        next_tier_requirement = None
        for name, req in ordered:
            if Decimal(str(req)) > staked:
                next_tier = name.title()
                next_tier_requirement = float(req)
                break

        return Response(
            {
                "success": True,
                "current_balance": float(teo_balance.available_balance),
                "staked_amount": float(teo_balance.staked_balance),
                "total_balance": float(teo_balance.total_balance),
                # Provide human-friendly tier name
                "tier": tier_info["tier_name"].title(),
                # commission_rate exposed as percentage (e.g. 40.0)
                "commission_rate": float(Decimal(str(tier_info["commission_rate"])) * 100),
                "teacher_earnings_percentage": float(
                    100.0 - (Decimal(str(tier_info["commission_rate"])) * 100)
                ),
                "next_tier_requirement": next_tier_requirement,
                "next_tier": next_tier,
                "next_tier_needed": float(next_tier_requirement - float(staked))
                if next_tier_requirement
                else 0,
                "can_upgrade": next_tier_requirement is not None
                and Decimal(str(staked)) >= Decimal(str(next_tier_requirement)),
            }
        )

    except Exception as e:
        logger.error(f"Error getting staking info for {request.user.email}: {str(e)}")
        return Response(
            {"success": False, "error": f"Failed to get staking information: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stake_tokens(request):
    """
    Stake TEO tokens from available balance (Teachers only)

    Body:
        amount (float): Amount of TEO to stake
    """
    try:
        user = request.user

        # Check if user is a teacher
        if user.role != "teacher":
            return Response(
                {
                    "success": False,
                    "error": "Staking is only available for teachers. Students cannot stake TEO tokens.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        amount = Decimal(str(request.data.get("amount", 0)))

        if amount <= 0:
            return Response(
                {"success": False, "error": "Amount must be greater than zero"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Get user's TeoCoin balance
            teo_balance = DBTeoCoinBalance.objects.select_for_update().get(user=user)

            # Check if user has enough available balance
            if teo_balance.available_balance < amount:
                return Response(
                    {
                        "success": False,
                        "error": f"Insufficient balance. Available: {teo_balance.available_balance} TEO",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Move from available to staked
            teo_balance.available_balance -= amount
            teo_balance.staked_balance += amount
            teo_balance.save()

            # Update teacher profile
            teacher_profile = TeacherProfile.objects.get(user=user)
            teacher_profile.staked_teo_amount = teo_balance.staked_balance

            # Update tier and commission based on new stake
            old_tier = teacher_profile.staking_tier
            tier_info = teacher_profile.update_tier_and_commission()
            teacher_profile.save()

            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type="staked",
                amount=amount,
                description=f'Staked {amount} TEO. Tier: {old_tier} → {tier_info["tier"]}',
            )

            logger.info(
                f"User {user.email} staked {amount} TEO. New tier: {tier_info['tier']}"
            )

            return Response(
                {
                    "success": True,
                    "message": f"Successfully staked {amount} TEO",
                    "new_available_balance": float(teo_balance.available_balance),
                    "new_staked_balance": float(teo_balance.staked_balance),
                    "new_tier": tier_info["tier"],
                    "new_commission_rate": float(tier_info["commission_rate"]),
                    "tier_upgraded": old_tier != tier_info["tier"],
                }
            )

    except DBTeoCoinBalance.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "TeoCoin balance not found. Please contact support.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except TeacherProfile.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Teacher profile not found. Please contact support.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"Error staking tokens for {request.user.email}: {str(e)}")
        return Response(
            {"success": False, "error": f"Failed to stake tokens: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unstake_tokens(request):
    """
    Unstake TEO tokens back to available balance (Teachers only)

    Body:
        amount (float): Amount of TEO to unstake
    """
    try:
        user = request.user

        # Check if user is a teacher
        if user.role != "teacher":
            return Response(
                {
                    "success": False,
                    "error": "Staking is only available for teachers. Students cannot unstake TEO tokens.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        amount = Decimal(str(request.data.get("amount", 0)))

        if amount <= 0:
            return Response(
                {"success": False, "error": "Amount must be greater than zero"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            # Get user's TeoCoin balance
            teo_balance = DBTeoCoinBalance.objects.select_for_update().get(user=user)

            # Check if user has enough staked balance
            if teo_balance.staked_balance < amount:
                return Response(
                    {
                        "success": False,
                        "error": f"Insufficient staked balance. Staked: {teo_balance.staked_balance} TEO",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Move from staked to available
            teo_balance.staked_balance -= amount
            teo_balance.available_balance += amount
            teo_balance.save()

            # Update teacher profile
            teacher_profile = TeacherProfile.objects.get(user=user)
            teacher_profile.staked_teo_amount = teo_balance.staked_balance

            # Update tier and commission based on new stake
            old_tier = teacher_profile.staking_tier
            tier_info = teacher_profile.update_tier_and_commission()
            teacher_profile.save()

            # Record transaction
            DBTeoCoinTransaction.objects.create(
                user=user,
                transaction_type="unstaked",
                amount=amount,
                description=f'Unstaked {amount} TEO. Tier: {old_tier} → {tier_info["tier"]}',
            )

            logger.info(
                f"User {user.email} unstaked {amount} TEO. New tier: {tier_info['tier']}"
            )

            return Response(
                {
                    "success": True,
                    "message": f"Successfully unstaked {amount} TEO",
                    "new_available_balance": float(teo_balance.available_balance),
                    "new_staked_balance": float(teo_balance.staked_balance),
                    "new_tier": tier_info["tier"],
                    "new_commission_rate": float(tier_info["commission_rate"]),
                    "tier_downgraded": old_tier != tier_info["tier"],
                }
            )

    except DBTeoCoinBalance.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "TeoCoin balance not found. Please contact support.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except TeacherProfile.DoesNotExist:
        return Response(
            {
                "success": False,
                "error": "Teacher profile not found. Please contact support.",
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    except Exception as e:
        logger.error(f"Error unstaking tokens for {request.user.email}: {str(e)}")
        return Response(
            {"success": False, "error": f"Failed to unstake tokens: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def get_staking_tiers(request):
    """
    Get all staking tier configurations
    No authentication required - public information
    """
    try:
        # Build tiers dict from canonical PlatformEconomics.STAKING_TIERS
        canonical = PE.STAKING_TIERS
        out = {}
        # Keep a simple ordering by teo_required ascending
        for name, cfg in sorted(canonical.items(), key=lambda x: x[1]["teo_required"]):
            commission_pct = float(cfg["commission_rate"] * 100)
            teacher_pct = float(cfg["teacher_rate"] * 100)
            out[name.title()] = {
                "min_stake": float(cfg["teo_required"]),
                "commission_rate": commission_pct,
                "teacher_earnings": teacher_pct,
                "description": "",
                # keep compatibility placeholders
                "benefits": [],
            }

        return Response({"success": True, "tiers": out})

    except Exception as e:
        logger.error(f"Error getting staking tiers: {str(e)}")
        return Response(
            {"success": False, "error": f"Failed to get staking tiers: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
def calculate_commission(request):
    """
    Calculate commission rates and tier progression

    Query params:
        current_stake (float): Current staked amount
    """
    try:
        current_stake = Decimal(str(request.GET.get("current_stake", 0)))

        # Use canonical tiers
        canonical = PE.STAKING_TIERS
        # Determine current tier using PlatformEconomics helper
        current = PE.get_teacher_tier(current_stake)
        current_commission_pct = Decimal(str(current["commission_rate"])) * 100
        current_teacher_pct = Decimal("100.0") - current_commission_pct

        # Find next tier by scanning ordered teo_required
        ordered = sorted(
            [(k, v["teo_required"]) for k, v in canonical.items()], key=lambda x: x[1]
        )
        next_tier = None
        next_tier_requirement = None
        next_tier_commission_pct = None
        for name, req in ordered:
            if Decimal(str(req)) > current_stake:
                next_tier = name.title()
                next_tier_requirement = float(req)
                next_cfg = canonical[name]
                next_tier_commission_pct = float(next_cfg["commission_rate"] * 100)
                break

        return Response(
            {
                "success": True,
                "current_stake": float(current_stake),
                "current_tier": current["tier_name"].title(),
                "current_commission_rate": float(current_commission_pct),
                "current_teacher_earnings": float(current_teacher_pct),
                "next_tier": next_tier,
                "next_tier_requirement": next_tier_requirement,
                "next_tier_commission": next_tier_commission_pct,
                "next_tier_teacher_earnings": (
                    float(100.0 - next_tier_commission_pct)
                    if next_tier_commission_pct is not None
                    else None
                ),
                "additional_stake_needed": (
                    float(next_tier_requirement - float(current_stake))
                    if next_tier_requirement
                    else 0
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error calculating commission: {str(e)}")
        return Response(
            {"success": False, "error": f"Failed to calculate commission: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
