from rest_framework import serializers
from .models import BlockchainTransaction


class BlockchainTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for blockchain transactions - replaces the old TeoCoinTransaction serializer.
    Provides detailed information about blockchain transactions including related objects.
    """
    explorer_url = serializers.ReadOnlyField()
    description = serializers.SerializerMethodField()
    related_object_title = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = BlockchainTransaction
        fields = [
            'id', 
            'transaction_type', 
            'amount', 
            'from_address', 
            'to_address', 
            'tx_hash', 
            'status', 
            'error_message',
            'notes',
            'created_at', 
            'confirmed_at',
            'explorer_url',
            'description',
            'related_object_title',
            'user'
        ]
        read_only_fields = ['id', 'created_at', 'confirmed_at', 'explorer_url']

    def get_description(self, obj):
        """Generate a human-readable description of the transaction"""
        if obj.notes:
            return obj.notes
            
        descriptions = {
            'course_purchase': f"Acquisto corso (${obj.amount} TEO)",
            'course_earned': f"Guadagno da vendita corso (${obj.amount} TEO)",
            'exercise_reward': f"Ricompensa esercizio (${obj.amount} TEO)",
            'review_reward': f"Ricompensa valutazione (${obj.amount} TEO)",
            'manual_mint': f"Distribuzione manuale (${obj.amount} TEO)",
            'reward_pool': f"Ricompensa dal pool (${obj.amount} TEO)"
        }
        
        return descriptions.get(obj.transaction_type, f"Transazione (${obj.amount} TEO)")

    def get_related_object_title(self, obj):
        """Get the title of the related object (course, exercise, etc.)"""
        if not obj.related_object_id:
            return None
            
        try:
            if obj.transaction_type in ['course_purchase', 'course_earned']:
                from courses.models import Course
                course = Course.objects.get(pk=obj.related_object_id)
                return course.title
                
            elif obj.transaction_type in ['exercise_reward']:
                from courses.models import Exercise
                exercise = Exercise.objects.get(pk=obj.related_object_id)
                return exercise.title
                
        except Exception:
            pass
            
        return None

    def get_user(self, obj):
        """Get user information for admin view"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name
            }
        return None

