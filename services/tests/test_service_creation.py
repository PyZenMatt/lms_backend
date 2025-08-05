#!/usr/bin/env python3
"""
Test rapido per verificare se TeoCoinService è correttamente definito
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/teo/Project/school/schoolplatform')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from blockchain.blockchain import TeoCoinService

def test_service_creation():
    print("🔧 Test creazione TeoCoinService...")
    
    try:
        tcs = TeoCoinService()
        print("✅ TeoCoinService creato correttamente")
        
        # Verifica che il metodo esista
        if hasattr(tcs, 'get_optimized_gas_price'):
            print("✅ Metodo get_optimized_gas_price trovato")
            
            # Prova a chiamare il metodo
            gas_price = tcs.get_optimized_gas_price()
            print(f"✅ Gas price ottenuto: {gas_price} wei")
            
        else:
            print("❌ Metodo get_optimized_gas_price NON trovato")
            
        # Lista tutti i metodi
        methods = [method for method in dir(tcs) if not method.startswith('_')]
        print(f"📋 Metodi disponibili: {', '.join(methods)}")
        
    except Exception as e:
        print(f"❌ Errore nella creazione del servizio: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service_creation()
