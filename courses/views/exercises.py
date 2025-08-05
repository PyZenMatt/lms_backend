from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db import models
from courses.models import Exercise, Lesson, Course, ExerciseSubmission, ExerciseReview
from courses.serializers import ExerciseSerializer, ExerciseSubmissionSerializer
from users.permissions import IsTeacher
from django.utils import timezone
from datetime import timedelta
import random
from users.models import User
from notifications.models import Notification
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.generics import RetrieveAPIView
import logging

logger = logging.getLogger(__name__)


def create_reward_transaction(user, amount, transaction_type, submission_id):
    """
    Create a reward transaction for a user using DB-based TeoCoin service
    """
    from services.db_teocoin_service import db_teocoin_service
    
    # Convert amount to Decimal for DB service
    from decimal import Decimal
    amount_decimal = Decimal(str(amount))
    
    # Create description based on transaction type
    if transaction_type == 'exercise_reward':
        description = f"Exercise completion reward (submission {submission_id})"
    elif transaction_type == 'review_reward':
        description = f"Exercise review reward (submission {submission_id})"
    else:
        description = f"{transaction_type.replace('_', ' ').title()} for submission {submission_id}"
    
    # Use DB service to add balance and create transaction
    success = db_teocoin_service.add_balance(
        user=user,
        amount=amount_decimal,
        transaction_type=transaction_type,
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
        logger.error(f"Failed to create reward transaction for {user.email}: {amount} {transaction_type}")
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
            raise PermissionDenied("Non puoi aggiungere esercizi a un corso non approvato.")
        lesson = get_object_or_404(Lesson, id=lesson_id, course=course)

        data = request.data.copy()
        data['lesson'] = lesson.id

        serializer = ExerciseSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            exercise = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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

        eligible_reviewers = User.objects.filter(role__in=['student', 'teacher']).exclude(id=request.user.id)
        reviewers = random.sample(list(eligible_reviewers), min(3, eligible_reviewers.count()))

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
                related_object_id=submission.id
            )

        submission.save()

        return Response({"success": "Esercizio inviato con successo."}, status=status.HTTP_201_CREATED)


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

        review = get_object_or_404(ExerciseReview, submission=submission, reviewer=request.user)
        if review.score is not None:
            return Response({"error": "Hai già valutato questo esercizio."}, status=status.HTTP_400_BAD_REQUEST)

        review.score = int(score)
        review.reviewed_at = timezone.now()
        review.save()

        # Aggiorna sempre la media dopo ogni review
        ExerciseReview.calculate_average_score(submission)

        reviews = ExerciseReview.objects.filter(submission=submission)
        if all(r.score is not None for r in reviews) and not submission.reviewed:
            # Mark as reviewed FIRST to prevent double processing
            submission.reviewed = True
            submission.save(update_fields=['reviewed'])
            
            logger.info(f"🔄 Starting reward processing for submission {submission.id}")
            
            # Use atomic transaction to ensure all rewards are created
            try:
                with transaction.atomic():
                    logger.info(f"📊 Calculating average score for submission {submission.id}")
                    # Calcola la media solo sulle review con score non None
                    scores = [r.score for r in reviews if r.score is not None]
                    if scores:
                        average = sum(scores) / len(scores)
                    else:
                        average = None
                    passed = average is not None and average >= 6
                    
                    logger.info(f"📈 Submission {submission.id}: average={average}, passed={passed}")
                    
                    # Get course - handle both lesson.course and direct course relationship
                    course = None
                    try:
                        if hasattr(submission.exercise, 'lesson') and submission.exercise.lesson:
                            course = submission.exercise.lesson.course
                        elif hasattr(submission.exercise, 'course') and submission.exercise.course:
                            course = submission.exercise.course
                    except AttributeError:
                        course = None
                    
                    logger.info(f"🎓 Course found: {course.title if course else 'None'}")
                    
                    # Update submission status
                    submission.passed = passed
                    
                    # Process rewards if course found
                    reward_transactions_created = []
                    if course and hasattr(course, 'price'):
                        logger.info(f"💰 Processing rewards for course {course.title} (price: {course.price})")
                        
                        # Exercise reward for student (if passed)
                        if passed:
                            # Reward max is PER STUDENT, not per course
                            reward_max_per_student = int(course.price * 0.15)
                            
                            # Check how much this student has already received for this course using DB service
                            from blockchain.models import DBTeoCoinTransaction
                            
                            # Get all exercise submissions for this student in this course
                            course_submission_ids = ExerciseSubmission.objects.filter(
                                exercise__lesson__course=course,
                                student=submission.student
                            ).values_list('id', flat=True)
                            
                            # Sum up exercise rewards for those submissions
                            student_rewards_for_course = 0
                            for sub_id in course_submission_ids:
                                reward_amount = DBTeoCoinTransaction.objects.filter(
                                    user=submission.student,
                                    transaction_type='exercise_reward',
                                    description__contains=f'submission {sub_id}'
                                ).aggregate(total=models.Sum('amount'))['total'] or 0
                                student_rewards_for_course += reward_amount
                            
                            remaining_for_student = reward_max_per_student - student_rewards_for_course

                            logger.info(f"🎯 Exercise reward check: max_per_student={reward_max_per_student}, student_received={student_rewards_for_course}, remaining_for_student={remaining_for_student}")

                            if remaining_for_student > 0:
                                reward_cap = max(1, int(course.price * 0.05))  # Ensure minimum 1
                                random_reward = min(random.randint(1, reward_cap), remaining_for_student)

                                logger.info(f"🎁 Creating exercise reward: {random_reward} TEO for {submission.student.username}")
                                
                                submission.reward_amount = random_reward
                                
                                # Create exercise reward transaction
                                exercise_reward = create_reward_transaction(
                                    submission.student, 
                                    random_reward, 
                                    'exercise_reward', 
                                    submission.id
                                )
                                reward_transactions_created.append(exercise_reward)
                                
                                if exercise_reward:
                                    logger.info(f"✅ Exercise reward transaction created: ID {exercise_reward.id}")
                                else:
                                    logger.error(f"❌ Failed to create exercise reward transaction")

                                # Note: We no longer track global course.reward_distributed
                                # Each student can earn up to their individual limit
                                logger.info(f"📊 Student reward: {random_reward} TEO (remaining: {remaining_for_student - random_reward})")
                            else:
                                logger.warning(f"⚠️ Student {submission.student.username} has already received maximum rewards for this course")

                        # Review rewards for all reviewers
                        reviewer_reward = max(1, int(course.price * 0.005))
                        logger.info(f"👥 Creating review rewards: {reviewer_reward} TEO each for {len(reviews)} reviewers")
                        
                        for i, r in enumerate(reviews):
                            logger.info(f"🔍 Creating review reward {i+1}/{len(reviews)} for {r.reviewer.username}")
                            review_reward = create_reward_transaction(
                                r.reviewer,
                                reviewer_reward,
                                'review_reward',
                                submission.id
                            )
                            reward_transactions_created.append(review_reward)
                            
                            if review_reward:
                                logger.info(f"✅ Review reward transaction created: ID {review_reward.id}")
                            else:
                                logger.error(f"❌ Failed to create review reward transaction for {r.reviewer.username}")
                    
                    logger.info(f"💾 Saving submission changes for {submission.id}")
                    # Save submission changes
                    submission.save()

                    logger.info(f"📢 Creating notification for student {submission.student.username}")
                    # Create notification for student
                    Notification.objects.create(
                        user=submission.student,
                        message=f"Il tuo esercizio '{submission.exercise.title}' è stato valutato con una media di {average:.1f}" if average is not None else "Il tuo esercizio è stato valutato.",
                        notification_type='exercise_graded',
                        related_object_id=getattr(submission, 'id', None)
                    )
                    
                    logger.info(f"✅ Review completed for submission {submission.id}. Created {len(reward_transactions_created)} reward transactions.")
                    
            except Exception as e:
                logger.error(f"❌ Error processing rewards for submission {submission.id}: {e}")
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

        logger.info(f"🎉 Successfully returning response for submission {submission.id}")        
        return Response({"success": "Esercizio valutato con successo."}, status=status.HTTP_201_CREATED)


class LessonExercisesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, lesson_id):
        lesson = get_object_or_404(Lesson, id=lesson_id)
        exercises = lesson.exercises.all()
        data = [{"id": e.id, "title": e.title, "description": e.description} for e in exercises]
        return Response(data, status=status.HTTP_200_OK)


class MySubmissionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, exercise_id):
        submission = ExerciseSubmission.objects.filter(exercise_id=exercise_id, student=request.user).first()
        if not submission:
            return Response({'detail': 'Nessuna submission trovata.'}, status=404)
        return Response(ExerciseSubmissionSerializer(submission).data)

class AssignedReviewsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        reviews = ExerciseReview.objects.filter(reviewer=request.user, score__isnull=True)
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

class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, submission_id):
        submission = get_object_or_404(ExerciseSubmission, pk=submission_id)
        if submission.student != request.user and not submission.reviewers.filter(pk=request.user.pk).exists():
            return Response({'detail': 'Non autorizzato.'}, status=403)
        return Response(ExerciseSubmissionSerializer(submission).data)

class SubmissionHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        submissions = ExerciseSubmission.objects.filter(student=request.user)
        data = ExerciseSubmissionSerializer(submissions, many=True).data
        return Response(data)

class ReviewHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        reviews = ExerciseReview.objects.filter(reviewer=request.user, score__isnull=False)
        data = [
            {
                'pk': r.pk,
                'submission_pk': r.submission.pk,
                'exercise_title': r.submission.exercise.title,
                'score': r.score,
                'reviewed_at': r.reviewed_at,
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
