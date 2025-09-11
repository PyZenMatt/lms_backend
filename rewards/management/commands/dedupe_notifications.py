from django.core.management.base import BaseCommand
from notifications.models import Notification
from collections import defaultdict

class Command(BaseCommand):
    help = "Deduplicate teocoin discount notifications by (user, notification_type, decision_id) keeping the most recent or urgent"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")

    def handle(self, *args, **options):
        dry = options.get("dry_run")
        # We'll collect keys as (user_id, notification_type, related_object_id)
        groups = defaultdict(list)
        qs = Notification.objects.filter(notification_type__in=["teocoin_discount_pending", "teocoin_discount_pending_urgent"]).order_by("user_id", "notification_type", "related_object_id", "-created_at")
        for n in qs:
            key = (n.user_id, n.notification_type, n.related_object_id)
            groups[key].append(n)

        to_delete = []
        for key, items in groups.items():
            if len(items) <= 1:
                continue
            # Keep the most recent urgent if present else the most recent overall
            # items are ordered with most recent first
            keep = items[0]
            for other in items[1:]:
                to_delete.append(other)

        if not to_delete:
            self.stdout.write(self.style.SUCCESS("No duplicates found."))
            return

        self.stdout.write(f"Found {len(to_delete)} duplicate notifications to remove.")
        for n in to_delete:
            self.stdout.write(f" - {n.id} user={n.user_id} type={n.notification_type} related={n.related_object_id} created={n.created_at}")

        if dry:
            self.stdout.write(self.style.WARNING("Dry run - no deletions performed."))
            return

        # Delete
        ids = [n.id for n in to_delete]
        Notification.objects.filter(id__in=ids).delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {len(ids)} notifications."))
