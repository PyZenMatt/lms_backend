from rest_framework import status, permissions, views
from rest_framework.response import Response
from decimal import Decimal

from rewards.services.transaction_services import (
    apply_discount_and_snapshot,
    teacher_make_decision,
)


class ApplyDiscountView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data
        res = apply_discount_and_snapshot(
            student_user_id=int(data["student_user_id"]),
            teacher_id=int(data["teacher_id"]),
            course_id=int(data["course_id"]),
            teo_cost=Decimal(str(data["teo_cost"])),
            offered_teacher_teo=Decimal(str(data.get("offered_teacher_teo", "0")))
        )
        return Response(res, status=status.HTTP_201_CREATED)


class TeacherDecisionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, decision_id: int, *args, **kwargs):
        accept = kwargs.get("action") == "accept"
        result = teacher_make_decision(decision_id=decision_id, accept=accept)
        return Response(result, status=status.HTTP_200_OK)
