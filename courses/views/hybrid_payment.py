from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from decimal import Decimal
from services.payment_service import payment_service
from services.exceptions import (
    TeoArtServiceException, 
    UserNotFoundError, 
    CourseNotFoundError,
    InsufficientTeoCoinsError
)

class HybridPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        """
        Initiate hybrid payment: deduct TeoCoin for discount, return Stripe intent for remainder.
        """
        try:
            teocoin_to_spend = Decimal(request.data.get('teocoin_to_spend', '0'))
            wallet_address = request.data.get('wallet_address')
            if not teocoin_to_spend or not wallet_address:
                return Response({"error": "teocoin_to_spend and wallet_address required"}, status=400)
            result = payment_service.create_hybrid_payment_intent(
                user_id=request.user.id,
                course_id=course_id,
                teocoin_to_spend=teocoin_to_spend,
                wallet_address=wallet_address
            )
            return Response(result, status=200)
        except (UserNotFoundError, CourseNotFoundError, TeoArtServiceException, InsufficientTeoCoinsError) as e:
            return Response({"error": str(e)}, status=getattr(e, 'status_code', 400))
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def put(self, request, course_id):
        """
        Complete hybrid payment after Stripe payment success.
        """
        try:
            payment_intent_id = request.data.get('payment_intent_id')
            if not payment_intent_id:
                return Response({"error": "payment_intent_id required"}, status=400)
            result = payment_service.process_successful_hybrid_payment(
                payment_intent_id=payment_intent_id,
                course_id=course_id,
                user_id=request.user.id
            )
            return Response(result, status=200)
        except (UserNotFoundError, CourseNotFoundError, TeoArtServiceException) as e:
            return Response({"error": str(e)}, status=getattr(e, 'status_code', 400))
        except Exception as e:
            return Response({"error": str(e)}, status=500)
