"""
Test TeoCoin notification alignment
"""
from django.core.management.base import BaseCommand
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from notifications.services import teocoin_notification_service
from users.models import User
from courses.models import Course
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Test TEO notification alignment with structured data'

    def handle(self, *args, **options):
        self.stdout.write("=== Testing TEO Notification Serialization ===")
        
        # Find existing TEO notifications
        notifications = Notification.objects.filter(
            notification_type__in=['teocoin_discount_pending', 'teocoin_discount_pending_urgent']
        ).order_by('-id')[:5]
        
        self.stdout.write(f"Found {notifications.count()} existing TEO notifications")
        
        for notif in notifications:
            self.stdout.write(f"\n--- Notification {notif.id} ({notif.notification_type}) ---")
            
            # Test serializer
            serializer = NotificationSerializer(notif)
            data = serializer.data
            
            self.stdout.write(f"discount_eur: {data.get('discount_eur')}")
            self.stdout.write(f"offered_teacher_teo: {data.get('offered_teacher_teo')}")
            self.stdout.write(f"decision_id: {data.get('decision_id')}")
            self.stdout.write(f"tier: {data.get('tier')}")
            self.stdout.write(f"expires_at: {data.get('expires_at')}")
            
            # Check if extra_data is populated
            if hasattr(notif, 'extra_data') and notif.extra_data:
                self.stdout.write(f"extra_data: {notif.extra_data}")
            else:
                self.stdout.write("extra_data: None")

        # Test creating a new notification
        self.stdout.write("\n=== Testing New Notification Creation ===")
        
        teacher = User.objects.filter(role='teacher').first()
        student = User.objects.filter(role='student').first()
        course = Course.objects.filter(teacher=teacher).first() if teacher else None
        
        if not all([teacher, student, course]):
            self.stdout.write("Skipping notification creation test - missing required objects")
            return
        
        self.stdout.write(f"Creating test notification for teacher {teacher.username}")
        
        # Create a pending notification
        success = teocoin_notification_service.notify_teacher_discount_pending(
            teacher=teacher,
            student=student,
            course_title=course.title,
            discount_percent=10,
            teo_cost=100.0,
            teacher_bonus=25.0,
            request_id=999999,
            expires_at=timezone.now() + timedelta(hours=24),
            offered_teacher_teo=125.0,
            decision_id=888888
        )
        
        if success:
            # Find the created notification
            test_notif = Notification.objects.filter(
                user=teacher,
                notification_type='teocoin_discount_pending',
                related_object_id=888888
            ).first()
            
            if test_notif:
                self.stdout.write(self.style.SUCCESS(f"✅ Created test notification {test_notif.id}"))
                
                # Test serialization
                serializer = NotificationSerializer(test_notif)
                data = serializer.data
                
                self.stdout.write(f"discount_eur: {data.get('discount_eur')} (expected: 10)")
                self.stdout.write(f"offered_teacher_teo: {data.get('offered_teacher_teo')} (expected: 125.00000000)")
                self.stdout.write(f"decision_id: {data.get('decision_id')} (expected: 888888)")
                
                # Clean up
                test_notif.delete()
                self.stdout.write("🧹 Cleaned up test notification")
            else:
                self.stdout.write(self.style.ERROR("❌ Test notification not found"))
        else:
            self.stdout.write(self.style.ERROR("❌ Failed to create test notification"))

        self.stdout.write(self.style.SUCCESS("\n✅ All tests completed"))
