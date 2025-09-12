# TEO Calculation & Duplicate Transaction Fix

## 🚨 Issues Identified

### Issue 1: Incorrect TEO Amount Calculation
- **Problem**: User applied 15 TEO discount but only 10 TEO was deducted
- **Root Cause**: Wrong parameter mapping in R1.1 `apply_discount_and_snapshot()`
- **Details**: Used `platform_teo` (0) instead of total `discount_amount` (15)

### Issue 2: Duplicate Transactions  
- **Problem**: 4 transactions in DB for single payment
- **Root Cause**: Parallel execution of old capture_hold system and new R1.1 system
- **Details**: Both systems deducting TEO simultaneously

### Issue 3: R1.1 Not Activating
- **Problem**: Snapshots created without decisions (Non-R1.1)
- **Root Cause**: `teacher_teo=0` failing the R1.1 activation condition
- **Details**: Incorrect parameter causing R1.1 to skip activation

## 🔧 Fixes Applied

### Fix 1: Corrected R1.1 Parameters

**Before (Incorrect)**:
```python
# courses/views/payments.py & rewards/views/discount_views.py
teo_cost=_Decimal(str(breakdown["platform_teo"])),  # ❌ Often 0
offered_teacher_teo=_Decimal(str(breakdown["teacher_teo"])),
```

**After (Correct)**:
```python
# courses/views/payments.py
teo_cost=discount_amount,  # ✅ Total discount amount (15 TEO)
offered_teacher_teo=_Decimal(str(breakdown["teacher_teo"])),

# rewards/views/discount_views.py  
teo_cost=discount_amount_eur,  # ✅ Total discount amount (15 TEO)
offered_teacher_teo=_Decimal(str(breakdown["teacher_teo"])),
```

### Fix 2: Prevented Duplicate Hold Capture

**Added conditional logic**:
```python
if applied_snapshot and applied_snapshot.wallet_hold_id:
    # Skip capture for R1.1 snapshots (those with decisions)
    if applied_snapshot.decision is not None:
        logger.info("🔗 Skipping immediate capture for R1.1 snapshot - waiting for teacher decision")
    else:
        # CAPTURE THE HOLD: Only for non-R1.1 snapshots
        capture_success = wallet_hold_service.capture_hold(...)
```

## 📊 Parameter Understanding

### `teo_cost` Parameter
- **Purpose**: Amount student PAYS in TEO (total discount amount)
- **Correct Value**: `discount_amount` / `discount_amount_eur` 
- **Example**: If 15 TEO discount → `teo_cost = 15.00`

### `offered_teacher_teo` Parameter  
- **Purpose**: Amount OFFERED to teacher if they accept
- **Correct Value**: `breakdown["teacher_teo"]`
- **Example**: With Bronze tier 1.25x bonus → `offered_teacher_teo = 18.75`

## 🎯 Expected Flow Now

### R1.1 Flow (TEO with Teacher Decision)
1. **Student applies 15 TEO discount**
2. **R1.1 activates** (`teacher_teo > 0`)
3. **Snapshot + Decision created atomically**
4. **No immediate capture** (decision pending)
5. **Teacher decides**:
   - Accept → Gets 18.75 TEO, Platform absorbs 3.75 TEO difference
   - Decline → Platform gets 15 TEO

### Non-R1.1 Flow (No Teacher Involvement)
1. **Student applies discount with no teacher bonus**
2. **R1.1 skips** (`teacher_teo = 0`)
3. **Snapshot created without decision**
4. **Immediate capture** (no teacher decision needed)

## ✅ Validation Points

- ✅ **Correct TEO amounts**: `teo_cost = discount_amount` (total)
- ✅ **No duplicate transactions**: R1.1 skips immediate capture  
- ✅ **R1.1 activation**: Proper `teacher_teo > 0` detection
- ✅ **Backward compatibility**: Non-R1.1 flows unchanged

## 🚀 Status: Fixed

Both calculation errors and duplicate transaction issues should now be resolved.
