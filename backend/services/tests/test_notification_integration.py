"""
Integration tests for notification views using NotificationService
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from notifications.models import Notification

User = get_user_model()


class NotificationViewsIntegrationTestCase(TestCase):
    """Integration tests for notification views"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass',
            role='student',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass',
            role='teacher',
            first_name='User',
            last_name='Two'
        )
        
        # Create API client
        self.client = APIClient()
        
        # Create test notifications
        self.notification1 = Notification.objects.create(
            user=self.user1,
            message="Test notification 1",
            notification_type="course_purchased",
            read=False
        )
        
        self.notification2 = Notification.objects.create(
            user=self.user1,
            message="Test notification 2",
            notification_type="lesson_purchased",
            read=True
        )
        
        self.notification3 = Notification.objects.create(
            user=self.user2,
            message="Other user notification",
            notification_type="course_purchased",
            read=False
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user authentication"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_notification_list_view(self):
        """Test listing notifications"""
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('notification-list')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only user1's notifications
        
        # Check notification data
        notification_messages = [n['message'] for n in response.data]
        self.assertIn("Test notification 1", notification_messages)
        self.assertIn("Test notification 2", notification_messages)
    
    def test_notification_list_view_with_filters(self):
        """Test listing notifications with filters"""
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Test unread filter
        url = reverse('notification-list')
        response = self.client.get(url, {'read': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], "Test notification 1")
        self.assertFalse(response.data[0]['read'])
        
        # Test notification type filter
        response = self.client.get(url, {'notification_type': 'course_purchased'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['notification_type'], 'course_purchased')
    
    def test_notification_unread_count_view(self):
        """Test getting unread notification count"""
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('notification-unread-count')
        response = self.client.get(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unread_count'], 1)  # Only 1 unread notification for user1
    
    def test_notification_mark_read_view(self):
        """Test marking notification as read"""
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('notification-mark-read', kwargs={'notification_id': self.notification1.id})
        response = self.client.patch(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertTrue(response.data['notification']['read'])
        
        # Verify in database
        self.notification1.refresh_from_db()
        self.assertTrue(self.notification1.read)
    
    def test_notification_mark_read_wrong_user(self):
        """Test marking notification as read with wrong user"""
        # Authenticate user2
        token = self.get_jwt_token(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Try to mark user1's notification as read
        url = reverse('notification-mark-read', kwargs={'notification_id': self.notification1.id})
        response = self.client.patch(url)
        
        # Should fail
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_notification_mark_all_read_view(self):
        """Test marking all notifications as read"""
        # Create another unread notification for user1
        Notification.objects.create(
            user=self.user1,
            message="Another unread",
            notification_type="course_purchased",
            read=False
        )
        
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('notification-mark-all-read')
        response = self.client.post(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['updated_count'], 2)  # 2 unread notifications were updated
        
        # Verify all user1's notifications are now read
        unread_count = Notification.objects.filter(user=self.user1, read=False).count()
        self.assertEqual(unread_count, 0)
    
    def test_notification_delete_view(self):
        """Test deleting a notification"""
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Make request
        url = reverse('notification-delete', kwargs={'notification_id': self.notification1.id})
        response = self.client.delete(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify notification is deleted
        with self.assertRaises(Notification.DoesNotExist):
            Notification.objects.get(id=self.notification1.id)
    
    def test_notification_delete_wrong_user(self):
        """Test deleting notification with wrong user"""
        # Authenticate user2
        token = self.get_jwt_token(self.user2)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Try to delete user1's notification
        url = reverse('notification-delete', kwargs={'notification_id': self.notification1.id})
        response = self.client.delete(url)
        
        # Should fail
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Verify notification still exists
        self.assertTrue(Notification.objects.filter(id=self.notification1.id).exists())
    
    def test_notification_clear_all_view(self):
        """Test clearing all notifications"""
        # Authenticate user
        token = self.get_jwt_token(self.user1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        # Check initial count
        initial_count = Notification.objects.filter(user=self.user1).count()
        self.assertEqual(initial_count, 2)
        
        # Make request
        url = reverse('notification-clear-all')
        response = self.client.delete(url)
        
        # Check response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify all user1's notifications are deleted
        remaining_count = Notification.objects.filter(user=self.user1).count()
        self.assertEqual(remaining_count, 0)
        
        # Verify user2's notifications are still there
        user2_count = Notification.objects.filter(user=self.user2).count()
        self.assertEqual(user2_count, 1)
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication"""
        # No authentication
        urls = [
            reverse('notification-list'),
            reverse('notification-unread-count'),
            reverse('notification-mark-read', kwargs={'notification_id': self.notification1.id}),
            reverse('notification-mark-all-read'),
            reverse('notification-delete', kwargs={'notification_id': self.notification1.id}),
            reverse('notification-clear-all'),
        ]
        
        for url in urls:
            for method in ['get', 'post', 'patch', 'delete']:
                if hasattr(self.client, method):
                    response = getattr(self.client, method)(url)
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
