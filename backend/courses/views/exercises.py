import logging
import random

from courses.models import (Course, Exercise, ExerciseReview,
                            ExerciseSubmission, Lesson)
from courses.serializers import (ExerciseSerializer,
                                 ExerciseSubmissionSerializer)
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
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

logger = logging.getLogger(__name__)


def create_reward_transaction(user, amount, transaction_type, submission_id, reference: str | None = None):
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
    pretty = transaction_type.replace('_', ' ').title()
    suffix = f" | ref={reference}" if reference else ""
    description = f"[{transaction_type}] {pretty} (submission {submission_id}){suffix}"
    mapped_type = 'bonus'

    # Use DB service to add balance and create transaction with mapped type
    success = db_teocoin_service.add_balance(
        user=user,
        amount=amount_decimal,
        transaction_type=mapped_type,
        description=description
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
            f"Failed to create reward transaction for {user.email}: {amount} {transaction_type}")
        return None


class ExerciseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries
        return Exercise.objects.select_related('lesson', 'lesson__course', 'lesson__course__teacher').prefetch_related(
            'submissions', 'submissions__student'
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class CreateExerciseView(APIView):
    permission_classes = [IsAuthenticated, IsTeacher]

    def post(self, request):
        course_id = request.data.get('course_id')
        lesson_id = request.data.get('lesson_id')

        if not course_id or not lesson_id:
            return Response({"error": "Gli ID del corso e della lezione sono obbligatori."}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, id=course_id, teacher=request.user)
        if not (request.user.is_staff or request.user.is_superuser) and not course.is_approved:
            raise PermissionDenied(
                "Non puoi aggiungere esercizi a un corso non approvato.")
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

        data = request.data.copy()
        data['lesson'] = lesson.id

        serializer = ExerciseSerializer(
            data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubmissionDetailForReviewerView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(ExerciseSubmission, id=submission_id)
        # Permesso: reviewer assegnato, staff, teacher del corso, o studente owner
        is_owner = submission.student.id == request.user.id if submission.student else False
        is_staff = getattr(request.user, 'is_staff', False)
        is_course_teacher = False
        if submission.exercise and submission.exercise.lesson and submission.exercise.lesson.course:
            is_course_teacher = (
                submission.exercise.lesson.course.teacher_id == request.user.id)
        is_reviewer = submission.reviewers.filter(id=request.user.id).exists()

        if not (is_owner or is_staff or is_course_teacher or is_reviewer):
            return Response({'detail': 'Non autorizzato.'}, status=403)

        return Response(ExerciseSubmissionSerializer(submission).data, status=200)


class SubmitExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, exercise_id):
        exercise = get_object_or_404(Exercise, id=exercise_id)
        course = exercise.lesson.course

        if not course.students.filter(id=request.user.id).exists():
            return Response({"error": "Non hai acquistato il corso associato a questo esercizio."}, status=status.HTTP_403_FORBIDDEN)

        if ExerciseSubmission.objects.filter(exercise=exercise, student=request.user).exists():
            return Response({"error": "Hai già sottomesso questo esercizio."}, status=status.HTTP_400_BAD_REQUEST)

        # Prendi la soluzione dal body della richiesta
        content = request.data.get('content', '')

        submission = ExerciseSubmission.objects.create(
            student=request.user,
            exercise=exercise,
            content=content
        )

        eligible_reviewers = User.objects.filter(
            role__in=['student', 'teacher']).exclude(id=request.user.id)
        reviewers = random.sample(
            list(eligible_reviewers), min(3, eligible_reviewers.count()))

        for reviewer in reviewers:
            ExerciseReview.objects.create(
                submission=submission,
                reviewer=reviewer
            )
            submission.reviewers.add(reviewer)
            Notification.objects.create(
                user=reviewer,
                message=f"Hai un nuovo esercizio da valutare: {exercise.title}",
                notification_type='review_assigned',
                related_object_id=submission.id,
                link=f"/review/{submission.id}"
            )

        submission.save()
        # Ritorna i dati reali della submission creata, così il frontend si sincronizza subito
        return Response(ExerciseSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)


class ReviewExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, submission_id):
        submission = get_object_or_404(ExerciseSubmission, id=submission_id)

        if submission.student == request.user:
            return Response({"error": "Non puoi valutare il tuo stesso esercizio."}, status=status.HTTP_403_FORBIDDEN)

        if not submission.reviewers.filter(id=request.user.id).exists():
            return Response({"error": "Non sei uno dei valutatori assegnati."}, status=status.HTTP_403_FORBIDDEN)

        score = request.data.get('score')
        if not score or not (1 <= int(score) <= 10):
            return Response({"error": "Il punteggio deve essere compreso tra 1 e 10."}, status=status.HTTP_400_BAD_REQUEST)

        review = get_object_or_404(
            ExerciseReview, submission=submission, reviewer=request.user)
        if review.score is not None:
            return Response({"error": "Hai già valutato questo esercizio."}, status=status.HTTP_400_BAD_REQUEST)

        review.score = int(score)
        review.reviewed_at = timezone.now()
        review.save()

        # Premio immediato al reviewer: 2 TEO per ogni review completata (idempotente)
        try:
            from blockchain.models import DBTeoCoinTransaction
            exists = DBTeoCoinTransaction.objects.filter(
                user=request.user,
                transaction_type='bonus'
            ).filter(
                Q(description__contains='[review_reward]') & Q(
                    description__contains=f"ref=review:{review.id}")
            ).exists()
            if not exists:
                _ = create_reward_transaction(
                    user=request.user,
                    amount=2,
                    transaction_type='review_reward',
                    submission_id=submission.id,
                    reference=f"review:{review.id}"
                )
        except Exception as e:
            logger.error(f"Errore creazione reward reviewer immediato: {e}")

        # Aggiorna sempre la media dopo ogni review
        ExerciseReview.calculate_average_score(submission)

        reviews = ExerciseReview.objects.filter(submission=submission)
        if all(r.score is not None for r in reviews) and not submission.reviewed:
            # Mark as reviewed FIRST to prevent double processing
            submission.reviewed = True
            submission.save(update_fields=['reviewed'])

            logger.info(
                f"🔄 Starting reward processing for submission {submission.id}")

            # Use atomic transaction to ensure all rewards are created
            try:
                with transaction.atomic():
                    logger.info(
                        f"📊 Calculating average score for submission {submission.id}")
                    # Calcola media e numero di review completate
                    scores = [r.score for r in reviews if r.score is not None]
                    completed_count = len(scores)
                    average = (
                        sum(scores) / completed_count) if completed_count > 0 else None

                    # Regola: studente premiato solo se almeno 3 review e media >= 6
                    passed = average is not None and completed_count >= 3 and average >= 6

                    logger.info(
                        f"📈 Submission {submission.id}: completed={completed_count}, average={average}, passed={passed}")

                    # Update submission status
                    submission.passed = passed

                    reward_transactions_created = []

                    # Premio fisso 2 TEO allo studente SE passato (idempotente)
                    if passed:
                        from blockchain.models import DBTeoCoinTransaction
                        existing_student_reward = DBTeoCoinTransaction.objects.filter(
                            user=submission.student,
                            transaction_type='bonus'
                        ).filter(
                            Q(description__contains='[exercise_reward]') & Q(
                                description__contains=f"submission {submission.id}")
                        ).exists()

                        if not existing_student_reward:
                            student_reward_amount = 2
                            submission.reward_amount = student_reward_amount
                            exercise_reward = create_reward_transaction(
                                submission.student,
                                student_reward_amount,
                                'exercise_reward',
                                submission.id
                            )
                            reward_transactions_created.append(exercise_reward)
                            if exercise_reward:
                                logger.info(
                                    f"✅ Exercise reward transaction created: ID {exercise_reward.id}")
                            else:
                                logger.error(
                                    f"❌ Failed to create exercise reward transaction")
                        else:
                            logger.info(
                                "ℹ️ Exercise reward already exists; skipping duplicate grant.")

                    logger.info(
                        f"💾 Saving submission changes for {submission.id}")
                    # Save submission changes
                    submission.save()

                    logger.info(
                        f"📢 Creating notification for student {submission.student.username}")
                    # Create notification for student
                    Notification.objects.create(
                        user=submission.student,
                        message=f"Il tuo esercizio '{submission.exercise.title}' è stato valutato con una media di {average:.1f}" if average is not None else "Il tuo esercizio è stato valutato.",
                        notification_type='exercise_graded',
                        related_object_id=getattr(submission, 'id', None)
                    )

                    logger.info(
                        f"✅ Review completed for submission {submission.id}. Created {len(reward_transactions_created)} reward transactions.")

            except Exception as e:
                logger.error(
                    f"❌ Error processing rewards for submission {submission.id}: {e}")
                logger.error(f"❌ Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"❌ Full traceback:\n{traceback.format_exc()}")

                # If reward processing fails, at least mark the review as complete
                # The rewards can be processed later manually
                if not submission.reviewed:
                    submission.reviewed = True
                    submission.save(update_fields=['reviewed'])

                # Return a more specific error message
                return Response({
                    "error": f"Errore durante il processing dei reward: {str(e)}",
                    "details": "La valutazione è stata salvata ma ci potrebbero essere problemi con i reward. Contatta l'amministratore."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info(
            f"🎉 Successfully returning response for submission {submission.id}")
        return Response({"success": "Esercizio valutato con successo."}, status=status.HTTP_201_CREATED)


class LessonExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        exercises = lesson.exercises.all()
        data = [{"id": e.id, "title": e.title, "description": e.description}
                for e in exercises]
        return Response(data, status=status.HTTP_200_OK)


class MySubmissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        submission = ExerciseSubmission.objects.filter(
            exercise_id=exercise_id, student=request.user).first()
        if not submission:
            return Response({'detail': 'Nessuna submission trovata.'}, status=404)
        return Response(ExerciseSubmissionSerializer(submission).data)


class SubmissionHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all submissions by the current user, newest first."""
        qs = (
            ExerciseSubmission.objects
            .filter(student=request.user)
            .select_related('exercise')
            .prefetch_related('reviews')
            .order_by('-created_at')
        )
        return Response(ExerciseSubmissionSerializer(qs, many=True).data)


class ReviewHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the review history for the current user (as reviewer)."""
        reviews = (
            ExerciseReview.objects
            .filter(reviewer=request.user)
            .select_related('submission__exercise', 'submission__student')
            .order_by('-assigned_at')
        )
        data = [
            {
                'pk': r.pk,
                'submission_id': r.submission.pk if getattr(r, 'submission', None) else None,
                'exercise_title': r.submission.exercise.title if getattr(r, 'submission', None) and getattr(r.submission, 'exercise', None) else None,
                'student_username': r.submission.student.username if getattr(r, 'submission', None) and getattr(r.submission, 'student', None) else None,
                'score': r.score,
                'assigned_at': r.assigned_at,
                'reviewed_at': r.reviewed_at,
            }
            for r in reviews
        ]
        return Response(data)


class AssignedReviewsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reviews = ExerciseReview.objects.filter(
            reviewer=request.user, score__isnull=True)
        data = [
            {
                'pk': r.pk,
                'submission_pk': r.submission.pk,
                'exercise_title': r.submission.exercise.title,
                'assigned_at': r.assigned_at,
                'student_username': r.submission.student.username if r.submission.student else None,
            } for r in reviews
        ]
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
            return Response({'detail': 'Non autorizzato.'}, status=403)
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
                reviewers.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'review_id': review.pk,
                    'jwt_access': str(refresh.access_token),
                })
            result.append({
                'submission_id': sub.pk,
                'student_id': sub.student.id,
                'student_username': sub.student.username,
                'reviewers': reviewers
            })
        return Response(result)


class ExerciseDetailView(RetrieveAPIView):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # ✅ OTTIMIZZATO - Prevent N+1 queries
        return Exercise.objects.select_related('lesson', 'lesson__course', 'lesson__course__teacher')


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, submission_id: int):
        submission = get_object_or_404(ExerciseSubmission, id=submission_id)
        # Autorizzazioni minime: studente proprietario, staff, o teacher del corso
        is_owner = submission.student.id == request.user.id if submission.student else False
        is_staff = getattr(request.user, 'is_staff', False)
        is_course_teacher = False
        if submission.exercise and submission.exercise.lesson and submission.exercise.lesson.course:
            is_course_teacher = (
                submission.exercise.lesson.course.teacher_id == request.user.id)

        if not (is_owner or is_staff or is_course_teacher):
            return Response({'detail': 'Non autorizzato.'}, status=403)

        return Response(ExerciseSubmissionSerializer(submission).data, status=200)
