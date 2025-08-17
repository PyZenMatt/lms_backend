"""
TeoCoin Discount Notification Service

Handles notifications for the TeoCoin discount system.
Sends notifications to teachers and students about discount requests and decisions.
"""

import logging
from typing import Dict, Optional
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

from notifications.models import Notification
from users.models import User

logger = logging.getLogger(__name__)


class TeoCoinDiscountNotificationService:
    """Service for handling TeoCoin discount system notifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def notify_teacher_discount_pending(
        self, 
        teacher: User, 
        student: User, 
        course_title: str,
        discount_percent: int,
        teo_cost: float,
        teacher_bonus: float,
        request_id: int,
        expires_at: timezone.datetime
    ) -> bool:
        """
        Notify teacher that a student received a discount and they need to choose EUR vs TEO
        
        Args:
            teacher: Teacher user
            student: Student user  
            course_title: Course title
            discount_percent: Discount percentage
            teo_cost: TEO cost from student
            teacher_bonus: TEO bonus for teacher
            request_id: Discount request ID
            expires_at: Request expiration time
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate time remaining
            time_remaining = expires_at - timezone.now()
            hours_remaining = max(0, int(time_remaining.total_seconds() / 3600))
            
            # Create in-app notification
            message = (
                f"🎓 Student {student.get_full_name() or student.username} got a {discount_percent}% "
                f"discount on '{course_title}' and is enrolled! \n\n"
                f"💰 Choose your payment: \n"
                f"🪙 Accept TEO: {teo_cost:.2f} TEO + {teacher_bonus:.2f} bonus = {teo_cost + teacher_bonus:.2f} TEO total (for staking)\n"
                f"💰 Keep EUR: Full EUR commission (platform absorbs discount)\n\n"
                f"⏰ Decide within {hours_remaining} hours or EUR will be chosen automatically."
            )
            
            notification = Notification.objects.create(
                user=teacher,
                message=message,
                notification_type='teocoin_discount_pending',
                related_object_id=request_id
            )
            
            # Send email notification if enabled
            if getattr(settings, 'SEND_DISCOUNT_EMAILS', True):
                self._send_teacher_email_notification(
                    teacher=teacher,
                    student=student,
                    course_title=course_title,
                    discount_percent=discount_percent,
                    teo_cost=teo_cost,
                    teacher_bonus=teacher_bonus,
                    hours_remaining=hours_remaining
                )
            
            self.logger.info(f"Teacher discount notification sent to {teacher.username} for request {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send teacher notification: {e}")
            return False
    
    def notify_student_teacher_decision(
        self,
        student: User,
        teacher: User,
        course_title: str,
        decision: str,  # 'accepted' or 'declined'
        teo_amount: Optional[float] = None
    ) -> bool:
        """
        Notify student of teacher's EUR vs TEO decision
        
        Args:
            student: Student user
            teacher: Teacher user
            course_title: Course title
            decision: 'accepted' or 'declined'
            teo_amount: TEO amount if accepted
            
        Returns:
            bool: Success status
        """
        try:
            if decision == 'accepted':
                message = (
                    f"🎉 Great news! Teacher {teacher.get_full_name() or teacher.username} "
                    f"accepted your {teo_amount:.2f} TEO payment for '{course_title}'!\n\n"
                    f"✅ Your discount is confirmed\n"
                    f"🪙 Your TEO tokens are being used for teacher staking benefits\n"
                    f"📚 You have full access to the course"
                )
                notification_type = 'teocoin_discount_accepted'
            else:
                message = (
                    f"📊 Teacher {teacher.get_full_name() or teacher.username} chose EUR payment "
                    f"for '{course_title}'\n\n"
                    f"✅ Your discount is still confirmed (platform absorbed the cost)\n"
                    f"🪙 Your TEO tokens have been returned\n"
                    f"📚 You have full access to the course"
                )
                notification_type = 'teocoin_discount_rejected'
            
            notification = Notification.objects.create(
                user=student,
                message=message,
                notification_type=notification_type
            )
            
            self.logger.info(f"Student decision notification sent to {student.username}: {decision}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send student decision notification: {e}")
            return False
    
    def notify_teacher_timeout_warning(
        self,
        teacher: User,
        student: User,
        course_title: str,
        request_id: int,
        minutes_remaining: int
    ) -> bool:
        """
        Send timeout warning to teacher
        
        Args:
            teacher: Teacher user
            student: Student user
            course_title: Course title
            request_id: Request ID
            minutes_remaining: Minutes until timeout
            
        Returns:
            bool: Success status
        """
        try:
            message = (
                f"⏰ URGENT: Only {minutes_remaining} minutes left to choose your payment method!\n\n"
                f"Student: {student.get_full_name() or student.username}\n"
                f"Course: '{course_title}'\n\n"
                f"If you don't choose, you'll automatically receive full EUR commission."
            )
            
            notification = Notification.objects.create(
                user=teacher,
                message=message,
                notification_type='teocoin_discount_pending',
                related_object_id=request_id
            )
            
            # Send urgent email
            if getattr(settings, 'SEND_URGENT_EMAILS', True):
                self._send_urgent_email(teacher, course_title, minutes_remaining)
            
            self.logger.info(f"Timeout warning sent to {teacher.username} for request {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send timeout warning: {e}")
            return False
    
    def notify_request_expired(
        self,
        teacher: User,
        student: User,
        course_title: str,
        request_id: int
    ) -> bool:
        """
        Notify about expired request (auto-EUR selection)
        
        Args:
            teacher: Teacher user
            student: Student user
            course_title: Course title
            request_id: Request ID
            
        Returns:
            bool: Success status
        """
        try:
            # Notify teacher
            teacher_message = (
                f"⏰ Time expired for TeoCoin discount decision on '{course_title}'\n\n"
                f"✅ You automatically received full EUR commission\n"
                f"💰 Platform absorbed the student's discount cost\n"
                f"🪙 Student's TEO tokens were returned"
            )
            
            Notification.objects.create(
                user=teacher,
                message=teacher_message,
                notification_type='teocoin_discount_expired',
                related_object_id=request_id
            )
            
            # Notify student
            student_message = (
                f"⏰ Teacher didn't respond in time for '{course_title}'\n\n"
                f"✅ Your discount is still confirmed\n"
                f"💰 Teacher received full EUR commission\n"
                f"🪙 Your TEO tokens have been returned\n"
                f"📚 You have full access to the course"
            )
            
            Notification.objects.create(
                user=student,
                message=student_message,
                notification_type='teocoin_discount_expired'
            )
            
            self.logger.info(f"Expiration notifications sent for request {request_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send expiration notifications: {e}")
            return False
    
    def create_teacher_staking_reminder(
        self,
        teacher: User,
        teo_amount: float
    ) -> bool:
        """
        Remind teacher about staking benefits after accepting TEO
        
        Args:
            teacher: Teacher user
            teo_amount: TEO amount received
            
        Returns:
            bool: Success status
        """
        try:
            message = (
                f"🪙 You received {teo_amount:.2f} TEO tokens!\n\n"
                f"💡 Staking Benefits:\n"
                f"• Stake your TEO to increase commission rates\n"
                f"• Higher tiers = higher % on all future sales\n"
                f"• Compound your TEO earnings over time\n\n"
                f"🚀 Visit the Staking section to maximize your earnings!"
            )
            
            notification = Notification.objects.create(
                user=teacher,
                message=message,
                notification_type='bonus_received'
            )
            
            self.logger.info(f"Staking reminder sent to {teacher.username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send staking reminder: {e}")
            return False
    
    # ========== PRIVATE METHODS ==========
    
    def _send_teacher_email_notification(
        self,
        teacher: User,
        student: User,
        course_title: str,
        discount_percent: int,
        teo_cost: float,
        teacher_bonus: float,
        hours_remaining: int
    ):
        """Send email notification to teacher"""
        try:
            subject = f"Student discount decision needed - {course_title}"
            
            context = {
                'teacher_name': teacher.get_full_name() or teacher.username,
                'student_name': student.get_full_name() or student.username,
                'course_title': course_title,
                'discount_percent': discount_percent,
                'teo_cost': teo_cost,
                'teacher_bonus': teacher_bonus,
                'total_teo': teo_cost + teacher_bonus,
                'hours_remaining': hours_remaining,
                'dashboard_url': f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/teacher/dashboard"
            }
            
            html_message = render_to_string('emails/teacher_discount_decision.html', context)
            plain_message = render_to_string('emails/teacher_discount_decision.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[teacher.email],
                html_message=html_message,
                fail_silently=False
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send teacher email: {e}")
    
    def _send_urgent_email(self, teacher: User, course_title: str, minutes_remaining: int):
        """Send urgent timeout warning email"""
        try:
            subject = f"URGENT: {minutes_remaining} minutes left - {course_title}"
            
            message = (
                f"Dear {teacher.get_full_name() or teacher.username},\n\n"
                f"You have only {minutes_remaining} minutes left to choose your payment method "
                f"for the discount request on '{course_title}'.\n\n"
                f"Please visit your dashboard to make your choice:\n"
                f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/teacher/dashboard\n\n"
                f"If you don't choose, you'll automatically receive full EUR commission."
            )
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[teacher.email],
                fail_silently=False
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send urgent email: {e}")


# Singleton instance
teocoin_notification_service = TeoCoinDiscountNotificationService()
