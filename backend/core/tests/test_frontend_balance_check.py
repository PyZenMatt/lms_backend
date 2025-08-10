#!/usr/bin/env python
"""
Test frontend balance display to ensure it shows student balance, not reward pool balance
"""

import os
import sys
import django
import asyncio
from datetime import datetime

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService
from account.models import CustomUser

async def test_balance_display():
    print("🧪 Testing Frontend Balance Display")
    print("=" * 50)
    
    try:
        # Get student1 user
        from account.models import CustomUser
        student1 = CustomUser.objects.get(username='student1')
        student_wallet = student1.wallet_address
        
        print(f"👤 Student1 wallet: {student_wallet}")
        
        # Get blockchain service
        blockchain = TeoCoinService()
        
        # Get reward pool address for comparison
        reward_pool_address = await blockchain.get_reward_pool_address()
        print(f"🏦 Reward pool wallet: {reward_pool_address}")
        
        # Get balances
        student_teo_balance = await blockchain.get_teocoin_balance(student_wallet)
        student_matic_balance = await blockchain.get_matic_balance(student_wallet)
        
        pool_teo_balance = await blockchain.get_teocoin_balance(reward_pool_address)
        pool_matic_balance = await blockchain.get_matic_balance(reward_pool_address)
        
        print("\n📊 Balance Comparison:")
        print(f"Student TEO Balance:    {student_teo_balance:.4f} TEO")
        print(f"Reward Pool TEO Balance: {pool_teo_balance:.4f} TEO")
        print(f"Student MATIC Balance:  {student_matic_balance:.6f} MATIC")
        print(f"Reward Pool MATIC Balance: {pool_matic_balance:.6f} MATIC")
        
        print("\n✅ IMPORTANT: Frontend should show STUDENT balances:")
        print(f"   TEO: {student_teo_balance:.4f}")
        print(f"   MATIC: {student_matic_balance:.6f}")
        
        print("\n❌ Frontend should NOT show reward pool balances:")
        print(f"   TEO: {pool_teo_balance:.4f}")
        print(f"   MATIC: {pool_matic_balance:.6f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_balance_display())
