"""
Rewards teocoin-related views

This module exposes a small compatibility endpoint used by the frontend
at /api/v1/rewards/staking/overview/ so older FE routes keep working while
the canonical staking API lives under /api/v1/services/staking/.

The endpoint is intentionally lightweight and composes its response from
the DB-based staking models (DBTeoCoinBalance and TeacherProfile).
"""

import logging
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from blockchain.models import DBTeoCoinBalance
from users.models import TeacherProfile
from core.economics import PlatformEconomics as PE
from blockchain.models import DBTeoCoinTransaction
from django.db import transaction

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staking_overview(request):
	"""Compatibility endpoint for frontend:

	Returns a compact overview of the authenticated teacher staking state.

	Response fields (example):
	  - balance_teo: available + staked (float)
	  - available_teo: available balance (float)
	  - staked_teo: staked balance (float)
	  - tier_name: current tier string
	  - commission_rate: platform commission percent (float)
	  - bonus_multiplier: multiplicative factor for teacher earnings (e.g. 0.25 means +25%%)
	  - next_tier: name of the next tier or null
	  - next_tier_threshold_teo: amount required for next tier or null
	"""
	try:
		user = request.user
		logger.info("staking_overview requested by user_id=%s email=%s", getattr(user, "id", None), getattr(user, "email", None))

		# Only teachers have staking
		if getattr(user, "role", None) != "teacher":
			return Response(
				{"ok": False, "error": "Staking available only for teachers"},
				status=status.HTTP_403_FORBIDDEN,
			)

		# Get or create balances/profiles
		teo_balance, _ = DBTeoCoinBalance.objects.get_or_create(
			user=user,
			defaults={
				"available_balance": Decimal("0.00"),
				"staked_balance": Decimal("0.00"),
			},
		)

		# Create or get teacher profile using SOT defaults when creating
		default_tier = PE.get_teacher_tier(Decimal("0"))
		default_commission_pct = Decimal(str(default_tier["commission_rate"])) * Decimal("100")
		teacher_profile, _ = TeacherProfile.objects.get_or_create(
			user=user,
			defaults={
				"commission_rate": default_commission_pct,
				"staking_tier": default_tier["tier_name"].title(),
				"staked_teo_amount": Decimal("0.00"),
			},
		)

		# Ensure teacher_profile staked amount mirrors DB balance
		if teacher_profile.staked_teo_amount != teo_balance.staked_balance:
			teacher_profile.staked_teo_amount = teo_balance.staked_balance
			teacher_profile.update_tier_and_commission()
			teacher_profile.save()

		# Determine current tier & next tier using canonical staking tiers
		staked = teo_balance.staked_balance or Decimal("0")
		tier_info = PE.get_teacher_tier(staked)
		# build ordered tiers ascending by teo_required
		ordered = sorted([(k, v["teo_required"]) for k, v in PE.STAKING_TIERS.items()], key=lambda x: x[1])
		next_tier = None
		next_threshold = None
		for name, req in ordered:
			if Decimal(str(req)) > staked:
				next_tier = name.title()
				next_threshold = req
				break

		# Bonus multiplier: difference vs bronze tier (use canonical bronze)
		bronze_cfg = PE.STAKING_TIERS.get("bronze", {})
		bronze_commission_pct = Decimal(str(bronze_cfg.get("commission_rate", Decimal("0.50")))) * Decimal("100")
		current_commission_pct = Decimal(str(tier_info.get("commission_rate", Decimal("0")))) * Decimal("100")
		bonus_percent = bronze_commission_pct - current_commission_pct
		bonus_multiplier = float(bonus_percent / Decimal("100"))

		# Debug: log balances returned
		logger.info(
			"staking_overview response for user_id=%s: available=%s staked=%s",
			getattr(user, "id", None),
			teo_balance.available_balance,
			teo_balance.staked_balance,
		)

		return Response(
			{
				"ok": True,
				"balance_teo": float(teo_balance.available_balance + teo_balance.staked_balance),
				"available_teo": float(teo_balance.available_balance),
				"staked_teo": float(teo_balance.staked_balance),
				"tier_name": tier_info["tier_name"].title(),
				"commission_rate": float(current_commission_pct),
				"teacher_earnings": float(100.0 - current_commission_pct),
				"bonus_multiplier": bonus_multiplier,
				"next_tier": next_tier,
				"next_tier_threshold_teo": float(next_threshold)
				if next_threshold is not None
				else None,
			}
		)

	except Exception as e:
		logger.exception(f"staking_overview error for {request.user.email}: {e}")
		return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_staking_tiers_rewards(request):
	"""Expose staking tiers for the frontend under rewards path (compat)."""
	try:
		tiers = {
			"Bronze": {
				"min_stake": 0,
				"commission_rate": 50.0,
				"teacher_earnings": 50.0,
				"color": "secondary",
				"benefits": ["Basic platform access", "Standard support"],
				"description": "Starting tier for all teachers",
			},
			"Silver": {
				"min_stake": 100.0,
				"commission_rate": 45.0,
				"teacher_earnings": 55.0,
				"color": "default",
				"benefits": ["5% higher earnings", "Priority support"],
				"description": "Enhanced earnings and support",
			},
			"Gold": {
				"min_stake": 300.0,
				"commission_rate": 40.0,
				"teacher_earnings": 60.0,
				"color": "warning",
				"benefits": ["10% higher earnings", "Advanced analytics"],
				"description": "Premium features and analytics",
			},
			"Platinum": {
				"min_stake": 600.0,
				"commission_rate": 35.0,
				"teacher_earnings": 65.0,
				"color": "primary",
				"benefits": ["15% higher earnings", "Premium features"],
				"description": "All premium features unlocked",
			},
			"Diamond": {
				"min_stake": 1000.0,
				"commission_rate": 25.0,
				"teacher_earnings": 75.0,
				"color": "success",
				"benefits": ["25% higher earnings", "VIP support", "All features"],
				"description": "Maximum tier with VIP treatment",
			},
		}

		return Response({"ok": True, "tiers": tiers})

	except Exception as e:
		logger.exception(f"get_staking_tiers_rewards error: {e}")
		return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def stake_from_rewards(request):
	"""Stake TEO via rewards path (compat)"""
	try:
		user = request.user
		if getattr(user, "role", None) != "teacher":
			return Response({"ok": False, "error": "Staking only for teachers"}, status=status.HTTP_403_FORBIDDEN)

		amount = Decimal(str(request.data.get("amount", 0)))
		if amount <= 0:
			return Response({"ok": False, "error": "Amount must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

		with transaction.atomic():
			teo_balance = DBTeoCoinBalance.objects.select_for_update().get(user=user)
			if teo_balance.available_balance < amount:
				return Response({"ok": False, "error": "Insufficient available balance"}, status=status.HTTP_400_BAD_REQUEST)

			teo_balance.available_balance -= amount
			teo_balance.staked_balance += amount
			teo_balance.save()

			teacher_profile = TeacherProfile.objects.get(user=user)
			teacher_profile.staked_teo_amount = teo_balance.staked_balance
			old_tier = teacher_profile.staking_tier
			tier_info = teacher_profile.update_tier_and_commission()
			teacher_profile.save()

			DBTeoCoinTransaction.objects.create(
				user=user,
				transaction_type="staked",
				amount=amount,
				description=f"Staked {amount} TEO. Tier: {old_tier} → {tier_info['tier']}",
			)

			logger.info("stake_from_rewards: user_id=%s available=%s staked=%s", user.id, teo_balance.available_balance, teo_balance.staked_balance)

			return Response({
				"ok": True,
				"message": f"Staked {amount} TEO",
				"new_available_balance": float(teo_balance.available_balance),
				"new_staked_balance": float(teo_balance.staked_balance),
				"new_tier": tier_info["tier"],
				"new_commission_rate": float(tier_info["commission_rate"]),
			})

	except DBTeoCoinBalance.DoesNotExist:
		return Response({"ok": False, "error": "Balance not found"}, status=status.HTTP_404_NOT_FOUND)
	except TeacherProfile.DoesNotExist:
		return Response({"ok": False, "error": "Teacher profile not found"}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception(f"stake_from_rewards error for {getattr(request.user, 'email', None)}: {e}")
		return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unstake_from_rewards(request):
	"""Unstake TEO via rewards path (compat)"""
	try:
		user = request.user
		if getattr(user, "role", None) != "teacher":
			return Response({"ok": False, "error": "Staking only for teachers"}, status=status.HTTP_403_FORBIDDEN)

		amount = Decimal(str(request.data.get("amount", 0)))
		if amount <= 0:
			return Response({"ok": False, "error": "Amount must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

		with transaction.atomic():
			teo_balance = DBTeoCoinBalance.objects.select_for_update().get(user=user)
			if teo_balance.staked_balance < amount:
				return Response({"ok": False, "error": "Insufficient staked balance"}, status=status.HTTP_400_BAD_REQUEST)

			teo_balance.staked_balance -= amount
			teo_balance.available_balance += amount
			teo_balance.save()

			teacher_profile = TeacherProfile.objects.get(user=user)
			teacher_profile.staked_teo_amount = teo_balance.staked_balance
			old_tier = teacher_profile.staking_tier
			tier_info = teacher_profile.update_tier_and_commission()
			teacher_profile.save()

			DBTeoCoinTransaction.objects.create(
				user=user,
				transaction_type="unstaked",
				amount=amount,
				description=f"Unstaked {amount} TEO. Tier: {old_tier} → {tier_info['tier']}",
			)

			logger.info("unstake_from_rewards: user_id=%s available=%s staked=%s", user.id, teo_balance.available_balance, teo_balance.staked_balance)

			return Response({
				"ok": True,
				"message": f"Unstaked {amount} TEO",
				"new_available_balance": float(teo_balance.available_balance),
				"new_staked_balance": float(teo_balance.staked_balance),
				"new_tier": tier_info["tier"],
				"new_commission_rate": float(tier_info["commission_rate"]),
			})

	except DBTeoCoinBalance.DoesNotExist:
		return Response({"ok": False, "error": "Balance not found"}, status=status.HTTP_404_NOT_FOUND)
	except TeacherProfile.DoesNotExist:
		return Response({"ok": False, "error": "Teacher profile not found"}, status=status.HTTP_404_NOT_FOUND)
	except Exception as e:
		logger.exception(f"unstake_from_rewards error for {getattr(request.user, 'email', None)}: {e}")
		return Response({"ok": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

