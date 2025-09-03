"""
Script di debug per creare dati minimi per uno sconto TeoCoin, creare uno snapshot,
chiamare il servizio di notifica e stampare i payload serializzati.
Eseguire con:
python3 manage.py shell -c "exec(open('backend/scripts/debug_discount_run.py').read())"
"""

import json
from decimal import Decimal
from django.utils import timezone

from users.models import User
from courses.models import Course
from rewards.models import PaymentDiscountSnapshot
from services.discount_calc import compute_discount_breakdown
from notifications.serializers import NotificationSerializer
from notifications.models import Notification
from rewards.serializers import PaymentDiscountSnapshotSerializer
from notifications.services import teocoin_notification_service


def ensure_user(username, email, is_teacher=False):
    user, created = User.objects.get_or_create(username=username, defaults={
        'email': email,
        'is_active': True,
    })
    # Ensure teacher_profile stub if teacher
    if is_teacher:
        tp = getattr(user, 'teacher_profile', None)
        if tp is None:
            # best-effort: skip creating complex related objects; many codepaths handle missing profile
            pass
    return user


def ensure_course(title, teacher, price=Decimal('100.00')):
    course, created = Course.objects.get_or_create(title=title, defaults={
        'teacher': teacher,
        'price_eur': price,
        'is_approved': True,
    })
    # ensure teacher relation
    if course.teacher is None:
        course.teacher = teacher
        course.save()
    return course


def run():
    print('\n--- debug_discount_run START ---')
    # Create minimal users
    teacher = ensure_user('teacher_debug', 'teacher_debug@example.com', is_teacher=True)
    student = ensure_user('student_debug', 'student_debug@example.com')

    # Create a course
    course = ensure_course('Debug Course', teacher, price=Decimal('200.00'))

    # Parameters for discount
    order_id = 'debug-order-1'
    price_eur = course.price_eur
    discount_percent = 15

    # Resolve tier - leave as None so compute uses defaults
    tier = None

    breakdown = compute_discount_breakdown(
        price_eur=price_eur,
        discount_percent=Decimal(str(discount_percent)),
        tier=tier,
        accept_teo=False,
        accept_ratio=None,
    )

    print('\nComputed breakdown (accept_teo=False):')
    print(json.dumps(breakdown, default=str, indent=2))

    # Compute offered preview (teacher accepts full TEO)
    offered = compute_discount_breakdown(
        price_eur=price_eur,
        discount_percent=Decimal(str(discount_percent)),
        tier=tier,
        accept_teo=True,
        accept_ratio=Decimal('1'),
    )

    print('\nComputed offered breakdown (accept_teo=True, accept_ratio=1):')
    print(json.dumps(offered, default=str, indent=2))

    # Create snapshot (idempotent)
    try:
        from rewards.services.transaction_services import get_or_create_payment_snapshot

        snap, created = get_or_create_payment_snapshot(order_id=order_id, defaults={
            'course': course,
            'student': student,
            'teacher': teacher,
            'price_eur': price_eur,
            'discount_percent': int(discount_percent),
            'student_pay_eur': breakdown.get('student_pay_eur'),
            'teacher_eur': breakdown.get('teacher_eur'),
            'platform_eur': breakdown.get('platform_eur'),
            'teacher_teo': breakdown.get('teacher_teo'),
            'platform_teo': breakdown.get('platform_teo'),
            'absorption_policy': breakdown.get('absorption_policy', 'none'),
            'teacher_accepted_teo': breakdown.get('teacher_teo', 0),
            'tier_name': None,
        }, source='local')
    except Exception:
        snap, created = PaymentDiscountSnapshot.objects.get_or_create(
            order_id=order_id,
            defaults={
                'course': course,
                'student': student,
                'teacher': teacher,
                'price_eur': price_eur,
                'discount_percent': int(discount_percent),
                'student_pay_eur': breakdown.get('student_pay_eur'),
                'teacher_eur': breakdown.get('teacher_eur'),
                'platform_eur': breakdown.get('platform_eur'),
                'teacher_teo': breakdown.get('teacher_teo'),
                'platform_teo': breakdown.get('platform_teo'),
                'absorption_policy': breakdown.get('absorption_policy', 'none'),
                'teacher_accepted_teo': breakdown.get('teacher_teo', 0),
                'tier_name': None,
            }
        )

    print('\nSnapshot created: id=', getattr(snap, 'id', None), ' created=', created)
    print(json.dumps(PaymentDiscountSnapshotSerializer(snap).data, default=str, indent=2))

    # Call notification service WITHOUT passing offered_teacher_teo to test fallback
    expires_at = timezone.now() + timezone.timedelta(hours=24)
    ok = teocoin_notification_service.notify_teacher_discount_pending(
        teacher=teacher,
        student=student,
        course_title=course.title,
        discount_percent=discount_percent,
        teo_cost=float(breakdown.get('teacher_teo') or 0),
        teacher_bonus=0.0,
        request_id=snap.id,
        expires_at=expires_at,
        offered_teacher_teo=None,
    )

    print('\nNotification service returned:', ok)

    # Fetch notifications for teacher
    qs = Notification.objects.filter(user=teacher).order_by('-created_at')[:5]
    ser = NotificationSerializer(qs, many=True).data
    print('\nNotifications for teacher:')
    print(json.dumps(ser, default=str, indent=2))

    print('\n--- debug_discount_run END ---')


if __name__ == '__main__':
    run()
