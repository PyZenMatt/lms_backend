#!/bin/bash

# TeoCoin Staking Contract Deployment Setup Script
# This script helps you securely set up deployment environment

echo "🚀 TeoCoin Staking Contract Deployment Setup"
echo "=============================================="

# Check if we're in the correct directory
if [ ! -f "scripts/deploy_staking_contract.py" ]; then
    echo "❌ Error: Please run this script from the schoolplatform root directory"
    exit 1
fi

echo ""
echo "📋 Deployment Checklist:"
echo "========================"

# Check Python dependencies
echo "🔧 Checking Python dependencies..."
python3 -c "import web3, solcx, eth_account" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed"
else
    echo "❌ Missing Python dependencies. Installing..."
    pip install web3 py-solc-x eth-account
fi

# Check network connectivity
echo "🌐 Testing Polygon Amoy connectivity..."
python3 -c "
from web3 import Web3
web3 = Web3(Web3.HTTPProvider('https://rpc-amoy.polygon.technology/'))
if web3.is_connected():
    print('✅ Connected to Polygon Amoy: True')
    print(f'🔗 Latest block: {web3.eth.block_number}')
else:
    print('❌ Failed to connect to Polygon Amoy')
    exit(1)
"

echo ""
echo "🔐 Private Key Setup:"
echo "===================="

# Check if private key is already set
if [ -z "$DEPLOYER_PRIVATE_KEY" ]; then
    echo "❌ DEPLOYER_PRIVATE_KEY not set"
    echo ""
    echo "💡 For actual deployment, you need to:"
    echo "   1. Get your MetaMask private key (Account Details → Export Private Key)"
    echo "   2. Make sure the account has MATIC for gas fees on Amoy testnet"
    echo "   3. Set the environment variable:"
    echo ""
    echo "   export DEPLOYER_PRIVATE_KEY=your_test_private_key"
    echo ""
    echo "🔒 SECURITY NOTES:"
    echo "   - Only use testnet private keys"
    echo "   - Never commit private keys to version control"
    echo "   - Use a dedicated test account"
    echo ""
    echo "🪙 To get Amoy MATIC:"
    echo "   - Visit: https://faucet.polygon.technology/"
    echo "   - Select Polygon Amoy"
    echo "   - Enter your wallet address"
    echo "   - Request test MATIC"
    echo ""
else
    echo "✅ DEPLOYER_PRIVATE_KEY is set"
    
    # Verify the private key format and derive address
    DEPLOYER_ADDRESS=$(python3 -c "
from eth_account import Account
import os
try:
    private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
    if not private_key.startswith('0x'):
        private_key = '0x' + private_key
    account = Account.from_key(private_key)
    print(f'📍 Deployer address: {account.address}')
except Exception as e:
    print(f'❌ Invalid private key format: {e}')
    exit(1)
    ")
    
    if [ $? -eq 0 ]; then
        echo "✅ Private key format valid"
        echo "$DEPLOYER_ADDRESS"
        
        # Check balance
        echo "💰 Checking MATIC balance..."
        python3 -c "
from web3 import Web3
from eth_account import Account
import os

web3 = Web3(Web3.HTTPProvider('https://rpc-amoy.polygon.technology/'))
private_key = os.getenv('DEPLOYER_PRIVATE_KEY')
if not private_key.startswith('0x'):
    private_key = '0x' + private_key
account = Account.from_key(private_key)
balance = web3.eth.get_balance(account.address)
balance_matic = web3.from_wei(balance, 'ether')

print(f'💰 Balance: {balance_matic:.4f} MATIC')

if balance_matic < 0.1:
    print('⚠️  Low balance! You may need more MATIC for deployment.')
    print('   Visit: https://faucet.polygon.technology/')
else:
    print('✅ Sufficient balance for deployment')
"
    else
        echo "❌ Invalid private key. Please check your DEPLOYER_PRIVATE_KEY"
        exit 1
    fi
fi

echo ""
echo "📄 Contract Information:"
echo "======================="
echo "📍 TeoCoin2 Address: 0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8"
echo "🔗 Chain ID: 80002 (Polygon Amoy)"
echo "📄 Contract File: ./blockchain/contracts/TeoCoinStaking.sol"

echo ""
echo "🚀 Ready to Deploy!"
echo "=================="

if [ -n "$DEPLOYER_PRIVATE_KEY" ]; then
    echo "✅ All prerequisites met. Run deployment with:"
    echo "   python3 scripts/deploy_staking_contract.py"
else
    echo "⏳ Set DEPLOYER_PRIVATE_KEY environment variable first"
    echo "   Then run: python3 scripts/deploy_staking_contract.py"
fi

echo ""
echo "📚 Post-deployment steps:"
echo "   1. Update backend service with new contract address"
echo "   2. Test staking functionality"
echo "   3. Integrate with frontend UI"
echo "   4. Update documentation"
