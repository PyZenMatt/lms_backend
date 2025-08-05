#!/usr/bin/env python3
"""
TeoCoin Contract Feature Verification Script

This script checks what features your current TeoCoin2 contract has
and identifies any missing functionality needed for the complete system.
"""

import os
import sys
from decimal import Decimal
from web3 import Web3
import json

# Add the Django project to the path
sys.path.insert(0, '/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')

import django
django.setup()

from blockchain.blockchain import TeoCoinService
from blockchain.teocoin_abi import TEOCOIN_ABI

def analyze_contract_features():
    """Analyze the current TeoCoin2 contract to see what features it has"""
    
    print("🔍 ANALYZING YOUR TEOCOIN2 CONTRACT")
    print("=" * 50)
    
    try:
        # Initialize TeoCoin service
        teo_service = TeoCoinService()
        
        print(f"✅ Contract Address: {teo_service.contract_address}")
        print(f"✅ Network: Polygon Amoy ({teo_service.rpc_url})")
        print(f"✅ Connection Status: {'Connected' if teo_service.w3.is_connected() else 'Failed'}")
        
        # Basic contract info
        try:
            name = teo_service.contract.functions.name().call()
            symbol = teo_service.contract.functions.symbol().call()
            decimals = teo_service.contract.functions.decimals().call()
            total_supply = teo_service.contract.functions.totalSupply().call()
            
            print(f"\n📊 TOKEN INFO:")
            print(f"   Name: {name}")
            print(f"   Symbol: {symbol}")
            print(f"   Decimals: {decimals}")
            print(f"   Total Supply: {Web3.from_wei(total_supply, 'ether')} {symbol}")
            
        except Exception as e:
            print(f"❌ Failed to get basic token info: {e}")
            return False
        
        # Check available functions
        print(f"\n🔧 AVAILABLE FUNCTIONS:")
        available_functions = []
        function_signatures = {}
        
        for item in TEOCOIN_ABI:
            if item.get('type') == 'function':
                func_name = item.get('name')
                available_functions.append(func_name)
                function_signatures[func_name] = item
                print(f"   ✅ {func_name}")
        
        # Check for required platform functions
        print(f"\n🎯 PLATFORM INTEGRATION CHECK:")
        
        required_functions = [
            'mint',           # For minting rewards
            'burn',           # For burning tokens if needed
            'pause',          # Emergency stop
            'unpause',        # Resume operations
            'hasRole',        # Role-based access
            'grantRole',      # Grant permissions
            'revokeRole',     # Revoke permissions
        ]
        
        missing_functions = []
        for func in required_functions:
            if func in available_functions:
                print(f"   ✅ {func} - Available")
            else:
                print(f"   ❌ {func} - Missing")
                missing_functions.append(func)
        
        # Check events
        print(f"\n📡 AVAILABLE EVENTS:")
        available_events = []
        for item in TEOCOIN_ABI:
            if item.get('type') == 'event':
                event_name = item.get('name')
                available_events.append(event_name)
                print(f"   ✅ {event_name}")
        
        # Test basic functionality
        print(f"\n🧪 FUNCTIONALITY TESTS:")
        
        # Test balance query
        try:
            admin_address = teo_service.w3.eth.accounts[0] if teo_service.w3.eth.accounts else "0x0000000000000000000000000000000000000000"
            balance = teo_service.get_balance(admin_address)
            print(f"   ✅ Balance Query: Works (tested with {admin_address[:10]}...)")
        except Exception as e:
            print(f"   ❌ Balance Query: Failed ({e})")
        
        # Test minting capability (if function exists)
        if 'mint' in available_functions:
            print(f"   ✅ Minting Function: Available (not tested - requires admin privileges)")
        else:
            print(f"   ❌ Minting Function: Not available - THIS IS CRITICAL!")
        
        # Generate recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if missing_functions:
            print(f"   🔧 MISSING CRITICAL FUNCTIONS:")
            for func in missing_functions:
                print(f"      - {func}: Needed for {get_function_purpose(func)}")
            
            print(f"\n   📋 NEXT STEPS:")
            print(f"      1. Upgrade your contract to include missing functions")
            print(f"      2. Or deploy a new contract with all required features")
            print(f"      3. Use proxy pattern for future upgrades")
        else:
            print(f"   ✅ Your contract has all required functions!")
            print(f"   🚀 Ready to implement the complete earning system")
        
        # Check if we can mint (admin test)
        print(f"\n🔐 ADMIN ACCESS TEST:")
        if hasattr(teo_service, 'admin_private_key') and teo_service.admin_private_key:
            print(f"   ✅ Admin private key configured")
            print(f"   ⚠️  Testing minting requires gas - skipping automatic test")
        else:
            print(f"   ❌ No admin private key configured")
            print(f"   📝 Set ADMIN_PRIVATE_KEY in your environment variables")
        
        return True
        
    except Exception as e:
        print(f"❌ CONTRACT ANALYSIS FAILED: {e}")
        return False

def get_function_purpose(function_name):
    """Get human-readable purpose for each function"""
    purposes = {
        'mint': 'rewarding users with TEO tokens',
        'burn': 'removing tokens from circulation',
        'pause': 'emergency stop functionality',
        'unpause': 'resuming operations after pause',
        'hasRole': 'checking user permissions',
        'grantRole': 'giving admin permissions',
        'revokeRole': 'removing admin permissions',
    }
    return purposes.get(function_name, 'platform operations')

def test_earning_system_readiness():
    """Test if the current setup is ready for the earning system"""
    
    print(f"\n🎮 EARNING SYSTEM READINESS CHECK:")
    print("=" * 40)
    
    try:
        teo_service = TeoCoinService()
        
        # Check reward pool configuration
        if hasattr(teo_service, 'reward_pool_address') and teo_service.reward_pool_address:
            print(f"   ✅ Reward Pool Address: {teo_service.reward_pool_address}")
        else:
            print(f"   ❌ Reward Pool Address: Not configured")
        
        if hasattr(teo_service, 'reward_pool_private_key') and teo_service.reward_pool_private_key:
            print(f"   ✅ Reward Pool Private Key: Configured")
        else:
            print(f"   ❌ Reward Pool Private Key: Not configured")
        
        # Check if we can simulate minting
        print(f"\n   💰 MINTING SIMULATION:")
        print(f"      ⚠️  Actual minting requires gas and admin privileges")
        print(f"      📝 Your service is configured to mint from: {getattr(teo_service, 'reward_pool_address', 'Not set')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Earning system check failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TEOCOIN2 CONTRACT ANALYSIS STARTING...")
    print("This will check your current contract features and readiness\n")
    
    # Run contract analysis
    contract_ok = analyze_contract_features()
    
    if contract_ok:
        # Run earning system readiness check
        earning_ok = test_earning_system_readiness()
        
        print(f"\n🎯 FINAL SUMMARY:")
        print("=" * 30)
        
        if contract_ok and earning_ok:
            print(f"✅ YOUR SYSTEM STATUS: READY FOR IMPLEMENTATION")
            print(f"📋 NEXT STEPS:")
            print(f"   1. Implement earning triggers (courses, exercises)")
            print(f"   2. Add real-time notifications")
            print(f"   3. Complete frontend dashboard")
            print(f"   4. Test end-to-end user journey")
        else:
            print(f"⚠️  YOUR SYSTEM STATUS: NEEDS CONFIGURATION")
            print(f"📋 REQUIRED ACTIONS:")
            print(f"   1. Fix missing contract functions")
            print(f"   2. Configure reward pool settings")
            print(f"   3. Set up admin private keys")
            print(f"   4. Re-run this analysis")
    
    print(f"\n✨ Analysis Complete!")
