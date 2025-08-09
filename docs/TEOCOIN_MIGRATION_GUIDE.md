# 🔄 TeoCoin Migration Guide - Old to New System

## 📋 **QUICK MIGRATION REFERENCE**

### **Old Blockchain Operations → New DB Operations**

#### **User Transfers (DEPRECATED)**
```python
# ❌ OLD - Blockchain transfer (REMOVED)
blockchain_service.transfer_tokens_between_users(from_user, to_user, amount, reason)

# ✅ NEW - DB-based transfer
from services.db_teocoin_service import db_teocoin_service

# Deduct from sender
db_teocoin_service.deduct_balance(from_user, amount, 'transfer', f'Transfer to {to_user.username}')
# Credit to receiver  
db_teocoin_service.add_balance(to_user, amount, 'transfer', f'Transfer from {from_user.username}')
```

#### **Course Payments (REFACTORED)**
```python
# ❌ OLD - Direct blockchain payment (DEPRECATED)
web3_service.processCoursePaymentDirectLegacy(student, teacher, price, course_id)

# ✅ NEW - DB-based discount + optional blockchain withdrawal
discount_info = db_teocoin_service.apply_course_discount(student, course_price, course)
# Blockchain only used if user wants to withdraw TEO to MetaMask
```

#### **Reward Distribution (REFACTORED)**
```python
# ❌ OLD - Blockchain reward from pool (REMOVED)
blockchain_service.mint_tokens_to_user(user, amount, reason)

# ✅ NEW - Direct DB crediting
db_teocoin_service.add_balance(user, amount, 'lesson_reward', 'Exercise completion')
```

### **Service Imports Update**

#### **For Internal Operations (Rewards, Discounts, Transfers)**
```python
# ✅ Use DB service for all business logic
from services.db_teocoin_service import db_teocoin_service

# Get balance
balance = db_teocoin_service.get_available_balance(user)

# Add reward
db_teocoin_service.add_balance(user, amount, 'reward', description)

# Apply discount
discount_result = db_teocoin_service.apply_course_discount(user, price, course)
```

#### **For External Operations (Mint/Burn only)**
```python
# ✅ Use blockchain service only for external operations
from blockchain.blockchain import teocoin_service

# Mint tokens to user's MetaMask (withdrawal)
tx_hash = teocoin_service.mint_tokens(user_wallet_address, amount)

# Get MetaMask balance (for verification)
balance = teocoin_service.get_balance(wallet_address)
```

## 🔧 **COMPATIBILITY LAYER**

### **Removed Functions with Replacements**

| **Removed Function** | **Replacement** | **Notes** |
|---------------------|-----------------|-----------|
| `transfer_tokens_between_users()` | Use `deduct_balance()` + `add_balance()` | DB-based, instant |
| `process_course_payment_blockchain()` | Use `apply_course_discount()` | DB-based discounts |
| `transfer_from_reward_pool()` | Use `add_balance()` directly | No pool needed |
| `processCoursePaymentDirectLegacy()` | Use DB payments + optional withdraw | Simplified flow |

### **Configuration Variables Cleanup**

#### **Remove from .env (No longer needed)**
```env
# Reward pool variables (pool system deprecated)
REWARD_POOL_ADDRESS=
REWARD_POOL_PRIVATE_KEY=

# Blockchain transaction settings (not needed for DB operations)
GAS_PRICE_MULTIPLIER=
MAX_GAS_LIMIT=
BLOCKCHAIN_RETRY_COUNT=
```

#### **Keep in .env (Still required)**
```env
# Required for mint/burn operations only
POLYGON_AMOY_RPC_URL=https://rpc-amoy.polygon.technology/
TEOCOIN_CONTRACT_ADDRESS=0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8
ADMIN_PRIVATE_KEY=your_admin_private_key
```

## 🧪 **Testing Updates**

### **Update Test Imports**
```python
# ❌ OLD - Testing blockchain transfers
from services.blockchain_service import blockchain_service
# blockchain transfer tests

# ✅ NEW - Testing DB operations
from services.db_teocoin_service import db_teocoin_service
from blockchain.models import DBTeoCoinTransaction, DBTeoCoinBalance

def test_user_reward():
    initial_balance = db_teocoin_service.get_available_balance(user)
    db_teocoin_service.add_balance(user, Decimal('2.0'), 'lesson_reward', 'Test')
    new_balance = db_teocoin_service.get_available_balance(user)
    assert new_balance == initial_balance + Decimal('2.0')
```

### **Remove Obsolete Tests**
- `test_transfer_tokens_between_users_*` - functionality removed
- `test_reward_pool_*` - reward pool system deprecated
- Blockchain transaction tests for internal operations

## 🚀 **Performance Benefits**

### **Before (Blockchain-heavy)**
```python
# Slow: 2-5 second blockchain transactions
await blockchain_service.transfer_tokens_between_users(from_user, to_user, amount)
# Expensive: $0.01-0.50 gas per transaction
# Unreliable: Network congestion causes failures
```

### **After (DB-optimized)**
```python
# Fast: Millisecond database operations
db_teocoin_service.deduct_balance(from_user, amount, 'transfer', reason)
db_teocoin_service.add_balance(to_user, amount, 'transfer', reason)
# Free: No gas costs for internal operations
# Reliable: Database transactions never fail due to network
```

## 🔍 **Verification Checklist**

### **✅ Confirm New System Working**
- [ ] Rewards credit instantly via DB
- [ ] Course discounts apply immediately
- [ ] Balance transfers work between users
- [ ] Staking operations function correctly
- [ ] Transaction history shows in real-time

### **✅ Confirm Blockchain Integration**
- [ ] Mint operations work for withdrawals
- [ ] Burn verification works for deposits  
- [ ] Balance queries work for MetaMask wallets
- [ ] Contract interaction functions properly

### **✅ Confirm Cleanup Complete**
- [ ] Removed obsolete blockchain transfer functions
- [ ] Updated all service imports
- [ ] Removed unnecessary environment variables
- [ ] Updated test suites
- [ ] Added deprecation notices

## 🆘 **Troubleshooting**

### **"Function not found" errors**
If you see errors about missing functions, check the migration table above for the new equivalent.

### **Import errors**
Make sure you're importing from the right service:
- **Internal operations:** `from services.db_teocoin_service import db_teocoin_service`
- **External operations:** `from blockchain.blockchain import teocoin_service`

### **Performance issues**
The new system should be much faster. If you experience slowness, you might be accidentally using old blockchain functions.

---

**📞 Need Help?** Check the full documentation in `TEOCOIN_REFACTORING_COMPLETE.md` or the service docstrings for detailed usage examples.
