import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from users.models import User
from courses.models import Course


@pytest.mark.django_db
def test_pending_list_excludes_unapproved_teacher():
    admin = User.objects.create(username="admin", is_staff=True, is_superuser=True)
    teacher1 = User.objects.create(username="t1", role="teacher", is_approved=True)
    teacher2 = User.objects.create(username="t2", role="teacher", is_approved=False)

    c1 = Course.objects.create(title="ApprovedTeacherCourse", description="x", teacher=teacher1)
    c2 = Course.objects.create(title="UnapprovedTeacherCourse", description="x", teacher=teacher2)

    client = APIClient()
    client.force_authenticate(admin)

    url = reverse("pending-courses")
    res = client.get(url)
    assert res.status_code == 200
    titles = [c["title"] for c in res.data]
    assert "ApprovedTeacherCourse" in titles
    assert "UnapprovedTeacherCourse" not in titles


@pytest.mark.django_db
def test_approve_returns_412_if_teacher_not_approved():
    admin = User.objects.create(username="admin2", is_staff=True, is_superuser=True)
    teacher = User.objects.create(username="t3", role="teacher", is_approved=False)
    course = Course.objects.create(title="PendingCourse", description="x", teacher=teacher)

    client = APIClient()
    client.force_authenticate(admin)

    url = reverse("approve-course", kwargs={"course_id": course.pk})
    res = client.post(url)
    assert res.status_code == 412
    assert res.data.get("code") == "TEACHER_NOT_APPROVED"


@pytest.mark.django_db
def test_approve_success_and_conflict():
    admin = User.objects.create(username="admin3", is_staff=True, is_superuser=True)
    teacher = User.objects.create(username="t4", role="teacher", is_approved=True)
    course = Course.objects.create(title="PendingCourse2", description="x", teacher=teacher)

    client = APIClient()
    client.force_authenticate(admin)

    url = reverse("approve-course", kwargs={"course_id": course.pk})
    res = client.post(url)
    assert res.status_code == 200
    assert res.data.get("success") is True
    # assert audit fields set
    course.refresh_from_db()
    assert course.approved_at is not None
    assert course.approved_by == admin

    # second attempt -> 409
    res2 = client.post(url)
    assert res2.status_code == 409
