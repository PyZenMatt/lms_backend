#!/usr/bin/env python3
"""
Check Production Configuration for Exercise System
Verifica la configurazione in produzione per il sistema esercizi
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings.prod')

try:
    django.setup()
    from django.conf import settings
    from courses.models import Exercise, ExerciseSubmission, ExerciseReview
    from users.models import User
    try:
        from services.consolidated_teocoin_service import ConsolidatedTeoCoinService as TeoCoinService
    except ImportError:
        try:
            from services.db_teocoin_service import DBTeoCoinService as TeoCoinService
        except ImportError:
            TeoCoinService = None
    from django.db import connection
    from datetime import datetime
    
    print("🔍 PRODUCTION ENVIRONMENT CHECK")
    print("=" * 60)
    
    # 1. Basic settings check
    print("\n1. 📋 Basic Configuration")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   ENVIRONMENT: {getattr(settings, 'ENVIRONMENT', 'NOT_SET')}")
    print(f"   DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
    
    # 2. Critical environment variables
    print("\n2. 🔐 Environment Variables")
    critical_vars = [
        'POLYGON_AMOY_RPC_URL',
        'TEOCOIN_CONTRACT_ADDRESS', 
        'ADMIN_PRIVATE_KEY',
        'ADMIN_WALLET_ADDRESS',
        'PLATFORM_WALLET_ADDRESS',
        'PLATFORM_PRIVATE_KEY',
        'REWARD_POOL_ADDRESS',
        'REWARD_POOL_PRIVATE_KEY'
    ]
    
    for var in critical_vars:
        value = getattr(settings, var, None) or os.getenv(var)
        if value:
            # Mask private keys for security
            if 'PRIVATE_KEY' in var:
                display_value = f"{value[:10]}...{value[-10:]}" if len(value) > 20 else "***masked***"
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: NOT SET")
    
    # 3. Database connectivity
    print("\n3. 🗄️ Database Connectivity")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("   ✅ Database connection: OK")
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'courses_%';")
            tables = cursor.fetchall()
            exercise_tables = [t[0] for t in tables if 'exercise' in t[0].lower()]
            print(f"   ✅ Exercise tables found: {len(exercise_tables)}")
            for table in exercise_tables:
                print(f"      - {table}")
                
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # 4. Model counts
    print("\n4. 📊 Model Data Counts")
    try:
        exercise_count = Exercise.objects.count()
        submission_count = ExerciseSubmission.objects.count()
        review_count = ExerciseReview.objects.count()
        user_count = User.objects.count()
        
        print(f"   ✅ Exercises: {exercise_count}")
        print(f"   ✅ Submissions: {submission_count}")
        print(f"   ✅ Reviews: {review_count}")
        print(f"   ✅ Users: {user_count}")
        
        # Check if we have recent activity
        if submission_count > 0:
            recent_submissions = ExerciseSubmission.objects.filter(
                created_at__gte=datetime.now().date()
            ).count()
            print(f"   📅 Today's submissions: {recent_submissions}")
            
    except Exception as e:
        print(f"   ❌ Model query error: {e}")
    
    # 5. TeoCoin service check
    print("\n5. ⚡ TeoCoin Service Check")
    try:
        if TeoCoinService:
            teocoin_service = TeoCoinService()
            print("   ✅ TeoCoin service initialized")
            
            # Try to get contract info (read-only) - only for blockchain services
            try:
                if hasattr(teocoin_service, 'contract'):
                    contract_address = teocoin_service.contract.address
                    print(f"   ✅ Contract address: {contract_address}")
                elif hasattr(teocoin_service, 'get_balance'):
                    print("   ✅ Database-based TeoCoin service (no blockchain contract)")
                else:
                    print("   ⚠️ Unknown TeoCoin service type")
            except Exception as e:
                print(f"   ⚠️ Contract connection issue: {e}")
        else:
            print("   ❌ No TeoCoin service available")
            
    except Exception as e:
        print(f"   ❌ TeoCoin service error: {e}")
    
    # 6. URLs check
    print("\n6. 🌐 URL Configuration")
    try:
        from django.urls import reverse
        from django.test import Client
        
        exercise_urls = [
            ('submit-exercise', [1]),
            ('review-exercise', [1]),
            ('assigned-reviews', []),
            ('review-history', []),
            ('submission-detail', [1]),
        ]
        
        for url_name, args in exercise_urls:
            try:
                url = reverse(url_name, args=args)
                print(f"   ✅ {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ {url_name}: {e}")
                
    except Exception as e:
        print(f"   ❌ URL check error: {e}")
    
    # 7. Recent logs check
    print("\n7. 📝 Log File Check")
    log_file = BASE_DIR / 'logs' / 'api_performance.log'
    if log_file.exists():
        print(f"   ✅ Log file exists: {log_file}")
        # Get last 5 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent_lines = lines[-5:] if lines else []
            print("   📋 Recent log entries:")
            for line in recent_lines:
                print(f"      {line.strip()}")
    else:
        print(f"   ⚠️ Log file not found: {log_file}")
    
    print("\n" + "=" * 60)
    print("✅ PRODUCTION CHECK COMPLETED")
    
except Exception as e:
    print(f"❌ CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
