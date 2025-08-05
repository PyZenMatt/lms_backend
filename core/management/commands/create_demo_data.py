#!/usr/bin/env python
"""
Demo Data Creation Script for TeoArt School Platform
Creates sample courses with fiat pricing for testing payment integration.
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/home/teo/Project/school/schoolplatform')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import Course
from users.models import User
from django.contrib.auth import get_user_model

def create_demo_data():
    """Create demo courses with fiat pricing"""
    
    # Get or create a demo instructor
    User = get_user_model()
    instructor, created = User.objects.get_or_create(
        username='demo_instructor',
        defaults={
            'email': 'instructor@teoart.school',
            'first_name': 'Demo',
            'last_name': 'Instructor',
            'is_staff': True,
        }
    )
    
    if created:
        print(f"✓ Created demo instructor: {instructor.username}")
    else:
        print(f"✓ Using existing instructor: {instructor.username}")
    
    # Sample courses data
    courses_data = [
        {
            'title': 'Digital Art Fundamentals',
            'description': 'Learn the basics of digital art creation using modern tools and techniques. Perfect for beginners who want to start their artistic journey.',
            'price_eur': Decimal('49.99'),
            'teocoin_reward': Decimal('250.00'),
            'teocoin_discount_percent': Decimal('15.00'),
        },
        {
            'title': 'Advanced 3D Modeling',
            'description': 'Master advanced 3D modeling techniques with Blender and industry-standard workflows. Includes character modeling and environment design.',
            'price_eur': Decimal('89.99'),
            'teocoin_reward': Decimal('450.00'),
            'teocoin_discount_percent': Decimal('20.00'),
        },
        {
            'title': 'NFT Art Creation Masterclass',
            'description': 'Complete guide to creating, minting, and selling NFT art. Learn about blockchain integration and digital marketplace strategies.',
            'price_eur': Decimal('129.99'),
            'teocoin_reward': Decimal('650.00'),
            'teocoin_discount_percent': Decimal('25.00'),
        },
        {
            'title': 'Photography & Post-Processing',
            'description': 'Professional photography techniques combined with advanced post-processing using Adobe Creative Suite.',
            'price_eur': Decimal('69.99'),
            'teocoin_reward': Decimal('350.00'),
            'teocoin_discount_percent': Decimal('18.00'),
        },
        {
            'title': 'Concept Art for Games',
            'description': 'Learn to create compelling concept art for video games. Covers character design, environment concepts, and visual storytelling.',
            'price_eur': Decimal('99.99'),
            'teocoin_reward': Decimal('500.00'),
            'teocoin_discount_percent': Decimal('22.00'),
        },
        {
            'title': 'Free Introduction to Art',
            'description': 'A completely free course to get you started with basic art principles. No payment required!',
            'price_eur': Decimal('0.00'),
            'teocoin_reward': Decimal('50.00'),
            'teocoin_discount_percent': Decimal('0.00'),
        }
    ]
    
    created_courses = []
    
    for course_data in courses_data:
        course, created = Course.objects.get_or_create(
            title=course_data['title'],
            defaults={
                'description': course_data['description'],
                'instructor': instructor,
                'price_eur': course_data['price_eur'],
                'teocoin_reward': course_data['teocoin_reward'],
                'teocoin_discount_percent': course_data['teocoin_discount_percent'],
                'is_published': True,
            }
        )
        
        if created:
            created_courses.append(course)
            print(f"✓ Created course: {course.title} (€{course.price_eur})")
        else:
            # Update existing course with new pricing
            course.price_eur = course_data['price_eur']
            course.teocoin_reward = course_data['teocoin_reward']
            course.teocoin_discount_percent = course_data['teocoin_discount_percent']
            course.save()
            print(f"✓ Updated course: {course.title} (€{course.price_eur})")
    
    print(f"\n🎉 Demo data creation completed!")
    print(f"📚 Total courses in database: {Course.objects.count()}")
    print(f"💰 Courses with fiat pricing: {Course.objects.filter(price_eur__gt=0).count()}")
    print(f"🆓 Free courses: {Course.objects.filter(price_eur=0).count()}")
    
    print("\n💡 You can now test the payment integration with these courses!")
    print("🔗 Access the platform at: http://localhost:8000")
    
    return created_courses

if __name__ == '__main__':
    try:
        courses = create_demo_data()
        print("\n✅ Demo data script completed successfully!")
    except Exception as e:
        print(f"\n❌ Error creating demo data: {str(e)}")
        sys.exit(1)
