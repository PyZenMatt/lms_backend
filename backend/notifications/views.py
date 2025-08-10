from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as df_filters
from rest_framework.generics import UpdateAPIView

# Service Layer imports
from services.notification_service import notification_service
from services.exceptions import TeoArtServiceException, UserNotFoundError
import logging

logger = logging.getLogger(__name__)

class NotificationFilter(df_filters.FilterSet):
    created_after = df_filters.DateTimeFilter(
    field_name='created_at', 
    lookup_expr='gte',
    help_text="Filtra notifiche create dopo questa data/ora (YYYY-MM-DD HH:MM:SS)"
    )

    class Meta:
        model = Notification
        fields = ['notification_type', 'read']

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user notifications with filtering options"""
        try:
            # Extract filter parameters
            notification_type = request.GET.get('notification_type')
            read_filter = request.GET.get('read')
            created_after = request.GET.get('created_after')
            limit = request.GET.get('limit')
            
            # Convert read filter to boolean
            unread_only = None
            if read_filter is not None:
                unread_only = read_filter.lower() == 'false'
            
            # Convert limit to int
            if limit:
                try:
                    limit = int(limit)
                except ValueError:
                    limit = None
            
            # Use NotificationService
            notifications_data = notification_service.get_user_notifications(
                user_id=request.user.id,
                notification_type=notification_type,
                unread_only=unread_only,
                limit=limit
            )
            
            # Convert service data to model instances for serialization
            notification_ids = [n['id'] for n in notifications_data]  # Use 'id', not 'notification_id'
            notifications = Notification.objects.filter(id__in=notification_ids).order_by('-created_at')
            
            # Apply additional filters if needed
            if created_after:
                try:
                    from django.utils import timezone
                    from datetime import datetime
                    created_after_dt = timezone.make_aware(datetime.fromisoformat(created_after.replace('Z', '+00:00')))
                    notifications = notifications.filter(created_at__gte=created_after_dt)
                except ValueError:
                    pass
            
            # Serialize and return
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.warning(f"NotificationListView service failed, falling back to old logic: {str(e)}")
            # Fallback to old logic
            queryset = Notification.objects.filter(user=request.user).order_by('-created_at')
            
            # Apply manual filters
            if notification_type:
                queryset = queryset.filter(notification_type=notification_type)
            if read_filter is not None:
                queryset = queryset.filter(read=read_filter.lower() == 'true')
            if created_after:
                try:
                    from django.utils import timezone
                    from datetime import datetime
                    created_after_dt = timezone.make_aware(datetime.fromisoformat(created_after.replace('Z', '+00:00')))
                    queryset = queryset.filter(created_at__gte=created_after_dt)
                except ValueError:
                    pass
            
            serializer = NotificationSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        """Mark a notification as read"""
        try:
            # Use NotificationService
            result = notification_service.mark_notification_as_read(
                notification_id=notification_id,
                user_id=request.user.id
            )
            
            # Get updated notification for response
            notification = Notification.objects.get(id=notification_id)
            serializer = NotificationSerializer(notification)
            
            return Response({
                'message': 'Notifica marcata come letta',
                'notification': serializer.data
            }, status=status.HTTP_200_OK)
            
        except (TeoArtServiceException, UserNotFoundError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.warning(f"NotificationMarkReadView service failed, falling back to old logic: {str(e)}")
            # Fallback to old logic
            try:
                notification = get_object_or_404(Notification, id=notification_id, user=request.user)
                notification.read = True
                notification.save()
                
                serializer = NotificationSerializer(notification)
                return Response({
                    'message': 'Notifica marcata come letta',
                    'notification': serializer.data
                }, status=status.HTTP_200_OK)
            except Exception as fallback_error:
                return Response({'error': str(fallback_error)}, status=status.HTTP_400_BAD_REQUEST)

class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Mark all user notifications as read"""
        try:
            # Use NotificationService
            result = notification_service.mark_all_notifications_as_read(request.user.id)
            
            return Response({
                'message': 'Tutte le notifiche sono state marcate come lette',
                'updated_count': result['updated_count']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.warning(f"NotificationMarkAllReadView service failed, falling back to old logic: {str(e)}")
            # Fallback to old logic
            try:
                updated_count = Notification.objects.filter(user=request.user, read=False).update(read=True)
                return Response({
                    'message': 'Tutte le notifiche sono state marcate come lette',
                    'updated_count': updated_count
                }, status=status.HTTP_200_OK)
            except Exception as fallback_error:
                return Response({'error': str(fallback_error)}, status=status.HTTP_400_BAD_REQUEST)

class NotificationClearAllView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request):
        """Delete all user notifications"""
        try:
            # Get count first using service (get all notifications)
            notifications_data = notification_service.get_user_notifications(request.user.id)
            total_count = len(notifications_data)
            
            # Delete all notifications (we'll implement batch delete in the future)
            # For now, use direct DB operation as fallback since service doesn't have bulk delete
            deleted_count = Notification.objects.filter(user=request.user).count()
            Notification.objects.filter(user=request.user).delete()
            
            return Response({
                'message': f'{deleted_count} notifiche sono state eliminate'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.warning(f"NotificationClearAllView service failed, falling back to old logic: {str(e)}")
            # Fallback to old logic
            try:
                count = Notification.objects.filter(user=request.user).count()
                Notification.objects.filter(user=request.user).delete()
                return Response({
                    'message': f'{count} notifiche sono state eliminate'
                }, status=status.HTTP_200_OK)
            except Exception as fallback_error:
                return Response({'error': str(fallback_error)}, status=status.HTTP_400_BAD_REQUEST)

class NotificationDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, notification_id):
        """Delete a specific notification"""
        try:
            # Use NotificationService
            result = notification_service.delete_notification(
                notification_id=notification_id,
                user_id=request.user.id
            )
            
            return Response({
                'message': 'Notifica eliminata con successo',
                'notification_id': result['notification_id']
            }, status=status.HTTP_200_OK)
            
        except (TeoArtServiceException, UserNotFoundError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.warning(f"NotificationDeleteView service failed, falling back to old logic: {str(e)}")
            # Fallback to old logic
            try:
                notification = get_object_or_404(Notification, id=notification_id, user=request.user)
                notification.delete()
                return Response({
                    'message': 'Notifica eliminata con successo',
                    'notification_id': notification_id
                }, status=status.HTTP_200_OK)
            except Exception as fallback_error:
                return Response({'error': str(fallback_error)}, status=status.HTTP_400_BAD_REQUEST)

class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get count of unread notifications for the user"""
        try:
            # Use NotificationService
            result = notification_service.get_unread_count(request.user.id)
            
            return Response({
                'unread_count': result['unread_count']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.warning(f"NotificationUnreadCountView service failed, falling back to old logic: {str(e)}")
            # Fallback to old logic
            try:
                unread_count = Notification.objects.filter(user=request.user, read=False).count()
                return Response({
                    'unread_count': unread_count
                }, status=status.HTTP_200_OK)
            except Exception as fallback_error:
                return Response({'error': str(fallback_error)}, status=status.HTTP_400_BAD_REQUEST)
