from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0013_add_decision_link'),
        ('rewards', '0014_add_idempotency_key'),
    ]

    operations = [
        # Remove any pre-existing constraint with previous name if present
        migrations.RunSQL(
            sql="""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uniq_snapshot_by_idempotency_key') THEN
                    ALTER TABLE rewards_payment_discount_snapshot DROP CONSTRAINT IF EXISTS uniq_snapshot_by_idempotency_key;
                END IF;
            END$$;
            """,
            reverse_sql="""
            -- no-op reverse
            """,
        ),
        migrations.AddConstraint(
            model_name='paymentdiscountsnapshot',
            constraint=models.UniqueConstraint(
                fields=['idempotency_key'],
                condition=Q(idempotency_key__isnull=False) & Q(status='pending'),
                name='uniq_snapshot_by_idempotency_key_pending',
            ),
        ),
    ]
