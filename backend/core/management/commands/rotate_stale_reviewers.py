from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from courses.models import ExerciseReview, ExerciseSubmission, Notification
from users.models import User
import random

class Command(BaseCommand):
    help = 'Sostituisce i reviewer inattivi oltre 24 ore'

    def handle(self, *args, **kwargs):
        timeout = timezone.now() - timedelta(hours=24)
        stale_reviews = ExerciseReview.objects.filter(score__isnull=True, assigned_at__lte=timeout)

        for review in stale_reviews:
            submission = review.submission
            current_reviewers = submission.reviewers.all()
            old_reviewer = review.reviewer
            review.delete()

            candidates = User.objects.filter(role='student').exclude(
                id__in=current_reviewers.values_list('id', flat=True)
            ).exclude(id=submission.student.id)

            if not candidates.exists():
                continue

            new_reviewer = random.choice(candidates)

            ExerciseReview.objects.create(
                submission=submission,
                reviewer=new_reviewer,
                assigned_at=timezone.now()
            )
            submission.reviewers.add(new_reviewer)

            Notification.objects.create(
                user=new_reviewer,
                message=f"Hai ricevuto una nuova richiesta di review (rimpiazzo) per l'esercizio: {submission.exercise.title}"
            )

            Notification.objects.create(
                user=old_reviewer,
                message=f"Sei stato rimpiazzato come reviewer per l'esercizio: {submission.exercise.title}"
            )

        self.stdout.write(self.style.SUCCESS("Reviewer scaduti sostituiti con successo."))