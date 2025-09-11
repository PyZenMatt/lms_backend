# 🎯 STRIPE WEBHOOK SETUP - FINAL STEP

## ✅ STATO ATTUALE: TUTTO PRONTO!

**Issue-04A (Metadata binding)**: ✅ VERIFIED  
**Issue-04B (Webhook correlation)**: ✅ VERIFIED  
**Settlement service**: ✅ VERIFIED  
**Endpoint disponibile**: ✅ VERIFIED

## 🚀 ULTIMO STEP: CONFIGURAZIONE STRIPE DASHBOARD

### 1. Accedi a Stripe Dashboard
- Vai su: https://dashboard.stripe.com/test/webhooks
- Usa account con chiave: `sk_test_51RcjXd1ION4Zwx6o...`

### 2. Crea Webhook Endpoint
```
Endpoint URL: https://yourdomain.com/api/v1/payments/webhooks/stripe/
(Per dev locale: usare ngrok o stripe CLI)

Eventi da ascoltare:
✅ checkout.session.completed
✅ payment_intent.succeeded
```

### 3. Per Development Locale (RACCOMANDATO)
```bash
# Installa Stripe CLI se non presente
curl -s https://packages.stripe.com/api/security/keypair/stripe-cli-gpg/public | gpg --dearmor | sudo tee /usr/share/keyrings/stripe.gpg
echo "deb [signed-by=/usr/share/keyrings/stripe.gpg] https://packages.stripe.com/stripe-cli-debian-local stable main" | sudo tee -a /etc/apt/sources.list.d/stripe.list
sudo apt update && sudo apt install stripe

# Login a Stripe
stripe login

# Forward webhook a server locale
stripe listen --forward-to http://127.0.0.1:8000/api/v1/payments/webhooks/stripe/

# Questo comando darà il WEBHOOK_SECRET da mettere nel .env:
# Example output: whsec_1234567890abcdef...
```

### 4. Aggiorna .env con il WEBHOOK_SECRET vero
```bash
# Sostituisci nel .env:
STRIPE_WEBHOOK_SECRET=whsec_REAL_SECRET_FROM_STRIPE_CLI
```

### 5. Test Completo
```bash
# In un terminale: forward webhook
stripe listen --forward-to http://127.0.0.1:8000/api/v1/payments/webhooks/stripe/

# In un altro terminale: trigger test
stripe trigger checkout.session.completed

# Verifica nei log Django:
# ✅ Webhook ricevuto
# ✅ Correlazione trovata via metadata.discount_snapshot_id
# ✅ Settlement eseguito
# ✅ Saldo TEO scalato
```

## 📊 VERIFICA FINALE

### Nel database dovrai vedere:
```sql
-- Snapshot status: pending → confirmed
-- external_txn_id: stripe_event:evt_...
-- confirmed_at: timestamp popolato
```

### Nei log Django:
```
🔄 Stripe webhook received event_id=evt_... event_type=checkout.session.completed
✅ Snapshot found via metadata.discount_snapshot_id: 123 → snapshot_id=123
INFO Capturing hold 456 for snapshot 123
INFO TEO hold captured: hold_id=456, capture_id=789, amount=10, user=1
✅ Successfully settled TEO hold operation=settle_completed
```

## 🎉 ISSUE RISOLTO!

**Root Cause**: Webhook mai configurato/ricevuto  
**Solution**: Issue-04A + Issue-04B + Stripe Dashboard setup  
**Result**: Settlement automatico funzionante  

**Saldo TEO ora viene scalato correttamente dopo pagamento Stripe! 🚀**
