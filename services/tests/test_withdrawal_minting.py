#!/usr/bin/env python3
"""
Test TeoCoin Withdrawal Minting Process
This script simulates the actual minting process for pending withdrawals
"""

import os
import django
import sys

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.models import TeoCoinWithdrawalRequest, DBTeoCoinBalance
from services.teocoin_withdrawal_service import teocoin_withdrawal_service
from django.conf import settings
from decimal import Decimal

def test_withdrawal_minting():
    """Test the withdrawal minting functionality"""
    
    print("🎯 TeoCoin Withdrawal Minting Test")
    print("=" * 50)
    
    # Check configuration
    print(f"🏛️ Platform wallet: {settings.PLATFORM_WALLET_ADDRESS}")
    print(f"📍 TeoCoin contract: {settings.TEOCOIN_CONTRACT_ADDRESS}")
    print(f"🌐 Polygon RPC: {getattr(settings, 'POLYGON_AMOY_RPC_URL', 'Not configured')}")
    
    # Get pending withdrawals
    pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(status='pending')
    print(f"\n📋 Pending withdrawals: {pending_withdrawals.count()}")
    
    if not pending_withdrawals.exists():
        print("❌ No pending withdrawals to process")
        return
    
    # Show what we would process
    for i, withdrawal in enumerate(pending_withdrawals[:3], 1):  # Show first 3
        print(f"\n{i}. 👤 {withdrawal.user.email}")
        print(f"   💰 Amount: {withdrawal.amount} TEO")
        print(f"   📍 To: {withdrawal.metamask_address}")
        print(f"   📅 Created: {withdrawal.created_at}")
        
        # Test the minting function
        print("   🔄 Testing minting functionality...")
        result = teocoin_withdrawal_service.mint_tokens_to_address(
            amount=withdrawal.amount,
            to_address=withdrawal.metamask_address
        )
        
        if result['success']:
            print(f"   ✅ {result['message']}")
            if 'gas_estimate' in result:
                print(f"   ⛽ Gas estimate: {result['gas_estimate']}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    print(f"\n💡 To actually process withdrawals, you need to:")
    print(f"   1. Add the platform wallet private key to environment variables")
    print(f"   2. Ensure the wallet has MATIC for gas fees")
    print(f"   3. Run: python manage.py process_teocoin_withdrawals")
    
    print(f"\n🔧 Current Contract Functions Available:")
    if teocoin_withdrawal_service.teo_contract:
        try:
            # Try to get contract function names
            print("   Contract loaded successfully!")
            print("   📝 Ready for minting operations")
        except Exception as e:
            print(f"   ❌ Contract issue: {e}")
    else:
        print("   ❌ Contract not loaded")

def demonstrate_balance_update():
    """Show how balances would be updated after minting"""
    
    print(f"\n💰 Balance Update Simulation")
    print("-" * 30)
    
    # Get a sample user with pending withdrawal
    sample_withdrawal = TeoCoinWithdrawalRequest.objects.filter(status='pending').first()
    
    if sample_withdrawal:
        user = sample_withdrawal.user
        balance = DBTeoCoinBalance.objects.get(user=user)
        
        print(f"👤 User: {user.email}")
        print(f"📊 Current Balance:")
        print(f"   Available: {balance.available_balance} TEO")
        print(f"   Pending: {balance.pending_withdrawal} TEO")
        print(f"   Staked: {balance.staked_balance} TEO")
        
        print(f"\n🔄 After processing withdrawal of {sample_withdrawal.amount} TEO:")
        new_pending = balance.pending_withdrawal - sample_withdrawal.amount
        print(f"   Available: {balance.available_balance} TEO (unchanged)")
        print(f"   Pending: {new_pending} TEO (reduced)")
        print(f"   Staked: {balance.staked_balance} TEO (unchanged)")
        
        print(f"✅ {sample_withdrawal.amount} TEO would be minted to {sample_withdrawal.metamask_address}")

if __name__ == "__main__":
    test_withdrawal_minting()
    demonstrate_balance_update()
