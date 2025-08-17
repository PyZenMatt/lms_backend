"""
Tests for Notification Service
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from notifications.models import Notification
from services.notification_service import notification_service
from services.exceptions import UserNotFoundError, TeoArtServiceException

User = get_user_model()


class NotificationServiceTestCase(TestCase):
    """Test cases for NotificationService"""
    
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
    
    def test_create_notification_success(self):
        """Test successful notification creation"""
        result = notification_service.create_notification(
            user_id=self.user1.id,
            message="Test notification message",
            notification_type="course_purchased",
            related_object_id=123
        )
        
        self.assertEqual(result['user_id'], self.user1.id)
        self.assertEqual(result['message'], "Test notification message")
        self.assertEqual(result['notification_type'], "course_purchased")
        self.assertEqual(result['related_object_id'], 123)
        self.assertFalse(result['read'])
        self.assertIn('notification_id', result)
        self.assertIn('created_at', result)
        
        # Verify notification exists in database
        notification = Notification.objects.get(id=result['notification_id'])
        self.assertEqual(notification.user, self.user1)
        self.assertEqual(notification.message, "Test notification message")
    
    def test_create_notification_user_not_found(self):
        """Test notification creation with non-existent user"""
        with self.assertRaises(UserNotFoundError):
            notification_service.create_notification(
                user_id=99999,
                message="Test message",
                notification_type="course_purchased"
            )
    
    def test_create_notification_invalid_type(self):
        """Test notification creation with invalid notification type"""
        with self.assertRaises(TeoArtServiceException):
            notification_service.create_notification(
                user_id=self.user1.id,
                message="Test message",
                notification_type="invalid_type"
            )
    
    def test_get_user_notifications(self):
        """Test getting user notifications"""
        # Create test notifications
        notification1 = Notification.objects.create(
            user=self.user1,
            message="First notification",
            notification_type="course_purchased"
        )
        notification2 = Notification.objects.create(
            user=self.user1,
            message="Second notification",
            notification_type="lesson_purchased",
            read=True
        )
        notification3 = Notification.objects.create(
            user=self.user2,
            message="Other user notification",
            notification_type="course_purchased"
        )
        
        notifications = notification_service.get_user_notifications(self.user1.id)
        
        self.assertEqual(len(notifications), 2)
        # Should be ordered by newest first
        self.assertEqual(notifications[0]['message'], "Second notification")
        self.assertEqual(notifications[1]['message'], "First notification")
    
    def test_get_user_notifications_unread_only(self):
        """Test getting only unread notifications"""
        # Create test notifications
        Notification.objects.create(
            user=self.user1,
            message="Unread notification",
            notification_type="course_purchased",
            read=False
        )
        Notification.objects.create(
            user=self.user1,
            message="Read notification",
            notification_type="lesson_purchased",
            read=True
        )
        
        notifications = notification_service.get_user_notifications(
            self.user1.id, 
            unread_only=True
        )
        
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]['message'], "Unread notification")
        self.assertFalse(notifications[0]['read'])
    
    def test_get_user_notifications_with_type_filter(self):
        """Test getting notifications with type filter"""
        # Create test notifications
        Notification.objects.create(
            user=self.user1,
            message="Course notification",
            notification_type="course_purchased"
        )
        Notification.objects.create(
            user=self.user1,
            message="Lesson notification",
            notification_type="lesson_purchased"
        )
        
        notifications = notification_service.get_user_notifications(
            self.user1.id,
            notification_type="course_purchased"
        )
        
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0]['message'], "Course notification")
        self.assertEqual(notifications[0]['notification_type'], "course_purchased")
    
    def test_get_user_notifications_with_limit(self):
        """Test getting notifications with limit"""
        # Create multiple notifications
        for i in range(5):
            Notification.objects.create(
                user=self.user1,
                message=f"Notification {i}",
                notification_type="course_purchased"
            )
        
        notifications = notification_service.get_user_notifications(
            self.user1.id,
            limit=3
        )
        
        self.assertEqual(len(notifications), 3)
    
    def test_mark_notification_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user1,
            message="Test notification",
            notification_type="course_purchased",
            read=False
        )
        
        result = notification_service.mark_notification_as_read(
            notification.id,
            self.user1.id
        )
        
        self.assertEqual(result['notification_id'], notification.id)
        self.assertTrue(result['read'])
        self.assertIn('updated_at', result)
        
        # Verify in database
        notification.refresh_from_db()
        self.assertTrue(notification.read)
    
    def test_mark_notification_as_read_wrong_user(self):
        """Test marking notification as read with wrong user"""
        notification = Notification.objects.create(
            user=self.user1,
            message="Test notification",
            notification_type="course_purchased"
        )
        
        with self.assertRaises(TeoArtServiceException):
            notification_service.mark_notification_as_read(
                notification.id,
                self.user2.id
            )
    
    def test_mark_notification_as_read_not_found(self):
        """Test marking non-existent notification as read"""
        with self.assertRaises(TeoArtServiceException):
            notification_service.mark_notification_as_read(
                99999,
                self.user1.id
            )
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read"""
        # Create test notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user1,
                message=f"Notification {i}",
                notification_type="course_purchased",
                read=False
            )
        
        # Create one read notification
        Notification.objects.create(
            user=self.user1,
            message="Already read",
            notification_type="course_purchased",
            read=True
        )
        
        result = notification_service.mark_all_notifications_as_read(self.user1.id)
        
        self.assertEqual(result['user_id'], self.user1.id)
        self.assertEqual(result['updated_count'], 3)  # Only 3 were unread
        self.assertIn('updated_at', result)
        
        # Verify all notifications are now read
        unread_count = Notification.objects.filter(user=self.user1, read=False).count()
        self.assertEqual(unread_count, 0)
    
    def test_get_unread_count(self):
        """Test getting unread notification count"""
        # Create test notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user1,
                message=f"Unread notification {i}",
                notification_type="course_purchased",
                read=False
            )
        
        # Create read notification
        Notification.objects.create(
            user=self.user1,
            message="Read notification",
            notification_type="course_purchased",
            read=True
        )
        
        result = notification_service.get_unread_count(self.user1.id)
        
        self.assertEqual(result['user_id'], self.user1.id)
        self.assertEqual(result['unread_count'], 3)
    
    def test_delete_notification(self):
        """Test deleting notification"""
        notification = Notification.objects.create(
            user=self.user1,
            message="Test notification",
            notification_type="course_purchased"
        )
        
        result = notification_service.delete_notification(
            notification.id,
            self.user1.id
        )
        
        self.assertEqual(result['notification_id'], notification.id)
        self.assertEqual(result['user_id'], self.user1.id)
        self.assertTrue(result['deleted'])
        self.assertIn('deleted_at', result)
        
        # Verify notification is deleted
        with self.assertRaises(Notification.DoesNotExist):
            Notification.objects.get(id=notification.id)
    
    def test_delete_notification_wrong_user(self):
        """Test deleting notification with wrong user"""
        notification = Notification.objects.create(
            user=self.user1,
            message="Test notification",
            notification_type="course_purchased"
        )
        
        with self.assertRaises(TeoArtServiceException):
            notification_service.delete_notification(
                notification.id,
                self.user2.id
            )
    
    def test_delete_notification_not_found(self):
        """Test deleting non-existent notification"""
        with self.assertRaises(TeoArtServiceException):
            notification_service.delete_notification(
                99999,
                self.user1.id
            )
