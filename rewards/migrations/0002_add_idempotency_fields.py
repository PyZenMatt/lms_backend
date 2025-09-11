# Generated migration for idempotency and status tracking

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rewards', '0001_initial'),
    ]

    operations = [
        # Add new fields for idempotency and state tracking
        migrations.AddField(
            model_name='paymentdiscountsnapshot',
            name='checkout_session_id',
            field=models.CharField(blank=True, db_index=True, max_length=120, null=True),
        ),
        migrations.AddField(
            model_name='paymentdiscountsnapshot',
            name='wallet_hold_id',
            field=models.CharField(blank=True, help_text='TEO wallet hold transaction ID', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='paymentdiscountsnapshot',
            name='wallet_capture_id',
            field=models.CharField(blank=True, help_text='TEO wallet capture transaction ID', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='paymentdiscountsnapshot',
            name='applied_at',
            field=models.DateTimeField(blank=True, help_text='When discount was applied (hold created)', null=True),
        ),
        migrations.AddField(
            model_name='paymentdiscountsnapshot',
            name='confirmed_at',
            field=models.DateTimeField(blank=True, help_text='When payment confirmed (hold captured)', null=True),
        ),
        migrations.AddField(
            model_name='paymentdiscountsnapshot',
            name='failed_at',
            field=models.DateTimeField(blank=True, help_text='When payment failed (hold released)', null=True),
        ),
        
        # Update status field choices to include new states
        migrations.AlterField(
            model_name='paymentdiscountsnapshot',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('applied', 'Applied (Pending Payment)'),
                    ('confirmed', 'Confirmed'),
                    ('failed', 'Failed'),
                    ('expired', 'Expired'),
                    ('superseded', 'Superseded'),
                    ('pending', 'Pending'),  # Legacy
                    ('closed', 'Closed'),   # Legacy
                ],
                default='draft',
                db_index=True,
                max_length=20
            ),
        ),
        
        # Remove old constraint and add new idempotency constraint
        migrations.RemoveConstraint(
            model_name='paymentdiscountsnapshot',
            name='uniq_snapshot_by_idempotency_key_pending',
        ),
        
        # Add new idempotency constraint for checkout sessions
        migrations.AddConstraint(
            model_name='paymentdiscountsnapshot',
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ('checkout_session_id__isnull', False),
                    ('status__in', ['applied', 'confirmed'])
                ),
                fields=['student', 'course', 'checkout_session_id'],
                name='uniq_discount_per_checkout_session'
            ),
        ),
        
        # Re-add legacy constraint with different condition
        migrations.AddConstraint(
            model_name='paymentdiscountsnapshot',
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ('idempotency_key__isnull', False),
                    ('status', 'pending')
                ),
                fields=['idempotency_key'],
                name='uniq_snapshot_by_idempotency_key_pending'
            ),
        ),
    ]
