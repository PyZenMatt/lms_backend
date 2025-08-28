"""
Smoke test script (run inside Django manage.py shell):

Usage:
    python manage.py shell -c "exec(open('backend/scripts/smoke_accept_flow.py').read())"

This script is idempotent: it will create users/course/balances if missing,
apply a discount (debiting student) and then accept it (crediting teacher).
It prints important IDs and balances so you can verify the flow.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from courses.models import Course
from blockchain.models import DBTeoCoinBalance
from rewards.services.transaction_services import apply_discount_and_snapshot, teacher_make_decision

User = get_user_model()

# Config
STUDENT_EMAIL = "student8@artschool.it"
TEACHER_EMAIL = "teacher8@artschool.it"
COURSE_TITLE = "SMOKE: KISS Course"
ORDER_ID = "smoke_order_001"

# Create or get users
student, student_created = User.objects.get_or_create(
    email=STUDENT_EMAIL,
    defaults={"username": STUDENT_EMAIL.split('@')[0], "password": "testpass123", "role": "student"},
)
teacher, teacher_created = User.objects.get_or_create(
    email=TEACHER_EMAIL,
    defaults={"username": TEACHER_EMAIL.split('@')[0], "password": "testpass123", "role": "teacher"},
)

# Create or get a course
course, course_created = Course.objects.get_or_create(
    title=COURSE_TITLE,
    defaults={"teacher": teacher, "price_eur": Decimal("10.00"), "description": "Smoke test course"},
)

# Ensure student balance
sbal, _ = DBTeoCoinBalance.objects.get_or_create(user=student, defaults={"available_balance": Decimal("50.0"), "staked_balance": Decimal("0")})
if sbal.available_balance < Decimal("5"):
    sbal.available_balance = Decimal("50.0")
    sbal.save(update_fields=["available_balance"]) 

print("=== SMOKE START ===")
print(f"student: {student.email} (id={student.id}) created={student_created}")
print(f"teacher: {teacher.email} (id={teacher.id}) created={teacher_created}")
print(f"course: {course.title} (id={course.id}) created={course_created}")
print("student balance before:", DBTeoCoinBalance.objects.get(user=student).available_balance)
print("teacher balance before:", DBTeoCoinBalance.objects.filter(user=teacher).first() and DBTeoCoinBalance.objects.get(user=teacher).available_balance)

# Apply discount: student pays teo_cost and snapshot+decision created
teo_cost = Decimal("1.5")
offered_teacher_teo = Decimal("1.5")
res = apply_discount_and_snapshot(student_user_id=student.id, teacher_id=teacher.id, course_id=course.id, teo_cost=teo_cost, offered_teacher_teo=offered_teacher_teo)
print("APPLY result:", res)

dec_id = res.get("pending_decision_id")
if not dec_id:
    print("No decision id returned; aborting smoke test.")
else:
    # Accept the decision
    out = teacher_make_decision(decision_id=dec_id, accept=True)
    print("ACCEPT result:", out)

    # Balances after
    print("student balance after:", DBTeoCoinBalance.objects.get(user=student).available_balance)
    print("teacher balance after:", DBTeoCoinBalance.objects.get(user=teacher).available_balance)

print("=== SMOKE END ===")
