import logging
import random

from courses.models import (
    Course,
    Exercise,
    ExerciseReview,
    ExerciseSubmission,
    Lesson,
    PeerReviewFeedbackItem,
)
from courses.serializers import (
    ExerciseSerializer,
    ExerciseSubmissionSerializer,
    PeerReviewFeedbackItemSerializer,
)
from courses.utils.peer_feedback_parser import parse_peer_review_blob
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from notifications.models import Notification
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from users.permissions import IsTeacher
from django.db.models import Count, Avg, Q, Max

logger = logging.getLogger(__name__)


def create_reward_transaction(
    user, amount, transaction_type, submission_id, reference: str | None = None
):
    """
    Create a reward transaction for a user using DB-based TeoCoin service.
    Maps specific reward types to DB-allowed transaction types and encodes the
    semantic type in the description for auditing.
    """
    # Convert amount to Decimal for DB service
    from decimal import Decimal

    from services.db_teocoin_service import db_teocoin_service

    amount_decimal = Decimal(str(amount))
    # Encode original semantic type in description for auditing, but map to a
    # valid DB transaction type (choices) for persistence
    pretty = transaction_type.replace("_", " ").title()
    suffix = f" | ref={reference}" if reference else ""
    description = f"[{transaction_type}] {pretty} (submission {submission_id}){suffix}"
    mapped_type = "bonus"

    # Use DB service to add balance and create transaction with mapped type
    success = db_teocoin_service.add_balance(
        user=user,
        amount=amount_decimal,
        transaction_type=mapped_type,
        description=description,
    )

    if success:
        # Return a mock object that mimics the old BlockchainTransaction for compatibility
        class MockTransaction:
            def __init__(self, user, amount, transaction_type, submission_id):
                self.id = f"db_{submission_id}_{transaction_type}"
                self.user = user
                self.amount = amount
                self.transaction_type = transaction_type
                self.submission_id = submission_id
                self.success = True

        return MockTransaction(user, amount_decimal, transaction_type, submission_id)
    else:
        logger.error(
            f"Failed to create reward transaction for {user.email}: {amount} {transaction_type}"
        )
        return None


class ExerciseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries
        return Exercise.objects.select_related(
            "lesson", "lesson__course", "lesson__course__teacher"
        ).prefetch_related("submissions", "submissions__student")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CreateExerciseView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request):
        course_id = request.data.get("course_id")
        lesson_id = request.data.get("lesson_id")

        if not course_id or not lesson_id:
            return Response(
                {"error": "Gli ID del corso e della lezione sono obbligatori."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch course (do not restrict by teacher here) then apply permission rules.
        course = get_object_or_404(Course, id=course_id)
        # Owners (course.teacher) and staff/superusers can add exercises even if the
        # course is not yet approved. Other users may only add exercises to approved courses.
        if not (request.user.is_staff or request.user.is_superuser or course.teacher == request.user):
            if not course.is_approved:
                raise PermissionDenied(
                    "Non puoi aggiungere esercizi a un corso non approvato."
                )
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

        data = request.data.copy()
        data["lesson"] = lesson.id

        serializer = ExerciseSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmissionDetailForReviewerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(ExerciseSubmission, id=submission_id)
        # Permesso: reviewer assegnato, staff, teacher del corso, o studente owner
        is_owner = (
            submission.student.id == request.user.id if submission.student else False
        )
        is_staff = getattr(request.user, "is_staff", False)
        is_course_teacher = False
        if (
            submission.exercise
            and submission.exercise.lesson
            and submission.exercise.lesson.course
        ):
            is_course_teacher = (
                submission.exercise.lesson.course.teacher_id == request.user.id
            )
        is_reviewer = submission.reviewers.filter(id=request.user.id).exists()

        if not (is_owner or is_staff or is_course_teacher or is_reviewer):
            return Response({"detail": "Non autorizzato."}, status=403)

        return Response(ExerciseSubmissionSerializer(submission).data, status=200)


class AreaFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id):
        raw_area = (request.query_params.get('area') or '').strip().lower()
        if not raw_area:
            return Response({'detail': 'area query param required'}, status=400)

        submission = get_object_or_404(ExerciseSubmission, id=submission_id)

        # permission: student owner or staff or teacher of course or reviewer
        is_owner = submission.student_id == request.user.id if getattr(submission, 'student_id', None) is not None else (getattr(submission, 'student', None) and submission.student.id == request.user.id)
        is_staff = getattr(request.user, 'is_staff', False)
        is_course_teacher = False
        if getattr(submission, 'exercise', None) and getattr(submission.exercise, 'lesson', None) and getattr(submission.exercise.lesson, 'course', None):
            is_course_teacher = submission.exercise.lesson.course.teacher_id == request.user.id
        is_reviewer = submission.reviewers.filter(id=request.user.id).exists() if hasattr(submission, 'reviewers') else False
        if not (is_owner or is_staff or is_course_teacher or is_reviewer):
            return Response({'detail': 'Forbidden'}, status=403)

        # Normalize requested area to canonical backend keys. Accept both
        # legacy frontend values and canonical ones used by FE: technical,
        # creative, following, as well as narrative keys highlights/suggestions/final.
        explicit_areas = {'highlights', 'suggestions', 'final'}
        legacy_map = {
            'technique': 'technical',
            'composition': 'following',
            'creativity': 'creative',
            'technical': 'technical',
            'creative': 'creative',
            'following': 'following',
        }

        area_key = legacy_map.get(raw_area, raw_area)

        explicit_items = []
        legacy_items = []

        # If caller asked for an explicit peer-review area, fetch those items
        if area_key in explicit_areas:
            explicit_qs = PeerReviewFeedbackItem.objects.filter(submission=submission, area=area_key).order_by('created_at')
            # Normalize explicit items to expose a canonical `comment` text field
            explicit_items = list(PeerReviewFeedbackItemSerializer(explicit_qs, many=True, context={'request': request}).data)
            for it in explicit_items:
                # keep backward-compatible `content` but expose `comment` as primary textual field
                if it.get('comment') is None:
                    it['comment'] = it.get('content')

        # If caller asked for one of the legacy frontend keys or canonical per-area keys,
        # derive items from existing ExerciseReview rows and expose a normalized `comment` field.
        if area_key in legacy_map.values() or area_key in explicit_areas:
            # gather reviewed ExerciseReview rows
            reviews = submission.reviews.filter(reviewed_at__isnull=False).order_by('reviewed_at') if hasattr(submission, 'reviews') else []
            for r in reviews:
                # technical / highlights
                if area_key == 'technical' or area_key == 'highlights':
                    if getattr(r, 'technical', None) is not None:
                        legacy_items.append({
                            'id': f'review-{getattr(r, "id", "")}-tech',
                            'reviewer': {'id': r.reviewer.id, 'name': getattr(r.reviewer, 'username', None)} if getattr(r, 'reviewer', None) else None,
                            'area': area_key,
                            # prefer dedicated per-area comment fields where present, else fallback to the generic comment
                            'comment': getattr(r, 'technical_comment', None) or getattr(r, 'comment', None),
                            'created_at': r.reviewed_at,
                        })
                    # highlights special: also include composite breakdown if present
                    if area_key == 'highlights' and (getattr(r, 'technical', None) is not None or getattr(r, 'creative', None) is not None or getattr(r, 'following', None) is not None):
                        parts = []
                        if getattr(r, 'technical', None) is not None:
                            parts.append(f"Technical: {r.technical}/5")
                        if getattr(r, 'creative', None) is not None:
                            parts.append(f"Creative: {r.creative}/5")
                        if getattr(r, 'following', None) is not None:
                            parts.append(f"Following: {r.following}/5")
                        legacy_items.append({
                            'id': f'review-{getattr(r, "id", "")}-highlights',
                            'reviewer': {'id': r.reviewer.id, 'name': getattr(r.reviewer, 'username', None)} if getattr(r, 'reviewer', None) else None,
                            'area': area_key,
                            'comment': None,  # prefer explicit strengths_comment / parsed highlights from detail; keep None here for frontend fallback
                            'created_at': r.reviewed_at,
                        })
                # following / composition
                if area_key == 'following':
                    if getattr(r, 'following', None) is not None:
                        legacy_items.append({
                            'id': f'review-{getattr(r, "id", "")}-comp',
                            'reviewer': {'id': r.reviewer.id, 'name': getattr(r.reviewer, 'username', None)} if getattr(r, 'reviewer', None) else None,
                            'area': area_key,
                            'comment': getattr(r, 'following_comment', None) or getattr(r, 'comment', None),
                            'created_at': r.reviewed_at,
                        })
                # creative / creativity
                if area_key == 'creative':
                    if getattr(r, 'creative', None) is not None:
                        legacy_items.append({
                            'id': f'review-{getattr(r, "id", "")}-crea',
                            'reviewer': {'id': r.reviewer.id, 'name': getattr(r.reviewer, 'username', None)} if getattr(r, 'reviewer', None) else None,
                            'area': area_key,
                            'comment': getattr(r, 'creative_comment', None) or getattr(r, 'comment', None),
                            'created_at': r.reviewed_at,
                        })
                # suggestions -> recommendations
                if area_key == 'suggestions':
                    if getattr(r, 'recommendations', None):
                        try:
                            recs = r.recommendations if isinstance(r.recommendations, list) else [str(r.recommendations)]
                        except Exception:
                            recs = [str(r.recommendations)]
                        for idx, rec in enumerate(recs):
                            legacy_items.append({
                                'id': f'review-{getattr(r, "id", "")}-rec-{idx}',
                                'reviewer': {'id': r.reviewer.id, 'name': getattr(r.reviewer, 'username', None)} if getattr(r, 'reviewer', None) else None,
                                'area': area_key,
                                'comment': rec,
                                'created_at': r.reviewed_at,
                            })
                # final -> comment
                if area_key == 'final':
                    if getattr(r, 'comment', None):
                        legacy_items.append({
                            'id': f'review-{getattr(r, "id", "")}-comment',
                            'reviewer': {'id': r.reviewer.id, 'name': getattr(r.reviewer, 'username', None)} if getattr(r, 'reviewer', None) else None,
                            'area': area_key,
                            'comment': r.comment,
                            'created_at': r.reviewed_at,
                        })

        # Combine explicit items and legacy items (explicit items first), then sort by created_at
        combined = []
        combined.extend(explicit_items)
        combined.extend(legacy_items)

        def _key(x):
            v = x.get('created_at')
            if v is None:
                return 0
            # If serializer produced a string, try to parse it
            if isinstance(v, str):
                dt = parse_datetime(v)
            else:
                dt = v
            if dt is None:
                return 0
            # Ensure we return a numeric timestamp for stable sorting
            try:
                if timezone.is_aware(dt):
                    return dt.timestamp()
                # make naive datetimes timezone-aware using current timezone
                aware = timezone.make_aware(dt)
                return aware.timestamp()
            except Exception:
                # As a last resort, fall back to string comparison
                return str(v)

        combined_sorted = sorted(combined, key=_key)

        received = len(combined_sorted)
        expected = 3

        # Ensure output items only contain reviewer and a textual `comment` field
        out_items = []
        for it in combined_sorted:
            out_items.append({
                'reviewer': it.get('reviewer'),
                'comment': it.get('comment'),
                'created_at': it.get('created_at'),
            })

        return Response({'submission_id': submission.id, 'area': area_key, 'received': received, 'expected': expected, 'items': out_items}, status=200)


class SubmitExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, id=exercise_id)
        course = exercise.lesson.course

        if not course.students.filter(id=request.user.id).exists():
            return Response(
                {"error": "Non hai acquistato il corso associato a questo esercizio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if ExerciseSubmission.objects.filter(
            exercise=exercise, student=request.user
        ).exists():
            return Response(
                {"error": "Hai già sottomesso questo esercizio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prendi la soluzione dal body della richiesta
        content = request.data.get("content", "")

        submission = ExerciseSubmission.objects.create(
            student=request.user, exercise=exercise, content=content
        )

        eligible_reviewers = User.objects.filter(
            role__in=["student", "teacher"]
        ).exclude(id=request.user.id)
        reviewers = random.sample(
            list(eligible_reviewers), min(3, eligible_reviewers.count())
        )

        for reviewer in reviewers:
            ExerciseReview.objects.create(submission=submission, reviewer=reviewer)
            submission.reviewers.add(reviewer)
            Notification.objects.create(
                user=reviewer,
                message=f"Hai un nuovo esercizio da valutare: {exercise.title}",
                notification_type="review_assigned",
                related_object_id=submission.id,
                link=f"/review/{submission.id}",
            )

        submission.save()
        # Ritorna i dati reali della submission creata, così il frontend si sincronizza subito
        return Response(
            ExerciseSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )


class ReviewExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, submission_id=None, exercise_id=None):
        """
        Accept either a submission_id (preferred) or an exercise_id in the URL.
        If called with an exercise_id, resolve the ExerciseSubmission assigned to the
        current user (reviewer) for that exercise and use it. This keeps backward
        compatibility with endpoints that post using either parameter name.
        """
        submission = None
        # If exercise_id was provided (URLs declare <exercise_id>), try to find
        # the submission for this exercise assigned to the current reviewer.
        if exercise_id is not None and submission_id is None:
            submission = (
                ExerciseSubmission.objects.filter(exercise_id=exercise_id)
                .filter(reviewers__id=request.user.id)
                .first()
            )
            if not submission:
                # No submission assigned to this reviewer for that exercise
                return Response(
                    {"detail": "Nessuna submission assegnata a te per questo esercizio."},
                    status=404,
                )

        # Fallback to submission_id if provided or if the exercise lookup failed
        if submission is None and submission_id is not None:
            submission = get_object_or_404(ExerciseSubmission, id=submission_id)

        # If still no submission, return not found
        if submission is None:
            return Response({"error": "Submission non trovata."}, status=404)

        if submission.student == request.user:
            return Response(
                {"error": "Non puoi valutare il tuo stesso esercizio."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not submission.reviewers.filter(id=request.user.id).exists():
            return Response(
                {"error": "Non sei uno dei valutatori assegnati."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Accept either legacy `score` (1-10) or breakdown fields (1-5)
        score = request.data.get("score")
        technical = request.data.get("technical")
        creative = request.data.get("creative")
        following = request.data.get("following")
        comment = request.data.get("comment")
        recommendations = request.data.get("recommendations")

        review = get_object_or_404(
            ExerciseReview, submission=submission, reviewer=request.user
        )
        if review.score is not None or (review.technical is not None and review.creative is not None and review.following is not None):
            return Response(
                {"error": "Hai già valutato questo esercizio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate and apply breakdown if present
        if technical is not None or creative is not None or following is not None:
            try:
                t = int(technical) if technical is not None else None
                c = int(creative) if creative is not None else None
                f = int(following) if following is not None else None
            except Exception:
                return Response({"error": "I breakdown devono essere numeri interi."}, status=status.HTTP_400_BAD_REQUEST)
            # If any field present, require all three to be integer 1..5 (allow nulls only if explicitly skipped)
            if any(v is None for v in (t, c, f)):
                return Response({"error": "Devi inviare technical, creative e following o nessuno."}, status=status.HTTP_400_BAD_REQUEST)
            if not all(1 <= v <= 5 for v in (t, c, f)):
                return Response({"error": "I valori breakdown devono essere compresi tra 1 e 5."}, status=status.HTTP_400_BAD_REQUEST)
            review.technical = t
            review.creative = c
            review.following = f
            # compute legacy score in 1-10 scale for compatibility
            review.score = int(round(((t + c + f) / 3.0) * 2.0))
        else:
            # Fallback to legacy score
            if not score or not (1 <= int(score) <= 10):
                return Response(
                    {"error": "Il punteggio deve essere compreso tra 1 e 10."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            review.score = int(score)

        # optional comment and recommendations
        if comment is not None:
            review.comment = str(comment)
        # Optional per-area textual comments (canonical fields for frontend)
        # Accept null/empty values (they will be left as None/blank) but persist if provided
        technical_comment = request.data.get("technical_comment")
        creative_comment = request.data.get("creative_comment")
        following_comment = request.data.get("following_comment")

        if technical_comment is not None:
            review.technical_comment = str(technical_comment) if technical_comment is not None else None
        if creative_comment is not None:
            review.creative_comment = str(creative_comment) if creative_comment is not None else None
        if following_comment is not None:
            review.following_comment = str(following_comment) if following_comment is not None else None
        if recommendations is not None:
            # Expecting list-like or JSON string
            review.recommendations = recommendations

        review.reviewed_at = timezone.now()
        review.save()

        # Premio immediato al reviewer: 2 TEO per ogni review completata (idempotente)
        try:
            from blockchain.models import DBTeoCoinTransaction

            exists = (
                DBTeoCoinTransaction.objects.filter(
                    user=request.user, transaction_type="bonus"
                )
                .filter(
                    Q(description__contains="[review_reward]")
                    & Q(description__contains=f"ref=review:{review.id}")
                )
                .exists()
            )
            if not exists:
                _ = create_reward_transaction(
                    user=request.user,
                    amount=2,
                    transaction_type="review_reward",
                    submission_id=submission.id,
                    reference=f"review:{review.id}",
                )
        except Exception as e:
            logger.error(f"Errore creazione reward reviewer immediato: {e}")

        # Aggiorna sempre la media dopo ogni review
        ExerciseReview.calculate_average_score(submission)

        reviews = ExerciseReview.objects.filter(submission=submission)
        if all(r.score is not None for r in reviews) and not submission.reviewed:
            # Mark as reviewed FIRST to prevent double processing
            submission.reviewed = True
            submission.save(update_fields=["reviewed"])

            logger.info(f"🔄 Starting reward processing for submission {submission.id}")

            # Use atomic transaction to ensure all rewards are created
            try:
                with transaction.atomic():
                    logger.info(
                        f"📊 Calculating average score for submission {submission.id}"
                    )
                    # Calcola media e numero di review completate
                    scores = [r.score for r in reviews if r.score is not None]
                    completed_count = len(scores)
                    average = (
                        (sum(scores) / completed_count) if completed_count > 0 else None
                    )

                    # Regola: studente premiato solo se almeno 3 review e media >= 6
                    passed = (
                        average is not None and completed_count >= 3 and average >= 6
                    )

                    logger.info(
                        f"📈 Submission {submission.id}: completed={completed_count}, average={average}, passed={passed}"
                    )

                    # Update submission status
                    submission.passed = passed

                    reward_transactions_created = []

                    # Premio fisso 2 TEO allo studente SE passato (idempotente)
                    if passed:
                        from blockchain.models import DBTeoCoinTransaction

                        existing_student_reward = (
                            DBTeoCoinTransaction.objects.filter(
                                user=submission.student, transaction_type="bonus"
                            )
                            .filter(
                                Q(description__contains="[exercise_reward]")
                                & Q(description__contains=f"submission {submission.id}")
                            )
                            .exists()
                        )

                        if not existing_student_reward:
                            student_reward_amount = 2
                            submission.reward_amount = student_reward_amount
                            exercise_reward = create_reward_transaction(
                                submission.student,
                                student_reward_amount,
                                "exercise_reward",
                                submission.id,
                            )
                            reward_transactions_created.append(exercise_reward)
                            if exercise_reward:
                                logger.info(
                                    f"✅ Exercise reward transaction created: ID {exercise_reward.id}"
                                )
                            else:
                                logger.error(
                                    f"❌ Failed to create exercise reward transaction"
                                )
                        else:
                            logger.info(
                                "ℹ️ Exercise reward already exists; skipping duplicate grant."
                            )

                    logger.info(f"💾 Saving submission changes for {submission.id}")
                    # Save submission changes
                    submission.save()

                    logger.info(
                        f"📢 Creating notification for student {submission.student.username}"
                    )
                    # Create notification for student
                    Notification.objects.create(
                        user=submission.student,
                        message=(
                            f"Il tuo esercizio '{submission.exercise.title}' è stato valutato con una media di {average:.1f}"
                            if average is not None
                            else "Il tuo esercizio è stato valutato."
                        ),
                        notification_type="exercise_graded",
                        related_object_id=getattr(submission, "id", None),
                    )

                    logger.info(
                        f"✅ Review completed for submission {submission.id}. Created {len(reward_transactions_created)} reward transactions."
                    )

            except Exception as e:
                logger.error(
                    f"❌ Error processing rewards for submission {submission.id}: {e}"
                )
                logger.error(f"❌ Exception type: {type(e).__name__}")
                import traceback

                logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")

                # If reward processing fails, at least mark the review as complete
                # The rewards can be processed later manually
                if not submission.reviewed:
                    submission.reviewed = True
                    submission.save(update_fields=["reviewed"])

                # Return a more specific error message
                return Response(
                    {
                        "error": f"Errore durante il processing dei reward: {str(e)}",
                        "details": "La valutazione è stata salvata ma ci potrebbero essere problemi con i reward. Contatta l'amministratore.",
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        logger.info(
            f"🎉 Successfully returning response for submission {submission.id}"
        )
        return Response(
            {"success": "Esercizio valutato con successo."},
            status=status.HTTP_201_CREATED,
        )


class LessonExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        exercises = lesson.exercises.all()
        data = [
            {"id": e.id, "title": e.title, "description": e.description}
            for e in exercises
        ]
        return Response(data, status=status.HTTP_200_OK)


class MySubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        submission = ExerciseSubmission.objects.filter(
            exercise_id=exercise_id, student=request.user
        ).first()
        if not submission:
            return Response({"detail": "Nessuna submission trovata."}, status=404)
        return Response(ExerciseSubmissionSerializer(submission).data)


class SubmissionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all submissions by the current user, newest first."""
        qs = (
            ExerciseSubmission.objects.filter(student=request.user)
            .select_related("exercise")
            .prefetch_related("reviews")
            .order_by("-created_at")
        )
        return Response(ExerciseSubmissionSerializer(qs, many=True).data)


class ReviewHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the review history for the current user (as reviewer)."""
        reviews = (
            ExerciseReview.objects.filter(reviewer=request.user)
            .select_related("submission__exercise", "submission__student")
            .order_by("-assigned_at")
        )
        data = [
            {
                "pk": r.pk,
                "submission_id": (
                    r.submission.pk if getattr(r, "submission", None) else None
                ),
                "exercise_title": (
                    r.submission.exercise.title
                    if getattr(r, "submission", None)
                    and getattr(r.submission, "exercise", None)
                    else None
                ),
                "student_username": (
                    r.submission.student.username
                    if getattr(r, "submission", None)
                    and getattr(r.submission, "student", None)
                    else None
                ),
                "score": r.score,
                "assigned_at": r.assigned_at,
                "reviewed_at": r.reviewed_at,
            }
            for r in reviews
        ]
        return Response(data)


class AssignedReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reviews = ExerciseReview.objects.filter(
            reviewer=request.user, score__isnull=True
        )
        data = []
        for r in reviews:
            sub = getattr(r, "submission", None)
            exercise = getattr(sub, "exercise", None) if sub else None
            course_id = None
            lesson_id = None
            if exercise and getattr(exercise, "lesson", None) and getattr(exercise.lesson, "course", None):
                course_id = exercise.lesson.course.id
                lesson_id = exercise.lesson.id
            student_obj = None
            if sub and getattr(sub, "student", None):
                student_obj = {"id": sub.student.id, "name": getattr(sub.student, "username", None)}
            status = None
            if sub:
                status = "reviewed" if getattr(sub, "reviewed", False) else "pending"
            data.append(
                {
                    "pk": r.pk,
                    "submission_id": sub.pk if sub else None,
                    "submission_pk": sub.pk if sub else None,
                    "exercise_id": getattr(sub, "exercise_id", None) if sub else None,
                    "exercise_title": exercise.title if exercise else None,
                    "assigned_at": r.assigned_at,
                    "student": student_obj,
                    "course_id": course_id,
                    "lesson_id": lesson_id,
                    "submitted_at": getattr(sub, "created_at", None) if sub else None,
                    "status": status,
                }
            )
        return Response(data)


class ExerciseSubmissionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        # Solo admin o docente del corso (gestione lesson/course null safe)
        teacher = None
        if exercise.lesson and exercise.lesson.course:
            teacher = exercise.lesson.course.teacher
        if not (request.user.is_staff or (teacher and teacher == request.user)):
            return Response({"detail": "Non autorizzato."}, status=403)
        submissions = ExerciseSubmission.objects.filter(exercise=exercise)
        data = ExerciseSubmissionSerializer(submissions, many=True).data
        return Response(data)


class ExerciseDebugReviewersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, pk=exercise_id)
        submissions = ExerciseSubmission.objects.filter(exercise=exercise)
        result = []
        for sub in submissions:
            reviewers = []
            for review in ExerciseReview.objects.filter(submission=sub):
                user = review.reviewer
                # Genera un access token JWT per il reviewer
                refresh = RefreshToken.for_user(user)
                reviewers.append(
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "review_id": review.pk,
                        "jwt_access": str(refresh.access_token),
                    }
                )
            result.append(
                {
                    "submission_id": sub.pk,
                    "student_id": sub.student.id,
                    "student_username": sub.student.username,
                    "reviewers": reviewers,
                }
            )
        return Response(result)


class ExerciseDetailView(RetrieveAPIView):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries
        return Exercise.objects.select_related(
            "lesson", "lesson__course", "lesson__course__teacher"
        )


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(ExerciseSubmission, id=submission_id)
        # Autorizzazioni minime: studente proprietario, staff, o teacher del corso
        is_owner = (
            submission.student.id == request.user.id if submission.student else False
        )
        is_staff = getattr(request.user, "is_staff", False)
        is_course_teacher = False
        if (
            submission.exercise
            and submission.exercise.lesson
            and submission.exercise.lesson.course
        ):
            is_course_teacher = (
                submission.exercise.lesson.course.teacher_id == request.user.id
            )

        if not (is_owner or is_staff or is_course_teacher):
            return Response({"detail": "Non autorizzato."}, status=403)

        # Build normalized detail contract expected by frontend
        reviews_out = []
        # Only include completed reviews (those with reviewed_at set)
        for r in ExerciseReview.objects.filter(submission=submission, reviewed_at__isnull=False).select_related('reviewer'):
            reviews_out.append({
                'reviewer': {
                    'username': getattr(r.reviewer, 'username', None),
                    'name': getattr(r.reviewer, 'username', None),
                } if getattr(r, 'reviewer', None) else None,
                # numeric breakdown (1–5)
                'technical': getattr(r, 'technical', None),
                'creative': getattr(r, 'creative', None),
                'following': getattr(r, 'following', None),

                # NEW: per-area textual comments (align with serializer contract)
                'technical_comment': getattr(r, 'technical_comment', None),
                'creative_comment': getattr(r, 'creative_comment', None),
                'following_comment': getattr(r, 'following_comment', None),

                # narrative/legacy fields (kept for compatibility)
                'strengths_comment': getattr(r, 'strengths_comment', None),
                'suggestions_comment': getattr(r, 'suggestions_comment', None),
                'final_comment': getattr(r, 'final_comment', None),
                'comment': getattr(r, 'comment', None),
                'created_at': r.reviewed_at,
            })

        return Response({"submission_id": submission.id, "reviews": reviews_out}, status=200)


class MySubmissionsListView(APIView):
    """
    GET: Return the current user's ExerciseSubmissions with aggregated
    feedback counts and per-area averages.

    Contract follows the frontend expectation: items[], count
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Annotate counts and averages to avoid N+1
        qs = (
            ExerciseSubmission.objects.filter(student=request.user)
            .select_related("exercise", "exercise__lesson", "exercise__lesson__course")
            .prefetch_related("reviews", "reviewers")
            .annotate(
                reviewers_count=Count("reviewers", distinct=True),
                total_feedback_received=Count(
                    "reviews",
                    filter=(Q(reviews__score__isnull=False) | Q(reviews__technical__isnull=False) | Q(reviews__creative__isnull=False) | Q(reviews__following__isnull=False)),
                ),
                technical_received=Count("reviews", filter=Q(reviews__technical__isnull=False)),
                creative_received=Count("reviews", filter=Q(reviews__creative__isnull=False)),
                following_received=Count("reviews", filter=Q(reviews__following__isnull=False)),
                technical_avg=Avg("reviews__technical"),
                creative_avg=Avg("reviews__creative"),
                following_avg=Avg("reviews__following"),
                last_reviewed_at=Max("reviews__reviewed_at"),
            )
            .order_by("-created_at")
        )

        items = []
        for s in qs:
            course = None
            if getattr(s, "exercise", None) and getattr(s.exercise, "lesson", None) and getattr(s.exercise.lesson, "course", None):
                c = s.exercise.lesson.course
                course = {"id": c.id, "title": c.title}

            # Map internal model areas to canonical frontend keys
            reviewers_count = getattr(s, "reviewers_count", 0) or 0
            expected_per_area = reviewers_count

            tech_avg = getattr(s, "technical_avg", None)
            creat_avg = getattr(s, "creative_avg", None)
            follow_avg = getattr(s, "following_avg", None)

            area_list = [
                {
                    "key": "technical",
                    "label": "Technique",
                    "received": int(getattr(s, "technical_received", 0) or 0),
                    "expected": expected_per_area,
                    "avg": round(float(tech_avg), 1) if tech_avg is not None else None,
                    "items": [],
                },
                {
                    "key": "creative",
                    "label": "Creative",
                    "received": int(getattr(s, "creative_received", 0) or 0),
                    "expected": expected_per_area,
                    "avg": round(float(creat_avg), 1) if creat_avg is not None else None,
                    "items": [],
                },
                {
                    "key": "following",
                    "label": "Following",
                    "received": int(getattr(s, "following_received", 0) or 0),
                    "expected": expected_per_area,
                    "avg": round(float(follow_avg), 1) if follow_avg is not None else None,
                    "items": [],
                },
            ]

            # Compute overall_avg as mean of available area averages (1-5 scale)
            avgs = [a["avg"] for a in [
                {"avg": round(float(tech_avg), 1) if tech_avg is not None else None},
                {"avg": round(float(follow_avg), 1) if follow_avg is not None else None},
                {"avg": round(float(creat_avg), 1) if creat_avg is not None else None},
            ] if a["avg"] is not None]
            overall_avg = round(sum(avgs) / len(avgs), 1) if avgs else None

            updated_at = getattr(s, "last_reviewed_at", None) or getattr(s, "submitted_at", None) or getattr(s, "created_at", None)

            status = "submitted"
            if getattr(s, "reviewed", False):
                status = "completed"
            elif reviewers_count > 0:
                status = "under_review"

            items.append(
                {
                    "submission_id": s.id,
                    "exercise": {"id": s.exercise.id if s.exercise else None, "title": s.exercise.title if s.exercise else None},
                    "course": course,
                    "status": status,
                    "created_at": s.created_at,
                    "updated_at": updated_at,
                    "feedback": {"received": int(getattr(s, "total_feedback_received", 0) or 0), "expected": expected_per_area},
                    "areas": area_list,
                    "overall_avg": overall_avg,
                }
            )

            # Backfill per-area reviewer items (up to 3) with numeric scores 0-5
            try:
                reviews_qs = s.reviews.filter(reviewed_at__isnull=False).order_by('reviewed_at')
                for a in area_list:
                    key = a['key']
                    preview_items = []
                    for r in reviews_qs:
                        if not getattr(r, 'reviewer', None):
                            continue
                        # Build reviewer info
                        try:
                            name = (
                                r.reviewer.get_full_name()
                                if callable(getattr(r.reviewer, 'get_full_name', None))
                                else getattr(r.reviewer, 'first_name', None)
                            )
                        except Exception:
                            name = getattr(r.reviewer, 'username', None)
                        reviewer = {"username": getattr(r.reviewer, 'username', None), "name": name or getattr(r.reviewer, 'username', None)}

                        # pick the numeric score for the canonical key
                        score_field = None
                        if key == 'technical':
                            score_field = getattr(r, 'technical', None) if hasattr(r, 'technical') else getattr(r, 'technique', None)
                        elif key == 'creative':
                            score_field = getattr(r, 'creative', None)
                        elif key == 'following':
                            score_field = getattr(r, 'following', None)

                        try:
                            score_val = int(score_field) if score_field is not None else 0
                        except Exception:
                            score_val = 0

                        preview_items.append({"reviewer": reviewer, "score": score_val, "review_id": getattr(r, 'id', None), "created_at": getattr(r, 'reviewed_at', None)})

                    # limit to first 3 reviewers
                    a['items'] = preview_items[:3]
            except Exception:
                pass

        return Response({"items": items, "count": qs.count()}, status=200)
