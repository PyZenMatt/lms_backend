#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import ExerciseSubmission, ExerciseReview
from users.models import User
from rewards.models import BlockchainTransaction
from django.utils import timezone
from datetime import timedelta

def test_automatic_reward_processing():
    """
    Test automatic reward processing system
    """
    print("🧪 TESTING AUTOMATIC REWARD PROCESSING")
    print("=" * 50)
    
    # Get test users
    try:
        student = User.objects.get(username='student1')
        reviewer = User.objects.get(username='teacher1')
        print(f"✅ Test users found: {student.username}, {reviewer.username}")
    except User.DoesNotExist:
        print("❌ Test users not found")
        return
    
    # Count current reward transactions
    initial_count = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward']
    ).count()
    print(f"📊 Initial reward transactions: {initial_count}")
    
    # Create a test review to trigger signal
    print("\n🔄 Creating test review...")
    
    # Get an existing submission
    submission = ExerciseSubmission.objects.filter(student=student).first()
    if not submission:
        print("❌ No existing submission found for testing")
        return
    
    print(f"📝 Using submission {submission.pk}")
    
    # Create a new review (this should trigger review_reward signal)
    review = ExerciseReview.objects.create(
        submission=submission,
        reviewer=reviewer,
        score=88,
        reviewed_at=timezone.now()
    )
    print(f"✅ Created review {review.pk}")
    
    # Wait a moment for signals to process
    import time
    time.sleep(1)
    
    # Check if new reward transactions were created
    recent = timezone.now() - timedelta(seconds=30)
    new_rewards = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward'],
        created_at__gte=recent
    ).order_by('-created_at')
    
    print(f"\n📊 New reward transactions created: {new_rewards.count()}")
    
    for tx in new_rewards:
        print(f"  - {tx.pk}: {tx.user.username} - {tx.amount} TEO ({tx.transaction_type})")
        print(f"    Status: {tx.status}")
        if tx.tx_hash:
            print(f"    TX Hash: {tx.tx_hash[:20]}...")
        if tx.error_message:
            print(f"    Error: {tx.error_message}")
    
    # Final count
    final_count = BlockchainTransaction.objects.filter(
        transaction_type__in=['exercise_reward', 'review_reward']
    ).count()
    
    print(f"\n📊 Final reward transactions: {final_count}")
    print(f"📈 New transactions created: {final_count - initial_count}")
    
    if new_rewards.count() > 0:
        print("🎉 Automatic reward processing is working!")
        
        # Check if any were automatically processed
        auto_processed = new_rewards.filter(status='completed').count()
        auto_failed = new_rewards.filter(status='failed').count()
        still_pending = new_rewards.filter(status='pending').count()
        
        print(f"  - Automatically processed: {auto_processed}")
        print(f"  - Failed during processing: {auto_failed}")
        print(f"  - Still pending: {still_pending}")
        
    else:
        print("⚠️  No new reward transactions were created - check signal configuration")

if __name__ == "__main__":
    test_automatic_reward_processing()
