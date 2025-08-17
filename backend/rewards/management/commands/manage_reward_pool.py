"""
Django management command per gestire la reward pool
"""

from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal
from blockchain.blockchain import teocoin_service


class Command(BaseCommand):
    help = 'Gestisce la reward pool TeoCoin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Controlla il bilancio della reward pool',
        )
        parser.add_argument(
            '--transfer',
            type=float,
            help='Trasferisce TEO alla reward pool dall\'account admin',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Mostra lo status completo della reward pool',
        )

    def handle(self, *args, **options):
        if options['check'] or options['status']:
            self.check_reward_pool_status()
        
        if options['transfer']:
            amount = options['transfer']
            if amount <= 0:
                raise CommandError('L\'importo deve essere positivo')
            
            self.transfer_to_reward_pool(amount)

    def check_reward_pool_status(self):
        """
        Controlla lo status della reward pool
        """
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("REWARD POOL STATUS"))
        self.stdout.write("=" * 60)
        
        try:
            # Verifica configurazione
            if not teocoin_service.reward_pool_address:
                self.stdout.write(
                    self.style.ERROR("❌ ERRORE: Reward pool address non configurato")
                )
                return
            
            if not teocoin_service.reward_pool_private_key:
                self.stdout.write(
                    self.style.ERROR("❌ ERRORE: Reward pool private key non configurata")
                )
                return
            
            self.stdout.write(
                f"🏦 Reward Pool Address: {teocoin_service.reward_pool_address}"
            )
            
            # Verifica bilancio
            balance = teocoin_service.get_reward_pool_balance()
            self.stdout.write(f"💰 Current Balance: {balance} TEO")
            
            # Analizza stato bilancio
            if balance < Decimal('10'):
                self.stdout.write(
                    self.style.ERROR("🚨 CRITICO: Bilancio reward pool molto basso (< 10 TEO)")
                )
                self.stdout.write(
                    self.style.WARNING("  Consiglio: Trasferire almeno 100 TEO alla reward pool")
                )
            elif balance < Decimal('50'):
                self.stdout.write(
                    self.style.WARNING("⚠️  ATTENZIONE: Bilancio reward pool basso (< 50 TEO)")
                )
                self.stdout.write(
                    self.style.WARNING("  Consiglio: Considerare di aggiungere più fondi")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✅ Bilancio reward pool OK")
                )
            
            # Verifica bilancio admin se richiesto status completo
            if hasattr(self, 'check_admin_balance'):
                admin_balance = self.check_admin_balance()
                if admin_balance is not None:
                    self.stdout.write(f"👑 Admin Balance: {admin_balance} TEO")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ ERRORE nel controllo reward pool: {e}")
            )

    def transfer_to_reward_pool(self, amount_teo):
        """
        Trasferisce TEO dall'account admin alla reward pool
        """
        try:
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.SUCCESS(f"TRASFERIMENTO ALLA REWARD POOL: {amount_teo} TEO")
            )
            self.stdout.write("=" * 60)
            
            # Verifica configurazione admin
            if not teocoin_service.admin_private_key:
                raise CommandError("Admin private key non configurata")
            
            if not teocoin_service.reward_pool_address:
                raise CommandError("Reward pool address non configurato")
            
            # Mostra stato prima del trasferimento
            self.stdout.write("📊 Stato prima del trasferimento:")
            balance_before = teocoin_service.get_reward_pool_balance()
            self.stdout.write(f"   Reward Pool: {balance_before} TEO")
            
            # Effettua trasferimento
            self.stdout.write(f"💸 Trasferendo {amount_teo} TEO alla reward pool...")
            
            tx_hash = teocoin_service.transfer_tokens(
                from_private_key=teocoin_service.admin_private_key,
                to_address=teocoin_service.reward_pool_address,
                amount=Decimal(str(amount_teo))
            )
            
            if tx_hash:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Trasferimento completato!")
                )
                self.stdout.write(f"🔗 Transaction Hash: {tx_hash}")
                
                # Mostra stato dopo il trasferimento
                self.stdout.write("\n📊 Stato dopo il trasferimento:")
                balance_after = teocoin_service.get_reward_pool_balance()
                self.stdout.write(f"   Reward Pool: {balance_after} TEO")
                self.stdout.write(
                    f"   Differenza: +{balance_after - balance_before} TEO"
                )
                
            else:
                raise CommandError("Trasferimento fallito - nessun hash di transazione ricevuto")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ ERRORE nel trasferimento: {e}")
            )
            raise CommandError(f"Trasferimento fallito: {e}")
