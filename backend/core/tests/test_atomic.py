from django.test import TestCase, TransactionTestCase
from django.db import transaction, DatabaseError
from django.db.models import F
from django.core.exceptions import ValidationError
from django.conf import settings
from core.models import User, Lesson, TeoCoinTransaction
import time
from threading import Thread
from django.test import skipIfDBFeature, tag, skipUnlessDBFeature
from unittest import skipIf, skipUnless
from django.db import connection

class AtomicTransactionTestsSQLite(TransactionTestCase):
    def setUp(self):
        # Usa username unici per evitare collisioni
        timestamp = str(time.time()).replace('.', '')
        self.teacher = User.objects.create_user(
            username=f'teacher_{timestamp}',
            password='testpass',
            role='teacher'
        )
        self.student = User.objects.create_user(
            username=f'student_{timestamp}',
            password='testpass',
            role='student',
            teo_coins=1000
        )
        self.lesson = Lesson.objects.create(
            title=f'Lesson_{timestamp}',
            content='Content',
            teacher=self.teacher,
            price=500,
            duration=60
        )

    @tag('sqlite')
    def test_atomic_operations(self):
        """Verifica operazioni atomiche di base per SQLite"""
        # Test operazioni sequenziali
        self.student.subtract_teo_coins(500)
        self.student.refresh_from_db()
        self.assertEqual(self.student.teo_coins, 500)
        
        # Test rollback transazione
        try:
            with transaction.atomic():
                self.student.subtract_teo_coins(500)
                raise DatabaseError("Errore simulato")
        except DatabaseError:
            pass
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.teo_coins, 500)

    @tag('sqlite')
    def test_serialized_transactions(self):
        """Test transazioni serializzate per SQLite"""
        # Crea nuovi utenti con username unici
        timestamp = str(time.time()).replace('.', '')
        student = User.objects.create_user(
            username=f'new_student_{timestamp}',
            password='testpass',
            role='student',
            teo_coins=1000
        )
        
        # Prima transazione
        with transaction.atomic():
            student.subtract_teo_coins(500)
            student.refresh_from_db()
            self.assertEqual(student.teo_coins, 500)
        
        # Seconda transazione
        with transaction.atomic():
            student.subtract_teo_coins(500)
            student.refresh_from_db()
            self.assertEqual(student.teo_coins, 0)

    @tag('sqlite')
    def test_data_integrity(self):
        """Verifica integrità dati dopo operazioni fallite"""
        original_coins = self.student.teo_coins
        
        try:
            with transaction.atomic():
                self.student.subtract_teo_coins(1500)  # Importo superiore al saldo
        except ValueError:
            pass
        
        self.student.refresh_from_db()
        self.assertEqual(self.student.teo_coins, original_coins)