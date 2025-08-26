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
