#!/bin/bash

# Script per controllare lo stato dell'utente admin
echo "🔍 Controllando lo stato dell'utente admin..."

cd /home/teo/Project/school
source venv/bin/activate
cd schoolplatform

python manage.py shell -c "
from blockchain.models import DBTeoCoinBalance, TeoCoinWithdrawalRequest
from users.models import User

admin_user = User.objects.get(id=1)
print(f'👤 Utente: {admin_user.username} ({admin_user.email}) - Ruolo: {admin_user.role}')

# Balance
try:
    balance = DBTeoCoinBalance.objects.get(user=admin_user)
    print(f'💰 Balance:')
    print(f'  - Available: {balance.available_balance} TEO')
    print(f'  - Staked: {balance.staked_balance} TEO') 
    print(f'  - Pending withdrawal: {balance.pending_withdrawal} TEO')
    print(f'  - Total: {balance.available_balance + balance.staked_balance + balance.pending_withdrawal} TEO')
except Exception as e:
    print(f'❌ Errore balance: {e}')

# Withdrawal requests
pending_withdrawals = TeoCoinWithdrawalRequest.objects.filter(
    user=admin_user, 
    status__in=['pending', 'processing']
).count()
print(f'⏳ Withdrawal pendenti: {pending_withdrawals}')

print('✅ Controllo completato')
"
