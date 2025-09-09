from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.models import ExerciseReview, PeerReviewFeedbackItem
from courses.utils.peer_feedback_parser import parse_peer_review_blob


class Command(BaseCommand):
    help = "Normalize legacy ExerciseReview.comment blobs into PeerReviewFeedbackItem rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Show what would be created without saving",
        )
        parser.add_argument(
            "--submission-id",
            type=int,
            dest="submission_id",
            help="Only process reviews for the given ExerciseSubmission id",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        submission_id = options.get("submission_id")

        qs = ExerciseReview.objects.all()
        if submission_id:
            qs = qs.filter(submission_id=submission_id)

        total_reviews = qs.count()
        self.stdout.write(f"Found {total_reviews} reviews to inspect")

        created = 0
        skipped = 0

        for review in qs.order_by("id"):
            blob = (review.comment or "").strip()
            if not blob:
                skipped += 1
                continue

            parsed = parse_peer_review_blob(blob)
            # parsed is dict with canonical keys: highlights, suggestions, final
            items_to_create = []
            for area_key, text in parsed.items():
                if not text:
                    continue
                # avoid creating duplicates if there are already feedback items linked to this review+area
                exists = PeerReviewFeedbackItem.objects.filter(review=review, area=area_key).exists()
                if exists:
                    self.stdout.write(f"Skipping existing items for review {review.id} area {area_key}")
                    continue

                items_to_create.append(
                    PeerReviewFeedbackItem(
                        submission_id=review.submission_id,
                        review=review,
                        reviewer_id=review.reviewer_id,
                        area=area_key,
                        content=text,
                    )
                )

            if not items_to_create:
                skipped += 1
                continue

            if dry_run:
                self.stdout.write(f"[DRY RUN] Review {review.id}: would create {len(items_to_create)} items")
                for it in items_to_create:
                    self.stdout.write(f"   - area={it.area} content={it.content[:80]!r}")
                created += len(items_to_create)
                continue

            # create within transaction
            with transaction.atomic():
                PeerReviewFeedbackItem.objects.bulk_create(items_to_create)
                created += len(items_to_create)

        self.stdout.write(f"Created {created} items, skipped {skipped} reviews")