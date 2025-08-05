#!/usr/bin/env python3
"""
Lista di faucet alternativi per Polygon Amoy testnet
"""

def show_alternative_faucets():
    """Mostra faucet alternativi per Polygon Amoy"""
    
    student1_address = "0x0a3bAF75b8ca80E3C6FDf6282e6b88370DD255C6"
    
    print("🔧 Alternative faucets for Polygon Amoy testnet")
    print("=" * 60)
    print(f"📍 Target address: {student1_address}")
    print()
    
    faucets = [
        {
            "name": "Official Polygon Faucet",
            "url": "https://faucet.polygon.technology/",
            "status": "❌ Blocked (72h cooldown)",
            "amount": "0.1-1 MATIC"
        },
        {
            "name": "Alchemy Polygon Faucet", 
            "url": "https://www.alchemy.com/faucets/polygon-amoy",
            "status": "🔄 Try this",
            "amount": "0.1 MATIC"
        },
        {
            "name": "QuickNode Faucet",
            "url": "https://faucet.quicknode.com/polygon/amoy",
            "status": "🔄 Try this", 
            "amount": "0.01-0.1 MATIC"
        },
        {
            "name": "GetBlock Faucet",
            "url": "https://getblock.io/faucet/polygon-amoy/",
            "status": "🔄 Try this",
            "amount": "0.01 MATIC"
        },
        {
            "name": "Moralis Faucet",
            "url": "https://moralis.io/faucets/",
            "status": "🔄 Try this",
            "amount": "0.1 MATIC"
        }
    ]
    
    for i, faucet in enumerate(faucets, 1):
        print(f"{i}. {faucet['name']}")
        print(f"   🔗 {faucet['url']}")
        print(f"   📊 {faucet['status']} - {faucet['amount']}")
        print()
    
    print("💡 INSTRUCTIONS:")
    print("1. Try faucets 2-5 (they may have different cooldown policies)")
    print("2. Some faucets require social media verification")
    print("3. Some require Discord or Twitter login")
    print("4. If all fail, we can use admin MATIC for testing")
    print()
    
    print("🧪 ALTERNATIVE: Use existing admin MATIC")
    print("   Admin still has 0.001 MATIC")
    print("   We can do limited testing with admin wallet")

if __name__ == "__main__":
    show_alternative_faucets()
