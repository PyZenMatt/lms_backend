#!/usr/bin/env python
"""
Script to debug the CHECK constraint issue
"""
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.db import connection
from rewards.models import BlockchainTransaction
from courses.models import Course

def check_database_constraints():
    """Check database constraints"""
    print("=== DATABASE CONSTRAINTS DEBUG ===")
    
    # Connect to SQLite directly
    db_path = 'db.sqlite3'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema for BlockchainTransaction
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='rewards_blockchaintransaction'")
        schema = cursor.fetchone()
        if schema:
            print("Table Schema:")
            print(schema[0])
            print()
        
        # Check if there are any CHECK constraints
        cursor.execute("PRAGMA table_info(rewards_blockchaintransaction)")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  {col}")
        print()
        
        conn.close()
    
    # Try to create a test transaction with different related_object_id values
    print("=== TESTING DIFFERENT related_object_id VALUES ===")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.first()
        if not user:
            print("No user found in database")
            return
            
        print(f"Testing with user: {user}")
        
        # Test cases
        test_cases = [
            ("1", "String number"),
            ("test", "String text"),
            ("", "Empty string"),
            (None, "None value"),
        ]
        
        for related_id, desc in test_cases:
            try:
                print(f"\nTesting {desc}: '{related_id}'")
                tx = BlockchainTransaction(
                    user=user,
                    transaction_type='course_purchase',
                    amount=10.0,
                    from_address='0x123',
                    to_address='0x456',
                    status='pending',
                    related_object_id=related_id,
                    notes='Test transaction'
                )
                tx.full_clean()  # Validate without saving
                print(f"  ✓ Validation passed")
                
                # Try to save
                tx.save()
                print(f"  ✓ Save successful - ID: {tx.id}")
                tx.delete()  # Clean up
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
    
    except Exception as e:
        print(f"Error in testing: {e}")

def test_real_course_purchase():
    """Test with real course data"""
    print("\n=== TESTING REAL COURSE PURCHASE ===")
    
    try:
        # Get first course
        course = Course.objects.first()
        if not course:
            print("No course found")
            return
            
        print(f"Testing with course: {course} (ID: {course.id})")
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.first()
        
        if not user:
            print("No user found")
            return
            
        print(f"Testing with user: {user}")
        
        # Test the exact code from the view
        tx = BlockchainTransaction.objects.create(
            user=user,
            transaction_type='course_purchase',
            amount=-15.0,  # Negative = outgoing
            from_address='0x123',
            to_address='0x456',
            transaction_hash='test_hash',
            status='completed',
            related_object_id=str(course.id),
            notes=f'Course purchase payment - Total: 15.0 TEO'
        )
        
        print(f"✓ Transaction created successfully - ID: {tx.id}")
        print(f"  Related object ID: {tx.related_object_id}")
        print(f"  Course ID: {course.id}")
        
        # Clean up
        tx.delete()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_database_constraints()
    test_real_course_purchase()
