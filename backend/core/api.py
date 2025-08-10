from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rewards.models import BlockchainTransaction 
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from core.serializers import BlockchainTransactionSerializer
from courses.models import Lesson 
from courses.serializers import LessonSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    user = request.user
    
    # Get blockchain balance instead of database balance
    blockchain_balance = "0"
    if user.wallet_address:
        try:
            from blockchain.views import teocoin_service
            blockchain_balance = str(teocoin_service.get_balance(user.wallet_address))
        except:
            blockchain_balance = "0"
    
    return Response({
        'user': {
            'username': user.username,
            'blockchain_balance': blockchain_balance,
            'wallet_address': user.wallet_address,
            'role': user.role
        },
        'lessons': LessonSerializer(
            Lesson.objects.filter(students=user).select_related('teacher'),
            many=True
        ).data,
        'transactions': BlockchainTransactionSerializer(
            BlockchainTransaction.objects.filter(user=user).order_by('-created_at')[:10],
            many=True
        ).data,
        'notifications': NotificationSerializer(
            Notification.objects.filter(user=user).order_by('-created_at')[:5], 
            many=True
        ).data
    })
