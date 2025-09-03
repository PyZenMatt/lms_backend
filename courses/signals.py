from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.models import Notification
from users.models import User

from .models import Course


@receiver(post_save, sender=Course)
def course_status_notification(sender, instance, created, **kwargs):
    """
    Notifiche per cambio stato del corso (approvazione/rifiuto)
    """
    if not created:
        # Il corso è stato aggiornato, verifica se è stato approvato/rifiutato
        if instance.is_approved and hasattr(instance, "_previous_approved_state"):
            # Corso approvato
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.info("creating_course_notification", extra={
                    "event": "creating_course_notification",
                    "notification_type": "course_approved",
                    "related_object_id": instance.id,
                    "teacher_id": getattr(instance.teacher, "id", None),
                })
            except Exception:
                pass

            Notification.objects.create(
                user=instance.teacher,
                message=f"🎉 Il tuo corso '{instance.title}' è stato approvato e pubblicato!",
                notification_type="course_approved",
                related_object_id=instance.id,
            )
        elif not instance.is_approved and hasattr(instance, "_previous_approved_state"):
            # Corso rifiutato (se implementato)
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.info("creating_course_notification", extra={
                    "event": "creating_course_notification",
                    "notification_type": "course_rejected",
                    "related_object_id": instance.id,
                    "teacher_id": getattr(instance.teacher, "id", None),
                })
            except Exception:
                pass

            Notification.objects.create(
                user=instance.teacher,
                message=f"❌ Il tuo corso '{instance.title}' non è stato approvato.",
                notification_type="course_rejected",
                related_object_id=instance.id,
            )


@receiver(post_save, sender=Course)
def new_course_published_notification(sender, instance, created, **kwargs):
    """
    Notifica a tutti gli studenti quando viene pubblicato un nuovo corso
    """
    if created and instance.is_approved:
        # Invia notifica a tutti gli studenti (o agli studenti interessati alla categoria)
        students = User.objects.filter(role="student", is_active=True)

        for student in students[:50]:  # Limita a 50 per non sovraccaricare
            try:
                import logging

                logger = logging.getLogger(__name__)
                logger.info("creating_course_notification", extra={
                    "event": "creating_course_notification",
                    "notification_type": "new_course_published",
                    "related_object_id": instance.id,
                    "student_id": getattr(student, "id", None),
                })
            except Exception:
                pass

            Notification.objects.create(
                user=student,
                message=f"📚 Nuovo corso disponibile: '{instance.title}' nella categoria {instance.category}!",
                notification_type="new_course_published",
                related_object_id=instance.id,
            )


def notify_course_purchase(course, buyer, seller):
    """
    Notifiche per acquisto corso (da chiamare manualmente quando qualcuno acquista)
    """
    # Notifica al compratore
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("creating_course_notification", extra={
            "event": "creating_course_notification",
            "notification_type": "course_purchased",
            "related_object_id": course.id,
            "buyer_id": getattr(buyer, "id", None),
        })
    except Exception:
        pass

    Notification.objects.create(
        user=buyer,
        message=f"✅ Hai acquistato con successo il corso '{course.title}'!",
        notification_type="course_purchased",
        related_object_id=course.id,
    )

    # Notifica al venditore
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("creating_course_notification", extra={
            "event": "creating_course_notification",
            "notification_type": "course_sold",
            "related_object_id": course.id,
            "seller_id": getattr(seller, "id", None),
        })
    except Exception:
        pass

    Notification.objects.create(
        user=seller,
        message=f"💰 Il tuo corso '{course.title}' è stato acquistato da {buyer.username}!",
        notification_type="course_sold",
        related_object_id=course.id,
    )


def notify_lesson_purchase(lesson, buyer, seller):
    """
    Notifiche per acquisto lezione (da chiamare manualmente quando qualcuno acquista)
    """
    # Notifica al compratore
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("creating_lesson_notification", extra={
            "event": "creating_lesson_notification",
            "notification_type": "lesson_purchased",
            "related_object_id": lesson.id,
            "buyer_id": getattr(buyer, "id", None),
        })
    except Exception:
        pass

    Notification.objects.create(
        user=buyer,
        message=f"✅ Hai acquistato con successo la lezione '{lesson.title}'!",
        notification_type="lesson_purchased",
        related_object_id=lesson.id,
    )

    # Notifica al venditore
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("creating_lesson_notification", extra={
            "event": "creating_lesson_notification",
            "notification_type": "lesson_sold",
            "related_object_id": lesson.id,
            "seller_id": getattr(seller, "id", None),
        })
    except Exception:
        pass

    Notification.objects.create(
        user=seller,
        message=f"💰 La tua lezione '{lesson.title}' è stata acquistata da {buyer.username}!",
        notification_type="lesson_sold",
        related_object_id=lesson.id,
    )


def notify_course_completion(course, student):
    """
    Notifica quando uno studente completa un corso
    """
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("creating_course_completion_notification", extra={
            "event": "creating_course_completion_notification",
            "notification_type": "course_completed",
            "related_object_id": course.id,
            "student_id": getattr(student, "id", None),
        })
    except Exception:
        pass

    Notification.objects.create(
        user=student,
        message=f"🎓 Congratulazioni! Hai completato il corso '{course.title}'!",
        notification_type="course_completed",
        related_object_id=course.id,
    )

    # Notifica anche al teacher
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info("creating_course_completion_notification", extra={
            "event": "creating_course_completion_notification",
            "notification_type": "system_message",
            "related_object_id": course.id,
            "teacher_id": getattr(course.teacher, "id", None),
        })
    except Exception:
        pass

    Notification.objects.create(
        user=course.teacher,
        message=f"🎉 Lo studente {student.username} ha completato il tuo corso '{course.title}'!",
        notification_type="system_message",
        related_object_id=course.id,
    )
