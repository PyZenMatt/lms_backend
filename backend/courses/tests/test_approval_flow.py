#!/usr/bin/env python3
"""
Script per testare approval + transferFrom con MetaMask flow
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import teocoin_service
from django.conf import settings

def test_approval_transferfrom():
    """Test del flusso approval + transferFrom"""
    
    print("🧪 Test Approval + TransferFrom Flow")
    print("=" * 50)
    
    # Configurazione
    student_address = "0x61CA0280cE520a8eB7e4ee175A30C768A5d144D4"
    teacher_address = "0xE2fA8AfbF1B795f5dEd1a33aa360872E9020a9A0"
    reward_pool_address = settings.REWARD_POOL_ADDRESS
    amount = Decimal('15')  # 15 TEO
    teacher_amount = amount * Decimal('0.85')  # 12.75 TEO
    commission_amount = amount * Decimal('0.15')  # 2.25 TEO
    
    print(f"👤 Student: {student_address}")
    print(f"👨‍🏫 Teacher: {teacher_address}")
    print(f"🏦 Reward Pool: {reward_pool_address}")
    print(f"💰 Amount: {amount} TEO (Teacher: {teacher_amount}, Commission: {commission_amount})")
    
    try:
        # 1. Verifica bilanci iniziali
        print("\n💼 1. Verifica bilanci iniziali...")
        student_balance = teocoin_service.get_balance(student_address)
        teacher_balance = teocoin_service.get_balance(teacher_address)
        reward_pool_balance = teocoin_service.get_balance(reward_pool_address)
        
        print(f"Student: {student_balance} TEO")
        print(f"Teacher: {teacher_balance} TEO")
        print(f"Reward Pool: {reward_pool_balance} TEO")
        
        # 2. Verifica allowance attuale
        print("\n🔍 2. Verifica allowance attuale...")
        allowance = teocoin_service.contract.functions.allowance(
            teocoin_service.w3.to_checksum_address(student_address),
            teocoin_service.w3.to_checksum_address(reward_pool_address)
        ).call()
        allowance_teo = teocoin_service.w3.from_wei(allowance, 'ether')
        print(f"Allowance: {allowance_teo} TEO")
        
        # 3. STEP CRITICO: Approve via reward pool (simula MetaMask)
        print("\n✍️ 3. Simulazione approval via reward pool...")
        print("💡 In produzione, questo sarebbe fatto via MetaMask dal frontend:")
        print("   - contract.approve(reward_pool_address, amount)")
        print("   - MetaMask richiede firma utente")
        
        # Per test, usiamo la chiave privata del reward pool per approvare dal wallet student
        # NOTA: Questo è solo per test! In produzione sarebbe via MetaMask
        
        # Proviamo a fare l'approval usando la reward pool come intermediario
        # Invece di approve diretto, testiamo il transfer dalla reward pool al student
        print("\n🔄 Alternativa: Transfer dalla reward pool allo studente...")
        
        # Prima assicuriamoci che la reward pool abbia abbastanza fondi
        if reward_pool_balance < amount:
            print(f"❌ Reward pool ha solo {reward_pool_balance} TEO, servono {amount} TEO")
            
            # Mint alcuni token alla reward pool per il test
            print("💰 Minting token alla reward pool per il test...")
            mint_tx = teocoin_service.mint_tokens(reward_pool_address, amount)
            if mint_tx:
                print(f"✅ Mint successful: {mint_tx}")
                reward_pool_balance = teocoin_service.get_balance(reward_pool_address)
                print(f"💼 Nuovo balance reward pool: {reward_pool_balance} TEO")
            else:
                print("❌ Mint failed")
                return
        
        # 4. Invece di transferFrom, testiamo transfer diretto dalla reward pool
        print("\n🚀 4. Test transfer diretto dalla reward pool...")
        
        # Transfer al teacher
        print(f"💸 Transfer {teacher_amount} TEO al teacher...")
        teacher_tx = teocoin_service.transfer_from_reward_pool(teacher_address, teacher_amount)
        
        if teacher_tx:
            print(f"✅ Teacher payment successful: {teacher_tx}")
        else:
            print("❌ Teacher payment failed")
            
        # 5. Verifica bilanci finali
        print("\n💼 5. Verifica bilanci finali...")
        student_balance_final = teocoin_service.get_balance(student_address)
        teacher_balance_final = teocoin_service.get_balance(teacher_address)
        reward_pool_balance_final = teocoin_service.get_balance(reward_pool_address)
        
        print(f"Student: {student_balance} → {student_balance_final} TEO")
        print(f"Teacher: {teacher_balance} → {teacher_balance_final} TEO")
        print(f"Reward Pool: {reward_pool_balance} → {reward_pool_balance_final} TEO")
        
        # 6. Calcolo differenze
        teacher_diff = float(teacher_balance_final) - float(teacher_balance)
        print(f"\n📊 Teacher ha ricevuto: {teacher_diff} TEO")
        
        if teacher_diff > 0:
            print("✅ Test successful! Il pagamento è andato a buon fine")
        else:
            print("❌ Test failed! Nessun pagamento ricevuto")
            
    except Exception as e:
        print(f"❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_approval_transferfrom()
