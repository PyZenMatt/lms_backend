#!/usr/bin/env python3
"""
Script per deduplicare i PaymentDiscountSnapshot esistenti nel database.

Identifica e risolve:
- Snapshot duplicati per la stessa combinazione user+course+checkout_session_id
- Snapshot orfani senza hold corrispondente
- Hold non rilasciati per snapshot scaduti
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
django.setup()

from django.db import transaction
from django.db.models import Count, Q
from payments.models import PaymentDiscountSnapshot
from blockchain.models import DBTeoCoinTransaction
from services.wallet_hold_service import WalletHoldService

class SnapshotDeduplicator:
    """Gestore per la deduplicazione degli snapshot"""
    
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.hold_service = WalletHoldService()
        self.stats = {
            'duplicates_found': 0,
            'duplicates_resolved': 0,
            'orphaned_holds_released': 0,
            'teo_refunded': 0,
            'snapshots_deleted': 0
        }
    
    def find_duplicate_snapshots(self):
        """Trova snapshot duplicati"""
        print("🔍 Finding duplicate snapshots...")
        
        # Trova gruppi con più snapshot per la stessa combinazione
        duplicates = PaymentDiscountSnapshot.objects.values(
            'user', 'course', 'checkout_session_id'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        duplicate_groups = []
        for dup in duplicates:
            snapshots = PaymentDiscountSnapshot.objects.filter(
                user_id=dup['user'],
                course_id=dup['course'],
                checkout_session_id=dup['checkout_session_id']
            ).order_by('created_at')
            
            duplicate_groups.append(list(snapshots))
            
        self.stats['duplicates_found'] = len(duplicate_groups)
        print(f"  Found {len(duplicate_groups)} duplicate groups")
        
        return duplicate_groups
    
    def resolve_duplicate_group(self, snapshots):
        """Risolvi un gruppo di snapshot duplicati"""
        if len(snapshots) <= 1:
            return
            
        print(f"  Resolving group: {len(snapshots)} snapshots for user {snapshots[0].user_id}")
        
        # Mantieni solo l'ultimo snapshot (più recente)
        keeper = snapshots[-1]
        to_remove = snapshots[:-1]
        
        total_refund = Decimal('0')
        
        for snapshot in to_remove:
            print(f"    Removing snapshot {snapshot.id} (created: {snapshot.created_at})")
            
            # Rilascia l'hold se presente
            if snapshot.wallet_hold_id:
                try:
                    released_amount = self.hold_service.release_hold(
                        snapshot.wallet_hold_id, 
                        'Duplicate snapshot cleanup'
                    )
                    if released_amount:
                        total_refund += released_amount
                        print(f"      Released hold: {released_amount} TEO")
                except Exception as e:
                    print(f"      Warning: Could not release hold {snapshot.wallet_hold_id}: {e}")
            
            # Elimina il snapshot
            if not self.dry_run:
                snapshot.delete()
                self.stats['snapshots_deleted'] += 1
        
        # Assicurati che il keeper sia nello stato corretto
        if keeper.status == 'draft' and not self.dry_run:
            keeper.status = 'applied'
            keeper.save()
            print(f"    Updated keeper snapshot {keeper.id} status to 'applied'")
        
        self.stats['teo_refunded'] += total_refund
        self.stats['duplicates_resolved'] += 1
        
        return total_refund
    
    def find_orphaned_holds(self):
        """Trova hold orfani (snapshot eliminati ma hold ancora attivi)"""
        print("🔍 Finding orphaned holds...")
        
        # Trova snapshot con hold che sono in stato 'superseded' da più di 1 ora
        cutoff_time = datetime.now() - timedelta(hours=1)
        
        orphaned_snapshots = PaymentDiscountSnapshot.objects.filter(
            status='superseded',
            updated_at__lt=cutoff_time,
            wallet_hold_id__isnull=False
        )
        
        print(f"  Found {orphaned_snapshots.count()} potentially orphaned holds")
        return list(orphaned_snapshots)
    
    def cleanup_orphaned_holds(self, orphaned_snapshots):
        """Pulisci hold orfani"""
        total_released = Decimal('0')
        
        for snapshot in orphaned_snapshots:
            print(f"  Releasing orphaned hold for snapshot {snapshot.id}")
            
            try:
                released_amount = self.hold_service.release_hold(
                    snapshot.wallet_hold_id,
                    'Orphaned hold cleanup'
                )
                if released_amount:
                    total_released += released_amount
                    
                # Aggiorna il snapshot
                if not self.dry_run:
                    snapshot.wallet_hold_id = None
                    snapshot.save()
                    
                print(f"    Released: {released_amount} TEO")
                
            except Exception as e:
                print(f"    Warning: Could not release hold {snapshot.wallet_hold_id}: {e}")
        
        self.stats['orphaned_holds_released'] = len(orphaned_snapshots)
        self.stats['teo_refunded'] += total_released
        
        return total_released
    
    def verify_constraints(self):
        """Verifica che i constraint siano rispettati dopo la pulizia"""
        print("🔍 Verifying database constraints...")
        
        # Verifica unicità per user+course+checkout_session_id tra snapshot attivi
        active_duplicates = PaymentDiscountSnapshot.objects.filter(
            status__in=['applied', 'draft']
        ).values(
            'user', 'course', 'checkout_session_id'
        ).annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if active_duplicates.exists():
            print(f"  ⚠️  WARNING: {active_duplicates.count()} active duplicate groups still exist!")
            return False
        else:
            print("  ✅ No active duplicates found")
            return True
    
    def generate_report(self):
        """Genera report delle operazioni"""
        print("\n" + "="*50)
        print("📊 DEDUPLICATION REPORT")
        print("="*50)
        print(f"Duplicate groups found: {self.stats['duplicates_found']}")
        print(f"Duplicate groups resolved: {self.stats['duplicates_resolved']}")
        print(f"Snapshots deleted: {self.stats['snapshots_deleted']}")
        print(f"Orphaned holds released: {self.stats['orphaned_holds_released']}")
        print(f"Total TEO refunded: {self.stats['teo_refunded']}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        
        if self.dry_run:
            print("\n⚠️  This was a DRY RUN - no changes were made!")
            print("Run with --live to apply changes.")
    
    def run_deduplication(self):
        """Esegui il processo completo di deduplicazione"""
        print("🚀 Starting snapshot deduplication...")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print("="*50)
        
        try:
            with transaction.atomic():
                # Step 1: Trova e risolvi duplicati
                duplicate_groups = self.find_duplicate_snapshots()
                for group in duplicate_groups:
                    self.resolve_duplicate_group(group)
                
                # Step 2: Pulisci hold orfani
                orphaned = self.find_orphaned_holds()
                if orphaned:
                    self.cleanup_orphaned_holds(orphaned)
                
                # Step 3: Verifica constraint
                constraints_ok = self.verify_constraints()
                
                # Step 4: Report
                self.generate_report()
                
                # Se è un dry run, fai rollback
                if self.dry_run:
                    print("\n🔄 Rolling back dry run transaction...")
                    transaction.set_rollback(True)
                
                return constraints_ok
                
        except Exception as e:
            print(f"❌ Error during deduplication: {e}")
            return False

def main():
    """Funzione principale"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deduplicate payment discount snapshots')
    parser.add_argument('--live', action='store_true', 
                       help='Apply changes (default is dry run)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    deduplicator = SnapshotDeduplicator(dry_run=not args.live)
    success = deduplicator.run_deduplication()
    
    if success:
        print("✅ Deduplication completed successfully!")
        return 0
    else:
        print("❌ Deduplication failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
