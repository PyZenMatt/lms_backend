"""
Core serializers for the TeoArt School Platform.

This module contains shared serializers used across multiple apps,
particularly for blockchain transactions and course-related data.

Classes:
    BlockchainTransactionSerializer: For blockchain transaction data
    TeacherCourseSerializer: For teacher course management data
"""
from rest_framework import serializers
from rewards.models import BlockchainTransaction
from courses.models import Course
from users.serializers import UserSerializer


class BlockchainTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for blockchain transactions.
    
    This serializer replaces the old TeoCoinTransaction serializer and provides
    detailed information about blockchain transactions including buyer information
    and human-readable descriptions.
    
    Fields:
        - id: Transaction ID
        - created_at: Transaction timestamp
        - amount: Transaction amount in TeoCoins
        - transaction_type: Type of transaction (earned, purchase, etc.)
        - buyer: Username of the buyer (for course transactions)
        - description: Human-readable transaction description
        - tx_hash: Blockchain transaction hash
        - status: Transaction status
    """
    buyer = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = BlockchainTransaction
        fields = [
            'id', 'created_at', 'amount', 'transaction_type', 
            'buyer', 'description', 'tx_hash', 'status'
        ]

    def get_buyer(self, obj):
        """
        Get the buyer information for course-related transactions.
        
        Args:
            obj: BlockchainTransaction instance
            
        Returns:
            str: Username of the buyer or None
        """
        # For course earnings, show who bought the course
        if obj.transaction_type == 'course_earned' and obj.related_object_id:
            purchase = BlockchainTransaction.objects.filter(
                transaction_type='course_purchase',
                related_object_id=obj.related_object_id
            ).order_by('-created_at').first()
            if purchase and purchase.user:
                return purchase.user.username
                
        # For course purchases, the buyer is the user
        if obj.transaction_type == 'course_purchase' and obj.user:
            return obj.user.username
            
        return None

    def get_description(self, obj):
        """
        Generate a human-readable description for the transaction.
        
        Args:
            obj: BlockchainTransaction instance
            
        Returns:
            str: Human-readable transaction description
        """
        try:
            # Handle course purchase transactions
            if obj.transaction_type == 'course_purchase':
                if obj.related_object_id:
                    try:
                        course = Course.objects.get(id=obj.related_object_id)
                        return f"Acquisto corso: {course.title}"
                    except Course.DoesNotExist:
                        return "Acquisto corso: (corso non trovato)"
                return "Acquisto corso"

            # Handle course earning transactions (teacher revenue)
            if obj.transaction_type == 'course_earned':
                if obj.related_object_id:
                    try:
                        course = Course.objects.get(id=obj.related_object_id)
                        return f"Vendita corso: {course.title}"
                    except Course.DoesNotExist:
                        return "Vendita corso: (corso non trovato)"
                return "Vendita corso"

            # Handle exercise and review rewards
            if obj.transaction_type == 'exercise_reward':
                return f"Premio esercizio (ID: {obj.related_object_id})"

            if obj.transaction_type == 'review_reward':
                return f"Premio valutazione (ID: {obj.related_object_id})"

            # Default: convert transaction type to readable format
            return obj.transaction_type.replace('_', ' ').title()

        except Exception as e:
            # Fallback description in case of any errors
            return f"Transazione blockchain: {obj.transaction_type}"


class TeacherCourseSerializer(serializers.ModelSerializer):
    """
    Serializer for teacher course management.
    
    This serializer provides course information specifically formatted for
    teacher dashboards, including student enrollment counts and teacher details.
    
    Fields:
        - id: Course ID
        - title: Course title
        - description: Course description
        - price: Course price in TeoCoins
        - teacher: Teacher information (nested)
        - students_count: Number of enrolled students
        - created_at: Course creation timestamp
        - updated_at: Last update timestamp
    """
    students_count = serializers.SerializerMethodField()
    teacher = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'teacher',
            'students_count', 'created_at', 'updated_at'
        ]

    def get_students_count(self, obj):
        """
        Get the number of students enrolled in the course.
        
        Args:
            obj: Course instance
            
        Returns:
            int: Number of enrolled students
        """
        return obj.students.count()


