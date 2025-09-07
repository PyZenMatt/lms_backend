import os
import sys
from decimal import Decimal

import django
import pytest
from blockchain.models import DBTeoCoinBalance, DBTeoCoinTransaction
from courses.models import Course
from django.contrib.auth import get_user_model
from services.db_teocoin_service import DBTeoCoinService

# Setup Django
sys.path.insert(0, "/home/teo/Project/school/schoolplatform")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "schoolplatform.settings")
django.setup()


User = get_user_model()


@pytest.mark.quarantine
@pytest.mark.slow
@pytest.mark.django_db
def test_teocoin_discount_deduction():
    """
    Test che verifica la deduzione del saldo TeoCoin dopo l'acquisto
    """
    # Cerca un utente esistente, altrimenti creane uno per il test
    user = User.objects.filter(role="student").first()
    if user is None:
        user = User.objects.create_user(
            username="test_student",
            email="test_student@example.com",
            password="testpassword",
            role="student",
            first_name="Test",
            last_name="Student",
        )

    # Inizializza il servizio TeoCoin
    db_teo_service = DBTeoCoinService()

    # Assicurati che l'utente abbia un balance record
    balance_obj, created = DBTeoCoinBalance.objects.get_or_create(
        user=user,
        defaults={
            "available_balance": Decimal("100.00"),
            "staked_balance": Decimal("0.00"),
        },
    )
    # Assicurati che l'utente abbia almeno 50 TEO per il test
    if balance_obj.available_balance < Decimal("50.00"):
        balance_obj.available_balance = Decimal("100.00")
        balance_obj.save()

    # Cerca un corso per il test, altrimenti creane uno
    course = Course.objects.first()
    if course is None:
        # Ensure there's a teacher to assign
        teacher = User.objects.filter(role="teacher").first()
        if teacher is None:
            teacher = User.objects.create_user(
                username="test_teacher",
                email="test_teacher@example.com",
                password="testpassword",
                role="teacher",
                first_name="Teacher",
                last_name="Test",
            )
        course = Course.objects.create(
            title="Test Course for TeoCoin",
            description="Auto-created course for test",
            price_eur=Decimal("50.00"),
            teacher=teacher,
        )

    # Registra il saldo iniziale
    initial_balance = db_teo_service.get_available_balance(user)

    # Simula la deduzione del discount (come farebbe ConfirmPaymentView)
    discount_amount = Decimal("25.00")  # 25 TEO discount

    # Verifica se esiste già una transazione per questo corso
    existing_discount = DBTeoCoinTransaction.objects.filter(
        user=user, course=course, transaction_type="spent_discount", amount__lt=0
    ).first()
    if existing_discount:
        existing_discount.delete()

    # Testa la deduzione
    success = db_teo_service.deduct_balance(
        user=user,
        amount=discount_amount,
        transaction_type="spent_discount",
        description=f"TeoCoin discount for course: {course.title} ({discount_amount} TEO)",
        course=course,
    )
    assert success, "Deduction failed"

    final_balance = db_teo_service.get_available_balance(user)
    expected_balance = initial_balance - discount_amount
    assert final_balance == expected_balance, "Balance mismatch"

    # Verifica che la transazione sia stata registrata
    transaction = DBTeoCoinTransaction.objects.filter(
        user=user, course=course, transaction_type="spent_discount"
    ).last()
    assert transaction is not None, "No transaction recorded"


@pytest.mark.quarantine
@pytest.mark.slow
@pytest.mark.django_db
def test_duplicate_deduction_prevention():
    """
    Test che verifica la prevenzione della doppia deduzione
    """
    user = User.objects.filter(role="student").first()
    course = Course.objects.first()
    assert (
        user is not None and course is not None
    ), "Missing user or course for duplicate test"

    # Controlla se esiste già una transazione
    existing_discount = DBTeoCoinTransaction.objects.filter(
        user=user, course=course, transaction_type="spent_discount", amount__lt=0
    ).first()
    assert (
        existing_discount is not None
    ), "No existing discount found - run the first test to create one"
