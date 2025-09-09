import pytest
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_submission_detail_includes_area_comment_fields(django_user_model):
    # Create users
    student = django_user_model.objects.create_user(
        username="stud", email="stud@example.com", password="x", role="student"
    )
    teacher = django_user_model.objects.create_user(
        username="teach", email="teach@example.com", password="x", role="teacher"
    )
    reviewer = django_user_model.objects.create_user(
        username="rev1", email="rev1@example.com", password="x", role="student"
    )

    # Create course/lesson/exercise
    from courses.models import Course, Lesson, Exercise, ExerciseSubmission, ExerciseReview

    course = Course.objects.create(
        title="C1",
        description="d",
        teacher=teacher,
        price_eur=10,
        is_approved=True,
    )
    lesson = Lesson.objects.create(
        title="L1",
        content="c",
        teacher=teacher,
        course=course,
        duration=10,
        order=1,
    )
    exercise = Exercise.objects.create(
        lesson=lesson,
        title="E1",
        description="d",
        exercise_type="practical",
        difficulty="beginner",
    )

    submission = ExerciseSubmission.objects.create(
        exercise=exercise, student=student, content="my work"
    )

    # Attach reviewer and complete a review with per-area comments
    submission.reviewers.add(reviewer)
    review = ExerciseReview.objects.create(
        submission=submission,
        reviewer=reviewer,
        technical=4,
        creative=5,
        following=3,
        comment="Overall nice work. Technical notes below.",
        technical_comment="Good brush control",
        creative_comment=None,
        following_comment="Composition feels balanced",
        reviewed_at=timezone.now(),
        score=8,
    )
    assert review.pk is not None

    client = APIClient()
    client.force_authenticate(user=student)

    # 1) Main detail endpoint
    url = f"/api/v1/submissions/{submission.id}/"
    res = client.get(url)
    assert res.status_code == 200, res.content
    payload = res.json()
    assert payload.get("submission_id") == submission.id
    reviews = payload.get("reviews") or []
    assert len(reviews) == 1
    r0 = reviews[0]
    # Ensure the *_comment fields are present and carry values
    assert "technical_comment" in r0
    assert "creative_comment" in r0
    assert "following_comment" in r0
    assert r0["technical_comment"] == "Good brush control"
    assert r0["creative_comment"] is None
    assert r0["following_comment"] == "Composition feels balanced"

    # 2) Reviewer detail endpoint (serializer-based) should also include fields
    url2 = f"/api/v1/submissions/{submission.id}/review-detail/"
    res2 = client.get(url2)
    assert res2.status_code == 200, res2.content
    payload2 = res2.json()
    # serializer returns full submission object; reviews under 'reviews'
    assert isinstance(payload2.get("reviews"), list)
    r02 = payload2["reviews"][0]
    assert r02.get("technical_comment") == "Good brush control"
    assert r02.get("creative_comment") is None
    assert r02.get("following_comment") == "Composition feels balanced"
