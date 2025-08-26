from django.db import migrations, models


def deduplicate_snapshots(apps, schema_editor):
    PaymentDiscountSnapshot = apps.get_model("rewards", "PaymentDiscountSnapshot")
    # Find order_ids with more than one snapshot
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT order_id, COUNT(*) as cnt FROM rewards_payment_discount_snapshot GROUP BY order_id HAVING COUNT(*)>1"
        )
        rows = cursor.fetchall()
    duplicates = [r[0] for r in rows]

    for order_id in duplicates:
        snaps = list(PaymentDiscountSnapshot.objects.filter(order_id=order_id).order_by("-created_at", "-id"))
        # Keep the first (most recent), delete the others
        keep = snaps[0]
        to_delete = snaps[1:]
        ids = [s.id for s in to_delete]
        if ids:
            PaymentDiscountSnapshot.objects.filter(id__in=ids).delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("rewards", "0005_tier_paymentdiscountsnapshot"),
    ]

    operations = [
        migrations.RunPython(deduplicate_snapshots, reverse_code=noop),
        migrations.AddConstraint(
            model_name="paymentdiscountsnapshot",
            constraint=models.UniqueConstraint(fields=["order_id"], name="unique_order_id_snapshot"),
        ),
    ]
