from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from rewards.models import BlockchainTransaction
from rewards.serializers import BlockchainTransactionSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_transactions_list(request):
    """
    Lista delle transazioni blockchain per dashboard admin
    """
    try:
        # Parametri di filtro
        limit = request.GET.get('limit', 50)
        status_filter = request.GET.get('status')
        type_filter = request.GET.get('type')
        
        # Query base
        queryset = BlockchainTransaction.objects.select_related('user').order_by('-created_at')
        
        # Filtri
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if type_filter:
            queryset = queryset.filter(transaction_type=type_filter)
        
        # Limita risultati
        transactions = queryset[:int(limit)]
        
        # Serializza
        serializer = BlockchainTransactionSerializer(transactions, many=True)
        
        return Response(serializer.data)
    
    except Exception as e:
        logger.error(f"Error fetching admin transactions: {e}")
        return Response(
            {'error': 'Errore nel recuperare le transazioni'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_transactions_stats(request):
    """
    Statistiche delle transazioni per dashboard admin
    """
    try:
        # Statistiche generali
        stats = BlockchainTransaction.objects.aggregate(
            total_count=Count('id'),
            completed_count=Count('id', filter=Q(status='completed')),
            pending_count=Count('id', filter=Q(status='pending')),
            failed_count=Count('id', filter=Q(status='failed')),
            total_volume=Sum('amount', filter=Q(status='completed'))
        )
        
        # Statistiche per tipo di transazione (ultimi 30 giorni)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_stats = BlockchainTransaction.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('transaction_type').annotate(
            count=Count('id'),
            volume=Sum('amount', filter=Q(status='completed'))
        ).order_by('-count')
        
        # Transazioni fallite recenti (ultime 24 ore)
        yesterday = timezone.now() - timedelta(hours=24)
        recent_failures = BlockchainTransaction.objects.filter(
            status='failed',
            created_at__gte=yesterday
        ).count()
        
        return Response({
            **stats,
            'total_volume': float(stats['total_volume'] or 0),
            'recent_failures_24h': recent_failures,
            'transaction_types': list(recent_stats)
        })
    
    except Exception as e:
        logger.error(f"Error fetching admin transaction stats: {e}")
        return Response(
            {'error': 'Errore nel recuperare le statistiche'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_retry_transaction(request, transaction_id):
    """
    Ritenta una transazione fallita (solo per admin)
    """
    try:
        transaction = BlockchainTransaction.objects.get(id=transaction_id)
        
        if transaction.status != 'failed':
            return Response(
                {'error': 'Solo le transazioni fallite possono essere ritentate'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reset status per permettere il re-processing
        transaction.status = 'pending'
        transaction.error_message = None
        transaction.save()
        
        # Log dell'azione admin
        logger.info(f"Admin {request.user.username} retrying transaction {transaction_id}")
        
        return Response({'message': 'Transazione rimessa in coda per il processing'})
    
    except BlockchainTransaction.DoesNotExist:
        return Response(
            {'error': 'Transazione non trovata'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error retrying transaction {transaction_id}: {e}")
        return Response(
            {'error': 'Errore nel ritentare la transazione'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_user_transactions(request, user_id):
    """
    Transazioni per uno specifico utente (per supporto clienti)
    """
    try:
        from users.models import User
        user = User.objects.get(id=user_id)
        
        transactions = BlockchainTransaction.objects.filter(
            user=user
        ).order_by('-created_at')[:20]
        
        serializer = BlockchainTransactionSerializer(transactions, many=True)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'transactions': serializer.data
        })
    
    except User.DoesNotExist:
        return Response(
            {'error': 'Utente non trovato'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error fetching user transactions: {e}")
        return Response(
            {'error': 'Errore nel recuperare le transazioni utente'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
