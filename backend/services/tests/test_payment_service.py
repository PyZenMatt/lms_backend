"""
Tests for Payment Service
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from decimal import Decimal
from unittest.mock import patch, MagicMock

from courses.models import Course
from rewards.models import BlockchainTransaction
from services.payment_service import payment_service
from services.exceptions import (
    UserNotFoundError, 
    CourseNotFoundError,
    InsufficientTeoCoinsError,
    TeoArtServiceException
)

User = get_user_model()


class PaymentServiceTestCase(TestCase):
    """Test cases for PaymentService"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.student = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass',
            role='student',
            first_name='Student',
            last_name='One',
            wallet_address='0x1234567890123456789012345678901234567890'
        )
        
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@test.com',
            password='testpass',
            role='teacher',
            first_name='Teacher',
            last_name='One',
            wallet_address='0x0987654321098765432109876543210987654321',
            is_approved=True
        )
        
        self.student_no_wallet = User.objects.create_user(
            username='student2',
            email='student2@test.com',
            password='testpass',
            role='student',
            first_name='Student',
            last_name='Two'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='A test course',
            price=Decimal('100.00'),
            teacher=self.teacher,
            is_approved=True
        )
        
        self.unapproved_course = Course.objects.create(
            title='Unapproved Course',
            description='An unapproved test course',
            price=Decimal('50.00'),
            teacher=self.teacher,
            is_approved=False
        )
    
    @patch('services.payment_service.PaymentService._get_user_balance')
    def test_initiate_course_purchase_success(self, mock_balance):
        """Test successful course purchase initiation"""
        mock_balance.return_value = Decimal('200.00')  # Sufficient balance
        
        result = payment_service.initiate_course_purchase(
            user_id=self.student.id,
            course_id=self.course.id,
            wallet_address=self.student.wallet_address
        )
        
        self.assertTrue(result['payment_required'])
        self.assertEqual(result['course_id'], self.course.id)
        self.assertEqual(result['course_title'], self.course.title)
        self.assertEqual(result['course_price'], 100.0)
        self.assertEqual(result['teacher_amount'], 85.0)  # 85% to teacher
        self.assertEqual(result['commission_amount'], 15.0)  # 15% commission
        self.assertEqual(result['commission_rate'], '15.0%')
        self.assertEqual(result['student_balance'], 200.0)
        
        # Check payment breakdown
        breakdown = result['payment_breakdown']
        self.assertEqual(breakdown['total_price'], 100.0)
        self.assertEqual(breakdown['teacher_receives'], 85.0)
        self.assertEqual(breakdown['platform_commission'], 15.0)
        self.assertEqual(breakdown['commission_percentage'], 15.0)
    
    def test_initiate_course_purchase_user_not_found(self):
        """Test course purchase initiation with non-existent user"""
        with self.assertRaises(UserNotFoundError):
            payment_service.initiate_course_purchase(
                user_id=99999,
                course_id=self.course.id,
                wallet_address='0x1234567890123456789012345678901234567890'
            )
    
    def test_initiate_course_purchase_course_not_found(self):
        """Test course purchase initiation with non-existent course"""
        with self.assertRaises(CourseNotFoundError):
            payment_service.initiate_course_purchase(
                user_id=self.student.id,
                course_id=99999,
                wallet_address=self.student.wallet_address
            )
    
    def test_initiate_course_purchase_invalid_role(self):
        """Test course purchase initiation with non-student user"""
        with self.assertRaises(TeoArtServiceException) as cm:
            payment_service.initiate_course_purchase(
                user_id=self.teacher.id,
                course_id=self.course.id,
                wallet_address=self.teacher.wallet_address
            )
        
        self.assertIn("Only students can purchase courses", str(cm.exception))
    
    def test_initiate_course_purchase_unapproved_course(self):
        """Test course purchase initiation with unapproved course"""
        with self.assertRaises(TeoArtServiceException) as cm:
            payment_service.initiate_course_purchase(
                user_id=self.student.id,
                course_id=self.unapproved_course.id,
                wallet_address=self.student.wallet_address
            )
        
        self.assertIn("Course is not available for purchase", str(cm.exception))
    
    @patch('services.payment_service.PaymentService._get_user_balance')
    def test_initiate_course_purchase_already_enrolled(self, mock_balance):
        """Test course purchase initiation when user already enrolled"""
        mock_balance.return_value = Decimal('200.00')
        
        # Enroll student in course
        self.course.students.add(self.student)
        
        with self.assertRaises(TeoArtServiceException) as cm:
            payment_service.initiate_course_purchase(
                user_id=self.student.id,
                course_id=self.course.id,
                wallet_address=self.student.wallet_address
            )
        
        self.assertIn("User already enrolled in this course", str(cm.exception))
    
    @patch('services.payment_service.PaymentService._get_user_balance')
    def test_initiate_course_purchase_insufficient_balance(self, mock_balance):
        """Test course purchase initiation with insufficient balance"""
        mock_balance.return_value = Decimal('50.00')  # Less than course price
        
        with self.assertRaises(InsufficientTeoCoinsError):
            payment_service.initiate_course_purchase(
                user_id=self.student.id,
                course_id=self.course.id,
                wallet_address=self.student.wallet_address
            )
    
    @patch('services.payment_service.PaymentService._get_user_balance')
    def test_initiate_course_purchase_updates_wallet(self, mock_balance):
        """Test that wallet address is updated during initiation"""
        mock_balance.return_value = Decimal('200.00')
        new_wallet = '0xNewWalletAddress123456789012345678901234'
        
        # Student has different wallet address
        self.student.wallet_address = '0xOldWallet'
        self.student.save()
        
        payment_service.initiate_course_purchase(
            user_id=self.student.id,
            course_id=self.course.id,
            wallet_address=new_wallet
        )
        
        # Check wallet was updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.wallet_address, new_wallet)
    
    @patch('services.payment_service.PaymentService._verify_payment_transaction')
    def test_complete_course_purchase_success(self, mock_verify):
        """Test successful course purchase completion"""
        mock_verify.return_value = True
        tx_hash = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        
        result = payment_service.complete_course_purchase(
            user_id=self.student.id,
            course_id=self.course.id,
            transaction_hash=tx_hash,
            wallet_address=self.student.wallet_address
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['course_id'], self.course.id)
        self.assertEqual(result['student_id'], self.student.id)
        self.assertEqual(result['total_paid'], 100.0)
        self.assertEqual(result['teacher_received'], 85.0)
        self.assertEqual(result['platform_commission'], 15.0)
        self.assertEqual(result['transaction_hash'], tx_hash)
        self.assertTrue(result['enrollment_confirmed'])
        
        # Verify student is enrolled
        self.course.refresh_from_db()
        self.assertIn(self.student, self.course.students.all())
        
        # Verify transactions were created
        purchase_tx = BlockchainTransaction.objects.get(
            transaction_hash=tx_hash,
            transaction_type='course_purchase'
        )
        self.assertEqual(purchase_tx.user, self.student)
        self.assertEqual(purchase_tx.amount, -Decimal('100.00'))
        
        teacher_tx = BlockchainTransaction.objects.get(
            transaction_hash=tx_hash,
            transaction_type='course_earned'
        )
        self.assertEqual(teacher_tx.user, self.teacher)
        self.assertEqual(teacher_tx.amount, Decimal('85.00'))
        
        commission_tx = BlockchainTransaction.objects.get(
            transaction_hash=tx_hash,
            transaction_type='platform_commission'
        )
        self.assertEqual(commission_tx.user, self.student)
        self.assertEqual(commission_tx.amount, -Decimal('15.00'))
    
    def test_complete_course_purchase_transaction_already_processed(self):
        """Test completion with already processed transaction"""
        tx_hash = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        
        # Create existing transaction
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('100.00'),
            transaction_type='course_purchase',
            status='completed',
            transaction_hash=tx_hash,
            from_address=self.student.wallet_address,
            to_address=self.teacher.wallet_address
        )
        
        with self.assertRaises(TeoArtServiceException) as cm:
            payment_service.complete_course_purchase(
                user_id=self.student.id,
                course_id=self.course.id,
                transaction_hash=tx_hash,
                wallet_address=self.student.wallet_address
            )
        
        self.assertIn("Transaction already processed", str(cm.exception))
    
    @patch('services.payment_service.PaymentService._verify_payment_transaction')
    def test_complete_course_purchase_verification_failed(self, mock_verify):
        """Test completion with failed transaction verification"""
        mock_verify.return_value = False
        tx_hash = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        
        with self.assertRaises(TeoArtServiceException) as cm:
            payment_service.complete_course_purchase(
                user_id=self.student.id,
                course_id=self.course.id,
                transaction_hash=tx_hash,
                wallet_address=self.student.wallet_address
            )
        
        self.assertIn("Blockchain transaction verification failed", str(cm.exception))
    
    def test_get_user_purchase_history(self):
        """Test getting user purchase history"""
        # Create test transactions
        tx1 = BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('100.00'),
            transaction_type='course_purchase',
            status='completed',
            transaction_hash='0x123',
            from_address=self.student.wallet_address,
            to_address=self.teacher.wallet_address,
            related_object_id=str(self.course.id),
            notes='Course purchase: Test Course'
        )
        
        tx2 = BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('15.00'),
            transaction_type='platform_commission',
            status='completed',
            transaction_hash='0x123',
            from_address=self.student.wallet_address,
            to_address='reward_pool',
            related_object_id=str(self.course.id),
            notes='Platform commission'
        )
        
        history = payment_service.get_user_purchase_history(self.student.id)
        
        self.assertEqual(len(history), 2)
        
        # Check transaction data
        purchase_data = next(tx for tx in history if tx['transaction_type'] == 'course_purchase')
        self.assertEqual(purchase_data['amount'], -100.0)
        self.assertEqual(purchase_data['transaction_hash'], '0x123')
        self.assertIsNotNone(purchase_data['related_course'])
        self.assertEqual(purchase_data['related_course']['title'], 'Test Course')
    
    def test_get_user_purchase_history_with_filters(self):
        """Test getting user purchase history with filters"""
        # Create test transactions
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('100.00'),
            transaction_type='course_purchase',
            status='completed',
            transaction_hash='0x123'
        )
        
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('15.00'),
            transaction_type='platform_commission',
            status='completed',
            transaction_hash='0x456'
        )
        
        # Filter by transaction type
        history = payment_service.get_user_purchase_history(
            self.student.id,
            transaction_type='course_purchase'
        )
        
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['transaction_type'], 'course_purchase')
        
        # Filter with limit
        history = payment_service.get_user_purchase_history(
            self.student.id,
            limit=1
        )
        
        self.assertEqual(len(history), 1)
    
    def test_get_course_sales_stats(self):
        """Test getting course sales statistics"""
        # Create test transactions for course sales
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('100.00'),
            transaction_type='course_purchase',
            status='completed',
            related_object_id=str(self.course.id)
        )
        
        BlockchainTransaction.objects.create(
            user=self.teacher,
            amount=Decimal('85.00'),
            transaction_type='course_earned',
            status='completed',
            related_object_id=str(self.course.id)
        )
        
        # Create another student and sale
        student2 = User.objects.create_user(
            username='student3',
            email='student3@test.com',
            role='student'
        )
        
        BlockchainTransaction.objects.create(
            user=student2,
            amount=-Decimal('100.00'),
            transaction_type='course_purchase',
            status='completed',
            related_object_id=str(self.course.id)
        )
        
        BlockchainTransaction.objects.create(
            user=self.teacher,
            amount=Decimal('85.00'),
            transaction_type='course_earned',
            status='completed',
            related_object_id=str(self.course.id)
        )
        
        stats = payment_service.get_course_sales_stats(self.course.id)
        
        self.assertEqual(stats['course_id'], self.course.id)
        self.assertEqual(stats['course_title'], self.course.title)
        self.assertEqual(stats['total_sales'], 2)
        self.assertEqual(stats['total_revenue'], 200.0)
        self.assertEqual(stats['teacher_earnings'], 170.0)
        self.assertEqual(stats['platform_commission'], 30.0)
        self.assertEqual(stats['average_sale_value'], 100.0)
        self.assertEqual(stats['commission_rate'], '15.0%')
    
    def test_get_course_sales_stats_no_sales(self):
        """Test getting course sales statistics with no sales"""
        stats = payment_service.get_course_sales_stats(self.course.id)
        
        self.assertEqual(stats['total_sales'], 0)
        self.assertEqual(stats['total_revenue'], 0.0)
        self.assertEqual(stats['teacher_earnings'], 0.0)
        self.assertEqual(stats['platform_commission'], 0.0)
        self.assertEqual(stats['average_sale_value'], 0.0)
    
    @patch('blockchain.views.teocoin_service')
    def test_get_user_balance(self, mock_service):
        """Test getting user balance"""
        mock_service.get_balance.return_value = 150.50
        
        balance = payment_service._get_user_balance('0x123')
        
        self.assertEqual(balance, Decimal('150.50'))
        mock_service.get_balance.assert_called_once_with('0x123')
    
    @patch('blockchain.views.teocoin_service')
    def test_get_user_balance_error(self, mock_service):
        """Test getting user balance with error"""
        mock_service.get_balance.side_effect = Exception("Connection error")
        
        balance = payment_service._get_user_balance('0x123')
        
        self.assertEqual(balance, Decimal('0'))
    
    def test_verify_payment_transaction_database_found(self):
        """Test transaction verification using database records"""
        tx_hash = '0x123abc'
        
        # Create transaction in database
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=-Decimal('100.00'),
            transaction_hash=tx_hash,
            from_address=self.student.wallet_address,
            to_address=self.teacher.wallet_address
        )
        
        result = payment_service._verify_payment_transaction(
            tx_hash,
            self.student.wallet_address,
            self.teacher.wallet_address,
            Decimal('100.00')
        )
        
        self.assertTrue(result)
    
    def test_verify_payment_transaction_simulated(self):
        """Test verification of simulated blockchain transaction"""
        tx_hash = '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        
        # Create simulated transaction
        BlockchainTransaction.objects.create(
            user=self.student,
            amount=Decimal('100.00'),
            transaction_type='simulated_payment',
            status='completed',
            transaction_hash=tx_hash,
            from_address=self.student.wallet_address,
            to_address=self.teacher.wallet_address
        )
        
        result = payment_service._verify_blockchain_transaction(
            tx_hash,
            self.student.wallet_address,
            self.teacher.wallet_address,
            Decimal('100.00')
        )
        
        self.assertTrue(result)
