from django.test import TestCase, Client
from django.urls import reverse

from users.models import User
from courses.models import Course


class PendingCoursesTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pending_list_excludes_unapproved_teacher(self):
        admin = User.objects.create(username="admin", is_staff=True, is_superuser=True)
        teacher1 = User.objects.create(username="t1", role="teacher", is_approved=True)
        teacher2 = User.objects.create(username="t2", role="teacher", is_approved=False)

        Course.objects.create(title="ApprovedTeacherCourse", description="x", teacher=teacher1)
        Course.objects.create(title="UnapprovedTeacherCourse", description="x", teacher=teacher2)

        self.client.force_login(admin)
        url = reverse("pending-courses")
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        titles = [c.get("title") for c in data]
        self.assertIn("ApprovedTeacherCourse", titles)
        self.assertNotIn("UnapprovedTeacherCourse", titles)

    def test_approve_returns_412_if_teacher_not_approved(self):
        admin = User.objects.create(username="admin2", is_staff=True, is_superuser=True)
        teacher = User.objects.create(username="t3", role="teacher", is_approved=False)
        course = Course.objects.create(title="PendingCourse", description="x", teacher=teacher)

        self.client.force_login(admin)
        url = reverse("approve-course", kwargs={"course_id": course.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 412)
        self.assertEqual(res.json().get("code"), "TEACHER_NOT_APPROVED")

    def test_approve_success_and_conflict(self):
        admin = User.objects.create(username="admin3", is_staff=True, is_superuser=True)
        teacher = User.objects.create(username="t4", role="teacher", is_approved=True)
        course = Course.objects.create(title="PendingCourse2", description="x", teacher=teacher)

        self.client.force_login(admin)
        url = reverse("approve-course", kwargs={"course_id": course.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json().get("success"))

        course.refresh_from_db()
        self.assertIsNotNone(course.approved_at)
        self.assertEqual(course.approved_by, admin)

        res2 = self.client.post(url)
        self.assertEqual(res2.status_code, 409)
