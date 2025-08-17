"""
Quick Deployment Verification Script
Verifies all prerequisites for TeoCoin Staking contract deployment
"""

import os
import sys
from web3 import Web3
from eth_account import Account

def main():
    print("🔍 TeoCoin Staking Deployment Verification")
    print("=" * 45)
    
    # 1. Check network connection
    print("\n🌐 Network Connectivity:")
    try:
        web3 = Web3(Web3.HTTPProvider('https://rpc-amoy.polygon.technology/'))
        if web3.is_connected():
            print(f"✅ Connected to Polygon Amoy: True")
            print(f"🔗 Chain ID: {web3.eth.chain_id}")
            print(f"🧱 Latest block: {web3.eth.block_number}")
        else:
            print("❌ Failed to connect to Polygon Amoy")
            return False
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False
    
    # 2. Check private key
    print("\n🔐 Private Key Check:")
    private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
    if not private_key:
        print("❌ DEPLOYER_PRIVATE_KEY not set")
        print("💡 For actual deployment, set: export DEPLOYER_PRIVATE_KEY=your_test_private_key")
        return False
    
    try:
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        account = Account.from_key(private_key)
        print(f"✅ Private key format valid")
        print(f"📍 Deployer address: {account.address}")
        
        # Check balance
        balance = web3.eth.get_balance(account.address)
        balance_matic = web3.from_wei(balance, 'ether')
        print(f"💰 Balance: {balance_matic:.6f} MATIC")
        
        if balance_matic < 0.01:
            print("⚠️  Very low balance! You may need more MATIC for deployment.")
            print("   Visit: https://faucet.polygon.technology/")
            return False
        elif balance_matic < 0.1:
            print("⚠️  Low balance, but should be sufficient for deployment.")
        else:
            print("✅ Sufficient balance for deployment")
            
    except Exception as e:
        print(f"❌ Invalid private key: {e}")
        return False
    
    # 3. Check contract file
    print("\n📄 Contract File Check:")
    contract_path = './blockchain/contracts/TeoCoinStaking.sol'
    if os.path.exists(contract_path):
        print(f"✅ Contract file found: {contract_path}")
        
        # Check contract content
        with open(contract_path, 'r') as f:
            content = f.read()
            if 'TeoCoinStaking' in content and 'constructor' in content:
                print("✅ Contract appears valid")
            else:
                print("❌ Contract file may be incomplete")
                return False
    else:
        print(f"❌ Contract file not found: {contract_path}")
        return False
    
    # 4. Check dependencies
    print("\n📦 Dependencies Check:")
    try:
        import web3
        import solcx
        import eth_account
        print("✅ All Python dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install web3 py-solc-x eth-account")
        return False
    
    # 5. TeoCoin2 contract check
    print("\n🪙 TeoCoin2 Contract Check:")
    teocoin_address = "0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"
    try:
        # Simple contract existence check
        code = web3.eth.get_code(teocoin_address)
        if code and len(code) > 2:  # More than '0x'
            print(f"✅ TeoCoin2 contract found at: {teocoin_address}")
        else:
            print(f"❌ No contract code at: {teocoin_address}")
            return False
    except Exception as e:
        print(f"❌ Error checking TeoCoin2 contract: {e}")
        return False
    
    print("\n🎉 All checks passed! Ready for deployment.")
    print("\n🚀 To deploy, run:")
    print("   python3 scripts/deploy_staking_contract.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
