from courses.models import Course, ExerciseSubmission, Lesson
from rest_framework import serializers

from .models import Notification
from decimal import Decimal


class NotificationSerializer(serializers.ModelSerializer):
    related_object = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    # Enrichment for discount pending notifications: offer preview (string, 8 d.p.)
    offered_teacher_teo = serializers.SerializerMethodField()
    discount_eur = serializers.SerializerMethodField()
    # Include resolved decision id for FE actions
    decision_id = serializers.SerializerMethodField()
    # Hint the FE about what the related id refers to (best-effort)
    related_object_type = serializers.SerializerMethodField()
    # Include additional structured fields from extra_data
    tier = serializers.SerializerMethodField()
    staking_allowed = serializers.SerializerMethodField()
    expires_at = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "message",
            "notification_type",
            "read",
            "created_at",
            "related_object",
            "link",
            "offered_teacher_teo",
            "discount_eur",
            "related_object_id",
            "related_object_type",
            "decision_id",
            "tier",
            "staking_allowed",
            "expires_at",
        ]
        ordering = ["-created_at"]

    def _get_extra_data(self, obj):
        """Parse extra_data JSON if available"""
        try:
            extra_data = getattr(obj, "extra_data", None)
            if extra_data:
                if isinstance(extra_data, str):
                    import json
                    return json.loads(extra_data)
                elif isinstance(extra_data, dict):
                    return extra_data
        except Exception:
            pass
        return {}

    def get_link(self, obj):
        """Generate appropriate navigation links based on notification type"""
        try:
            # Reviews e Exercises
            if obj.notification_type == "review_assigned" and obj.related_object_id:
                return f"/review/{obj.related_object_id}"
            elif obj.notification_type == "exercise_graded" and obj.related_object_id:
                return f"/submission-graded/{obj.related_object_id}"

            # Corsi e Lezioni
            elif (
                obj.notification_type
                in ["lesson_purchased", "lesson_sold", "new_lesson_added"]
                and obj.related_object_id
            ):
                return f"/lezioni/{obj.related_object_id}"
            elif (
                obj.notification_type
                in [
                    "course_approved",
                    "course_purchased",
                    "course_sold",
                    "course_completed",
                    "new_course_published",
                    "course_updated",
                ]
                and obj.related_object_id
            ):
                return f"/corsi/{obj.related_object_id}"

            # TeoCoins e Rewards - redirect al profilo
            elif obj.notification_type in [
                "teocoins_earned",
                "teocoins_spent",
                "reward_earned",
                "bonus_received",
            ]:
                return "/profile"

            # Achievements e Sistema
            elif obj.notification_type in ["achievement_unlocked", "level_up"]:
                return "/profile"

            # Default per notifiche di sistema
            elif obj.notification_type in ["system_message", "welcome_message"]:
                return "/dashboard/student"

            return None
        except Exception:
            return None

    def to_representation(self, instance):
        """Include a backward-compatible absorption_id for discount notifications"""
        data = super().to_representation(instance)
        try:
            if data.get("notification_type") in ["teocoin_discount_pending", "teocoin_discount_pending_urgent"] and data.get("related_object_id"):
                data["absorption_id"] = data["related_object_id"]
        except Exception:
            pass
        return data

    def get_related_object(self, obj):
        try:
            if obj.notification_type == "exercise_graded":
                submission = ExerciseSubmission.objects.get(id=obj.related_object_id)
                return {
                    "id": getattr(submission, "id", None),
                    "exercise_title": submission.exercise.title,
                    "lesson_title": submission.exercise.lesson.title,
                    "submitted_at": submission.submitted_at,
                }
            elif obj.notification_type in [
                "lesson_purchased",
                "lesson_sold",
                "new_lesson_added",
            ]:
                lesson = Lesson.objects.get(id=obj.related_object_id)
                return {
                    "id": getattr(lesson, "id", None),
                    "title": lesson.title,
                    "price": getattr(lesson, "price", None),
                }
            elif obj.notification_type in [
                "course_approved",
                "course_purchased",
                "course_sold",
                "course_completed",
                "new_course_published",
                "course_updated",
            ]:
                course = Course.objects.get(id=obj.related_object_id)
                return {
                    "id": getattr(course, "id", None),
                    "title": course.title,
                    "price": getattr(course, "price", None),
                    "category": getattr(course, "category", None),
                }
            elif obj.notification_type in [
                "teocoins_earned",
                "teocoins_spent",
                "reward_earned",
                "bonus_received",
            ]:
                # Per le notifiche TeoCoin, related_object_id potrebbe essere l'amount o transaction_id
                return {"amount": obj.related_object_id, "type": obj.notification_type}
        except Exception:
            return None

    def get_offered_teacher_teo(self, obj):
        """Return offered_teacher_teo as string with 8 d.p. for teocoin_discount_pending.

        Priority:
        1) Check extra_data for offered_teacher_teo (source of truth from services)
        2) Resolve via TeacherDiscountDecision.related (obj.related_object_id assumed to be decision.id)
           offered = (teo_cost + teacher_bonus) / 1e18 → format 8 d.p.
        3) Legacy fallback: resolve via PaymentDiscountSnapshot (order_id or pk) and reuse
           PaymentDiscountSnapshotSerializer.offered_teacher_teo
        4) If nothing can be resolved, return None (avoid misleading "0.00000000").
        """
        try:
            # For pending/urgent discount notifications we intentionally do not
            # expose offered_teacher_teo (TEO amounts) in the API. Always return
            # None to avoid leaking TEO quantities to the frontend.
            if obj.notification_type in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                return None

            decision_id = obj.related_object_id
            # Try resolve decision first
            try:
                from courses.models import TeacherDiscountDecision

                dec = (
                    TeacherDiscountDecision.objects.filter(pk=decision_id).first()
                    if decision_id
                    else None
                )
                if dec:
                    total_wei = Decimal(str(getattr(dec, "teo_cost", 0))) + Decimal(
                        str(getattr(dec, "teacher_bonus", 0))
                    )
                    offered = (total_wei / Decimal(10 ** 18)).quantize(
                        Decimal("0.00000001")
                    )
                    return f"{offered:.8f}"
            except Exception:
                pass

            # Legacy fallback via snapshot
            try:
                from rewards.models import PaymentDiscountSnapshot
                from rewards.serializers import PaymentDiscountSnapshotSerializer

                snap = None
                try:
                    snap = PaymentDiscountSnapshot.objects.filter(
                        order_id=str(obj.related_object_id)
                    ).first()
                except Exception:
                    snap = None
                if not snap:
                    try:
                        snap = PaymentDiscountSnapshot.objects.filter(
                            pk=obj.related_object_id
                        ).first()
                    except Exception:
                        snap = None
                if snap:
                    raw = PaymentDiscountSnapshotSerializer(snap).data
                    if isinstance(raw, dict):
                        val = raw.get("offered_teacher_teo")
                    else:
                        try:
                            val = getattr(raw, "get", lambda *_: None)(
                                "offered_teacher_teo"
                            )
                        except Exception:
                            val = None
                    if val is not None:
                        return val
            except Exception:
                pass
        except Exception:
            pass

        # Prefer None over a misleading zero string
        return None

    def get_decision_id(self, obj):
        """Prefer direct related_object_id as the TeacherDiscountDecision id for pending discount notifications.

        Priority:
        1) Check extra_data for decision_id (source of truth from services)
        2) Direct related_object_id as the TeacherDiscountDecision id
        3) Backward compatibility: if related_object_id points to a snapshot/order, try to resolve the
           matching pending decision the old way.
        """
        try:
            if obj.notification_type not in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                return None

            # Priority 1: Check extra_data first
            extra_data = self._get_extra_data(obj)
            if extra_data.get("decision_id") is not None:
                return extra_data["decision_id"]

            # Fast path: if related_object_id is a real decision id
            try:
                from courses.models import TeacherDiscountDecision

                dec = TeacherDiscountDecision.objects.filter(pk=obj.related_object_id).first()
                if dec:
                    return getattr(dec, "id", None)
            except Exception:
                pass

            # Fallback legacy resolution via snapshot
            try:
                from rewards.models import PaymentDiscountSnapshot
                from courses.models import TeacherDiscountDecision

                snap = None
                try:
                    snap = PaymentDiscountSnapshot.objects.filter(pk=obj.related_object_id).first()
                except Exception:
                    snap = None
                if not snap:
                    try:
                        snap = PaymentDiscountSnapshot.objects.filter(order_id=str(obj.related_object_id)).first()
                    except Exception:
                        snap = None
                if not snap:
                    return None
                decision = (
                    TeacherDiscountDecision.objects.filter(
                        teacher=snap.teacher,
                        student=snap.student,
                        course=snap.course,
                        decision="pending",
                    )
                    .order_by("-created_at")
                    .first()
                )
                return getattr(decision, "id", None)
            except Exception:
                return None
        except Exception:
            return None

    def get_discount_eur(self, obj):
        """Return discount in EUR (5/10/15) for discount notifications.

        Strategy:
        1) Check extra_data for discount_eur (source of truth from services)
        2) If related_object_id points to a TeacherDiscountDecision, read discount_percentage
        3) Else, try PaymentDiscountSnapshot.discount_percent
        4) Map percent -> fixed eur amount using known mapping (5/10/15) or None
        """
        try:
            if obj.notification_type not in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                return None

            # Priority 1: Check extra_data first
            extra_data = self._get_extra_data(obj)
            if extra_data.get("discount_eur") is not None:
                return extra_data["discount_eur"]

            # Try TeacherDiscountDecision
            try:
                from courses.models import TeacherDiscountDecision

                dec = TeacherDiscountDecision.objects.filter(pk=obj.related_object_id).first()
                if dec:
                    pct = getattr(dec, "discount_percentage", None)
                    if pct in (5, 10, 15):
                        return int(pct)
            except Exception:
                pass

            # Fallback to snapshot
            try:
                from rewards.models import PaymentDiscountSnapshot

                snap = PaymentDiscountSnapshot.objects.filter(pk=obj.related_object_id).first()
                if not snap:
                    snap = PaymentDiscountSnapshot.objects.filter(order_id=str(obj.related_object_id)).first()
                if snap:
                    pct = getattr(snap, "discount_percent", None)
                    if pct in (5, 10, 15):
                        return int(pct)
            except Exception:
                pass
        except Exception:
            pass
        return None

    def get_related_object_type(self, obj):
        try:
            if obj.notification_type in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                # As of Aug 2025 we bind related_object_id to the TeacherDiscountDecision
                return "TeacherDiscountDecision"
        except Exception:
            pass
        return None

    def get_tier(self, obj):
        """Return tier name for discount notifications"""
        try:
            if obj.notification_type not in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                return None

            # Check extra_data first
            extra_data = self._get_extra_data(obj)
            tier = extra_data.get("tier")
            if tier:
                return str(tier)
        except Exception:
            pass
        return None

    def get_staking_allowed(self, obj):
        """Return staking_allowed for discount notifications"""
        try:
            if obj.notification_type not in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                return None

            # Check extra_data first
            extra_data = self._get_extra_data(obj)
            staking = extra_data.get("staking_allowed")
            if isinstance(staking, bool):
                return staking
        except Exception:
            pass
        return None

    def get_expires_at(self, obj):
        """Return expires_at for discount notifications"""
        try:
            if obj.notification_type not in ("teocoin_discount_pending", "teocoin_discount_pending_urgent"):
                return None

            # Check extra_data first
            extra_data = self._get_extra_data(obj)
            expires = extra_data.get("expires_at")
            if expires:
                return str(expires)
        except Exception:
            pass
        return None
