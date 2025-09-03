from courses.models import Course, ExerciseSubmission, Lesson
from rest_framework import serializers

from .models import Notification
from decimal import Decimal


class NotificationSerializer(serializers.ModelSerializer):
    related_object = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    # Enrichment for discount pending notifications: offer preview (string, 8 d.p.)
    offered_teacher_teo = serializers.SerializerMethodField()
    # Include resolved decision id for FE actions
    decision_id = serializers.SerializerMethodField()
    # Hint the FE about what the related id refers to (best-effort)
    related_object_type = serializers.SerializerMethodField()

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
            "related_object_id",
            "related_object_type",
            "decision_id",
        ]
        ordering = ["-created_at"]

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
            if data.get("notification_type") == "teocoin_discount_pending" and data.get(
                "related_object_id"
            ):
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
        1) Resolve via TeacherDiscountDecision.related (obj.related_object_id assumed to be decision.id)
           offered = (teo_cost + teacher_bonus) / 1e18 → format 8 d.p.
        2) Legacy fallback: resolve via PaymentDiscountSnapshot (order_id or pk) and reuse
           PaymentDiscountSnapshotSerializer.offered_teacher_teo
        3) If nothing can be resolved, return None (avoid misleading "0.00000000").
        """
        try:
            if obj.notification_type != "teocoin_discount_pending":
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

        Backward compatibility: if related_object_id points to a snapshot/order, try to resolve the
        matching pending decision the old way.
        """
        try:
            if obj.notification_type != "teocoin_discount_pending":
                return None
            # Fast path: if related_object_id is a real decision id
            try:
                from courses.models import TeacherDiscountDecision

                dec = TeacherDiscountDecision.objects.filter(
                    pk=obj.related_object_id
                ).first()
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

    def get_related_object_type(self, obj):
        try:
            if obj.notification_type == "teocoin_discount_pending":
                # As of Aug 2025 we bind related_object_id to the TeacherDiscountDecision
                return "TeacherDiscountDecision"
        except Exception:
            pass
        return None
