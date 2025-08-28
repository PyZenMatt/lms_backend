from rest_framework import serializers

from .models import BlockchainTransaction


class BlockchainTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for blockchain transactions - replaces the old TeoCoinTransaction serializer.
    Provides detailed information about blockchain transactions including related objects.
    """

    explorer_url = serializers.ReadOnlyField()
    description = serializers.SerializerMethodField()
    related_object_title = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = BlockchainTransaction
        fields = [
            "id",
            "transaction_type",
            "amount",
            "from_address",
            "to_address",
            "tx_hash",
            "status",
            "error_message",
            "notes",
            "created_at",
            "confirmed_at",
            "explorer_url",
            "description",
            "related_object_title",
            "user",
        ]
        read_only_fields = ["id", "created_at", "confirmed_at", "explorer_url"]

    def get_description(self, obj):
        """Generate a human-readable description of the transaction"""
        if obj.notes:
            return obj.notes

        descriptions = {
            "course_purchase": f"Acquisto corso (${obj.amount} TEO)",
            "course_earned": f"Guadagno da vendita corso (${obj.amount} TEO)",
            "exercise_reward": f"Ricompensa esercizio (${obj.amount} TEO)",
            "review_reward": f"Ricompensa valutazione (${obj.amount} TEO)",
            "manual_mint": f"Distribuzione manuale (${obj.amount} TEO)",
            "reward_pool": f"Ricompensa dal pool (${obj.amount} TEO)",
        }

        return descriptions.get(
            obj.transaction_type, f"Transazione (${obj.amount} TEO)"
        )

    def get_related_object_title(self, obj):
        """Get the title of the related object (course, exercise, etc.)"""
        if not obj.related_object_id:
            return None

        try:
            if obj.transaction_type in ["course_purchase", "course_earned"]:
                from courses.models import Course

                course = Course.objects.get(pk=obj.related_object_id)
                return course.title

            elif obj.transaction_type in ["exercise_reward"]:
                from courses.models import Exercise

                exercise = Exercise.objects.get(pk=obj.related_object_id)
                return exercise.title

        except Exception:
            pass

        return None

    def get_user(self, obj):
        """Get user information for admin view"""
        if obj.user:
            return {
                "id": obj.user.id,
                "username": obj.user.username,
                "email": obj.user.email,
                "first_name": obj.user.first_name,
                "last_name": obj.user.last_name,
            }
        return None


# --- Discount preview/confirm serializers ---


class DiscountPreviewInputSerializer(serializers.Serializer):
    price_eur = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0, max_value=100, required=False, default=0)
    accept_teo = serializers.BooleanField(required=False, default=False)
    accept_ratio = serializers.DecimalField(max_digits=5, decimal_places=4, min_value=0, max_value=1, required=False, allow_null=True)
    course_id = serializers.IntegerField(required=False, allow_null=True)
    teacher_id = serializers.IntegerField(required=False, allow_null=True)
    student_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_course_id(self, value):
        if value is None:
            return value
        from courses.models import Course

        try:
            Course.objects.get(id=value)
        except Exception:
            raise serializers.ValidationError("course_id does not exist")
        return value

    def validate_teacher_id(self, value):
        if value is None:
            return value
        from users.models import User

        try:
            User.objects.get(id=value)
        except Exception:
            raise serializers.ValidationError("teacher_id does not exist")
        return value

    def validate_student_id(self, value):
        if value is None:
            return value
        from users.models import User

        try:
            User.objects.get(id=value)
        except Exception:
            raise serializers.ValidationError("student_id does not exist")
        return value


class DiscountConfirmInputSerializer(DiscountPreviewInputSerializer):
    order_id = serializers.CharField(max_length=200)


class DiscountBreakdownSerializer(serializers.Serializer):
    student_pay_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    teacher_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    platform_eur = serializers.DecimalField(max_digits=10, decimal_places=2)
    teacher_teo = serializers.DecimalField(max_digits=18, decimal_places=8)
    platform_teo = serializers.DecimalField(max_digits=18, decimal_places=8)
    absorption_policy = serializers.CharField()
    tier = serializers.DictField(child=serializers.CharField(), required=False, allow_null=True)


class PaymentDiscountSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import PaymentDiscountSnapshot

        model = PaymentDiscountSnapshot
        fields = [
            "id",
            "order_id",
            "course",
            "student",
            "teacher",
            "price_eur",
            "discount_percent",
            "student_pay_eur",
            "teacher_eur",
            "platform_eur",
            "teacher_teo",
            "platform_teo",
            # Offered values (computed on-the-fly for pending records)
            "offered_teacher_teo",
            "offered_platform_teo",
            "absorption_policy",
            "teacher_accepted_teo",
            "tier_name",
            "tier_teacher_split_percent",
            "tier_platform_split_percent",
            "tier_max_accept_discount_ratio",
            "tier_teo_bonus_multiplier",
            "created_at",
        ]
        read_only_fields = fields

    offered_teacher_teo = serializers.SerializerMethodField()
    offered_platform_teo = serializers.SerializerMethodField()

    def _build_tier_from_snapshot(self, obj):
        """Recreate tier dict from snapshot fields with safe fallbacks"""
        try:
            tier = {
                "teacher_split_percent": getattr(obj, "tier_teacher_split_percent", None) or None,
                "platform_split_percent": getattr(obj, "tier_platform_split_percent", None) or None,
                "max_accept_discount_ratio": getattr(obj, "tier_max_accept_discount_ratio", None) or None,
                "teo_bonus_multiplier": getattr(obj, "tier_teo_bonus_multiplier", None) or None,
                "name": getattr(obj, "tier_name", None) or None,
            }

            # If all tier-specific fields are missing/None, return None so the
            # discount calculator will use its default tier resolution (tier=None).
            tier_values = [
                tier.get("teacher_split_percent"),
                tier.get("platform_split_percent"),
                tier.get("max_accept_discount_ratio"),
                tier.get("teo_bonus_multiplier"),
            ]
            if all(v is None for v in tier_values):
                return None

            return tier
        except Exception:
            return None

    def get_offered_teacher_teo(self, obj):
        """Compute offered teacher TEO (as string with 8 d.p.) based on snapshot"""
        try:
            from services.discount_calc import compute_discount_breakdown
            from decimal import Decimal

            tier = self._build_tier_from_snapshot(obj)
            # Determine accept_ratio default: use tier max if present, otherwise 1
            max_ratio = None
            try:
                max_ratio = Decimal(str(tier.get("max_accept_discount_ratio"))) if tier and tier.get("max_accept_discount_ratio") is not None else None
            except Exception:
                max_ratio = None

            accept_ratio = max_ratio if max_ratio is not None else Decimal("1")

            breakdown = compute_discount_breakdown(
                price_eur=obj.price_eur,
                discount_percent=obj.discount_percent,
                tier=tier,
                accept_teo=True,
                accept_ratio=accept_ratio,
            )

            teacher_teo = breakdown.get("teacher_teo")
            if teacher_teo is None:
                return str(Decimal("0").quantize(Decimal("0.00000001")))
            # ensure string with 8 d.p.
            try:
                return str(Decimal(teacher_teo).quantize(Decimal("0.00000001")))
            except Exception:
                return str(Decimal("0").quantize(Decimal("0.00000001")))
        except Exception:
            # fallback zero as string with 8 decimals
            from decimal import Decimal

            return str(Decimal("0").quantize(Decimal("0.00000001")))

    def get_offered_platform_teo(self, obj):
        """Compute offered platform TEO (as string with 8 d.p.) based on snapshot"""
        try:
            from services.discount_calc import compute_discount_breakdown
            from decimal import Decimal

            tier = self._build_tier_from_snapshot(obj)
            max_ratio = None
            try:
                max_ratio = Decimal(str(tier.get("max_accept_discount_ratio"))) if tier and tier.get("max_accept_discount_ratio") is not None else None
            except Exception:
                max_ratio = None

            accept_ratio = max_ratio if max_ratio is not None else Decimal("1")

            breakdown = compute_discount_breakdown(
                price_eur=obj.price_eur,
                discount_percent=obj.discount_percent,
                tier=tier,
                accept_teo=True,
                accept_ratio=accept_ratio,
            )

            platform_teo = breakdown.get("platform_teo")
            if platform_teo is None:
                return str(Decimal("0").quantize(Decimal("0.00000001")))
            try:
                return str(Decimal(platform_teo).quantize(Decimal("0.00000001")))
            except Exception:
                return str(Decimal("0").quantize(Decimal("0.00000001")))
        except Exception:
            from decimal import Decimal

            return str(Decimal("0").quantize(Decimal("0.00000001")))
