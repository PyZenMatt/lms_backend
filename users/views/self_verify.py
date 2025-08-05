from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from users.models import User

class SelfVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.is_approved:
            return Response({'detail': 'Utente già verificato.'}, status=status.HTTP_200_OK)
        user.is_approved = True
        user.save()
        return Response({'detail': 'Utente verificato con successo.'}, status=status.HTTP_200_OK)
