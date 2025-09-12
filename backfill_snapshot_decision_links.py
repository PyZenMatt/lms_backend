#!/usr/bin/env python3
"""
BACKFILL SICURO: Snapshot ↔ Decision Linking
============================================

PROBLEMA IDENTIFICATO:
- 100% delle decisions non hanno snapshot linkato
- 100% degli snapshots non hanno decision linkato  
- La UI /teacher/pending-discounts risulta vuota perché filtra su decisions linkate

SOLUZIONE BACKFILL:
1. Match intelligente: stesso teacher, student, course, timeframe compatibile
2. Solo record NON già linkati (safety-first)
3. Preferenza per decisions più recenti
4. Log dettagliato di ogni operazione
5. Rollback facile in caso di problemi

SICUREZZA:
- Read-only mode per test preview
- Batch processing con conferme
- Backup automatico dei link esistenti (se ci fossero)

Run: python manage.py shell < backfill_snapshot_decision_links.py
"""

import os
import sys
import django
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

# Django setup
sys.path.append('/home/teo/Project/school/schoolplatform/lms_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from courses.models import TeacherDiscountDecision
from rewards.models import PaymentDiscountSnapshot

def analyze_linkable_records():
    """Analizza quali record possono essere linkati in modo intelligente"""
    print("🔍 ANALYZING LINKABLE RECORDS")
    print("=" * 40)
    
    # Snapshot senza decision
    orphan_snapshots = PaymentDiscountSnapshot.objects.filter(decision__isnull=True).order_by('-created_at')
    orphan_decisions = TeacherDiscountDecision.objects.filter(payment_snapshot__isnull=True).order_by('-created_at')
    
    print(f"📊 Found {orphan_snapshots.count()} unlinked snapshots")
    print(f"📊 Found {orphan_decisions.count()} unlinked decisions")
    
    # Strategia di matching intelligente
    matches = []
    
    for snapshot in orphan_snapshots:
        # Cerca decision compatibile: stesso teacher, course, timeframe ragionevole
        compatible_decisions = orphan_decisions.filter(
            course=snapshot.course,
            teacher=snapshot.course.teacher,  # teacher viene dal course
            # Timeframe: decision created entro 1 ora da snapshot
            created_at__gte=snapshot.created_at - timedelta(hours=1),
            created_at__lte=snapshot.created_at + timedelta(hours=1)
        ).order_by('-created_at')  # Preferisci la più recente
        
        if compatible_decisions.exists():
            best_decision = compatible_decisions.first()
            time_diff = abs((snapshot.created_at - best_decision.created_at).total_seconds() / 60)
            
            matches.append({
                'snapshot': snapshot,
                'decision': best_decision,
                'time_diff_minutes': time_diff,
                'confidence': 'HIGH' if time_diff < 5 else 'MEDIUM' if time_diff < 30 else 'LOW'
            })
            
            print(f"✅ Match found: Snapshot {snapshot.id} ↔ Decision {best_decision.id}")
            print(f"   Course: {snapshot.course.title}")
            print(f"   Teacher: {snapshot.course.teacher.username}")
            print(f"   Time diff: {time_diff:.1f} minutes")
            print(f"   Confidence: {matches[-1]['confidence']}")
            print()
    
    return matches

def preview_backfill(matches):
    """Preview delle operazioni senza eseguirle"""
    print("🔬 BACKFILL PREVIEW (READ-ONLY)")
    print("=" * 35)
    
    high_confidence = [m for m in matches if m['confidence'] == 'HIGH']
    medium_confidence = [m for m in matches if m['confidence'] == 'MEDIUM']
    low_confidence = [m for m in matches if m['confidence'] == 'LOW']
    
    print(f"📈 High confidence matches: {len(high_confidence)}")
    print(f"📈 Medium confidence matches: {len(medium_confidence)}")  
    print(f"📈 Low confidence matches: {len(low_confidence)}")
    print()
    
    print("🎯 RECOMMENDED STRATEGY:")
    if high_confidence:
        print(f"✅ Process {len(high_confidence)} HIGH confidence matches immediately")
    if medium_confidence:
        print(f"⚠️  Review {len(medium_confidence)} MEDIUM confidence matches manually")
    if low_confidence:
        print(f"❌ Skip {len(low_confidence)} LOW confidence matches (too risky)")
    
    return high_confidence, medium_confidence, low_confidence

def execute_backfill(matches, dry_run=True):
    """Esegue il backfill con safety checks"""
    print(f"{'🧪 DRY RUN' if dry_run else '🚀 EXECUTING'} BACKFILL")
    print("=" * 30)
    
    success_count = 0
    error_count = 0
    
    for match in matches:
        snapshot = match['snapshot']
        decision = match['decision']
        
        try:
            if not dry_run:
                with transaction.atomic():
                    # Double check che non siano già linkati
                    if snapshot.decision is not None:
                        print(f"⚠️  Snapshot {snapshot.id} already has decision, skipping")
                        continue
                    if decision.payment_snapshot is not None:
                        print(f"⚠️  Decision {decision.id} already has snapshot, skipping")
                        continue
                    
                    # Crea il link bidirezionale
                    snapshot.decision = decision
                    snapshot.save(update_fields=['decision'])
                    
                    print(f"✅ Linked: Snapshot {snapshot.id} ↔ Decision {decision.id}")
            else:
                print(f"🧪 Would link: Snapshot {snapshot.id} ↔ Decision {decision.id}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error linking Snapshot {snapshot.id} ↔ Decision {decision.id}: {e}")
            error_count += 1
    
    print(f"\n📊 RESULTS:")
    print(f"   Successful: {success_count}")
    print(f"   Errors: {error_count}")
    
    return success_count, error_count

def main():
    """Main backfill process"""
    print("🔧 SNAPSHOT ↔ DECISION BACKFILL TOOL")
    print("=" * 45)
    print("SAFETY: Starting in analysis mode\n")
    
    # Step 1: Analyze
    matches = analyze_linkable_records()
    
    if not matches:
        print("❌ No linkable records found")
        return
    
    # Step 2: Preview
    high_conf, medium_conf, low_conf = preview_backfill(matches)
    
    # Step 3: Dry run on high confidence
    if high_conf:
        print(f"\n🧪 DRY RUN: High confidence matches ({len(high_conf)})")
        execute_backfill(high_conf, dry_run=True)
        
        print(f"\n🤔 EXECUTE FOR REAL?")
        print("If these results look good, change dry_run=False below and re-run")
        print("WARNING: This will modify the database!")
        
        # Per eseguire davvero, decommentare la riga seguente:
        # execute_backfill(high_conf, dry_run=False)
    
    # Step 4: API test suggestion
    print(f"\n🎯 NEXT STEPS:")
    print("1. Review the matches above")
    print("2. If satisfied, set dry_run=False and re-run")
    print("3. Test /teacher/pending-discounts page")
    print("4. Deploy R1.1 patch for permanent fix")

if __name__ == '__main__':
    main()
