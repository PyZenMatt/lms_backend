# 🐛 Fix TeoCoin Discount Bug - Documentazione

## 📋 Problema Originale

**Bug**: Durante l'acquisto di corsi con sconto TeoCoin, lo sconto veniva applicato al prezzo finale ma il saldo TeoCoin dello studente rimaneva invariato nel database.

**Comportamento atteso**: Dopo l'acquisto, il campo `balance` in TeoCoin dello studente deve essere diminuito dell'importo dello sconto applicato.

**Impatto**: Gli studenti potevano utilizzare TeoCoin per ottenere sconti senza che il loro saldo venisse effettivamente scalato, causando un problema di consistenza nei dati.

## 🔍 Analisi Root Cause

### Problemi Identificati:

1. **Doppio flusso payment confuso**: 
   - NUOVO flusso: `CreatePaymentIntentView` → Stripe → `ConfirmPaymentView` → deduzione TeoCoin
   - VECCHIO flusso: Frontend → `ApplyDiscountView` (deprecato ma ancora chiamato)

2. **Frontend obsoleto**: Il frontend chiamava ancora l'endpoint deprecato `/teocoin/apply-discount/`

3. **Logica buggy in ConfirmPaymentView**: Conditional logic errato per gestire transazioni esistenti

4. **Parametri incorrect**: Uso di parametri sbagliati nel servizio `DBTeoCoinService`

## 🛠️ Soluzioni Implementate

### 1. Fix ConfirmPaymentView Logic (courses/views/payments.py)

**Prima** (logica buggy):
```python
# Logica confusa e potenzialmente doppia deduzione
if balance_obj['available_balance'] >= discount_amount:
    # Forza la deduzione se la transazione esiste ma il saldo non è stato scalato
    success = db_teo_service.deduct_balance(...)
```

**Dopo** (logica semplificata):
```python
# Controlla se discount già applicato per questo corso
existing_discount = DBTeoCoinTransaction.objects.filter(
    user=user,
    course=course,
    transaction_type='spent_discount',
    amount__lt=0
).first()

if existing_discount:
    logger.info("✅ TeoCoin discount already applied - skipping duplicate")
else:
    # Apply TeoCoin deduction for the first time
    success = db_teo_service.deduct_balance(
        user=user,
        amount=discount_amount,
        transaction_type='spent_discount',
        description=f'TeoCoin discount for course: {course.title}',
        course=course
    )
```

### 2. Cleanup Frontend (frontend/src/services/api/teocoin.js)

**Rimosso**:
```javascript
// DEPRECATED: Questa funzione chiamava l'endpoint deprecato
export const applyTeoCoinDiscount = async (courseId, teoAmount, discountPercentage) => {
  const response = await api.post('/teocoin/apply-discount/', {...});
  return response.data;
};
```

**Aggiunto**:
```javascript
// NOTE: The applyTeoCoinDiscount function has been removed.
// TeoCoin discount is now automatically applied during payment confirmation
// in the CreatePaymentIntentView → ConfirmPaymentView flow.
```

### 3. Correzioni Tecniche

- ✅ **Import Decimal**: Aggiunto import locale per risolvere scope issues
- ✅ **Exception handling**: Rimosso except clause unreachable  
- ✅ **Transaction type**: Corretto da `'discount'` a `'spent_discount'`
- ✅ **Course parameter**: Corretto da `course_id=str(course_id)` a `course=course`
- ✅ **Logging**: Aggiunto logging dettagliato per debugging

## 🎯 Flusso Corretto Post-Fix

```
1. 👤 Student seleziona corso con TeoCoin discount
   ↓
2. 💳 CreatePaymentIntentView calcola prezzo scontato
   - Controlla balance TeoCoin disponibile
   - Calcola discount amount
   - Crea Stripe payment intent con prezzo scontato
   ↓
3. 💰 Stripe processa pagamento (importo già scontato)
   ↓
4. ✅ ConfirmPaymentView conferma pagamento
   - Verifica payment_intent.status == 'succeeded'
   - Crea CourseEnrollment
   - 🎯 DEDUCE TeoCoin balance (fix principale!)
   ↓
5. 🛡️ Anti-duplicate protection:
   - Controlla se esiste già DBTeoCoinTransaction per questo corso
   - Se esiste → skip deduzione
   - Se non esiste → applica deduzione
```

## 📊 Test di Verifica

Il fix è stato validato per garantire:

- ✅ **Deduzione corretta**: TeoCoin balance viene scalato dopo payment confirmation
- ✅ **No doppia deduzione**: Sistema previene multiple deduzioni per stesso corso
- ✅ **Transaction logging**: Ogni deduzione viene registrata in DBTeoCoinTransaction
- ✅ **Error handling**: Gestione errori robusta con logging dettagliato
- ✅ **Frontend cleanup**: Endpoint deprecato non più chiamato

## 🚀 Deployment Checklist

- [x] Fix backend logic in ConfirmPaymentView
- [x] Remove deprecated frontend API calls
- [x] Validate parameter corrections
- [x] Add comprehensive logging
- [x] Test duplicate prevention logic
- [x] Verify transaction type compatibility

## 📝 Note per il Futuro

1. **Monitoring**: I nuovi log permetteranno di monitorare facilmente le deduzioni TeoCoin
2. **Transaction history**: Ogni sconto è ora tracciato in DBTeoCoinTransaction
3. **Audit trail**: Possibile vedere chi ha usato TeoCoin discount e quando
4. **Scalability**: Logica pulita e semplice, facile da mantenere

## 🎉 Risultato Finale

**PRIMA**: 
- Sconto applicato ✅
- Balance TeoCoin scalato ❌ (BUG!)

**DOPO**: 
- Sconto applicato ✅ 
- Balance TeoCoin scalato ✅ (RISOLTO!)

Il sistema ora funziona correttamente: quando uno studente acquista un corso con sconto TeoCoin, il prezzo viene scontato E il balance TeoCoin viene dedotto della quantità corretta.
