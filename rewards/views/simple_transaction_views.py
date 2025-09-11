from rest_framework import status, permissions, views
from rest_framework.response import Response
from decimal import Decimal
import hashlib
from django.db import transaction, IntegrityError
from rewards.models import PaymentDiscountSnapshot

from rewards.services.transaction_services import (
    apply_discount_and_snapshot,
    teacher_make_decision,
)


class ApplyDiscountView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _generate_idempotency_key(self, student_user_id, teacher_id, course_id, teo_cost, checkout_session_id=None):
        """Generate idempotency key to prevent duplicate discount applications"""
        key_data = f"{student_user_id}:{teacher_id}:{course_id}:{teo_cost}"
        if checkout_session_id:
            key_data += f":{checkout_session_id}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def post(self, request, *args, **kwargs):
        data = request.data
        
        # Extract parameters
        student_user_id = int(data["student_user_id"])
        teacher_id = int(data["teacher_id"])
        course_id = int(data["course_id"])
        teo_cost = Decimal(str(data["teo_cost"]))
        offered_teacher_teo = Decimal(str(data.get("offered_teacher_teo", "0")))
        checkout_session_id = data.get("checkout_session_id")  # Optional client session ID
        
        # Generate idempotency key
        idempotency_key = self._generate_idempotency_key(
            student_user_id, teacher_id, course_id, teo_cost, checkout_session_id
        )

        # Check if discount already applied with this key (active/pending)
        try:
            with transaction.atomic():
                existing_snapshot = (
                    PaymentDiscountSnapshot.objects.select_for_update()
                    .filter(idempotency_key=idempotency_key)
                    .first()
                )

                if existing_snapshot and existing_snapshot.status in ("pending", "closed"):
                    # Return existing snapshot without side effects
                    return Response({
                        "snapshot_id": existing_snapshot.id,
                        "pending_decision_id": existing_snapshot.decision.id if existing_snapshot.decision else None,
                        "message": "Discount already applied",
                        "idempotent": True,
                    }, status=status.HTTP_200_OK)

                # Apply discount with idempotency key
                try:
                    res = apply_discount_and_snapshot(
                        student_user_id=student_user_id,
                        teacher_id=teacher_id,
                        course_id=course_id,
                        teo_cost=teo_cost,
                        offered_teacher_teo=offered_teacher_teo,
                        idempotency_key=idempotency_key,  # Pass key to service
                    )
                    res["idempotent"] = False
                    return Response(res, status=status.HTTP_201_CREATED)

                except IntegrityError:
                    # Race condition: another request created the same key
                    existing_snapshot = PaymentDiscountSnapshot.objects.filter(
                        idempotency_key=idempotency_key
                    ).first()

                    if existing_snapshot:
                        return Response({
                            "snapshot_id": existing_snapshot.id,
                            "pending_decision_id": existing_snapshot.decision.id if existing_snapshot.decision else None,
                            "message": "Discount already applied (race condition handled)",
                            "idempotent": True,
                        }, status=status.HTTP_200_OK)
                    else:
                        # Should not happen, but handle gracefully
                        raise
        except Exception:
            # Bubble up unexpected exceptions for visibility
            raise


class TeacherDecisionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, decision_id: int, *args, **kwargs):
        accept = kwargs.get("action") == "accept"
        result = teacher_make_decision(decision_id=decision_id, accept=accept)
        return Response(result, status=status.HTTP_200_OK)
