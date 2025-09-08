from courses.models import Course
from courses.serializers import CourseSerializer
from django.shortcuts import get_object_or_404
from notifications.models import Notification
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView


class PendingCoursesView(ListAPIView):
    """List courses pending approval but only for teachers who are themselves approved.

    This enforces the business rule server-side: admin sees only pending courses
    coming from approved teachers.
    """
    serializer_class = CourseSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        qs = Course.objects.filter(is_approved=False, teacher__is_approved=True)
        # Optional q filter on title/slug
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        return qs


class ApproveCourseView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, course_id):
        """Approve a course only if its teacher is approved and the course is pending.

        Responses:
        - 200: course approved
        - 409: conflict (course already approved)
        - 412: precondition failed (teacher not approved)
        """
        course = get_object_or_404(Course, id=course_id)

        # If course already approved -> 409
        if course.is_approved:
            return Response(
                {"error": "Course already approved", "code": "ALREADY_APPROVED"},
                status=409,
            )

        # If teacher not approved -> 412
        if not getattr(course.teacher, "is_approved", False):
            return Response(
                {
                    "error": "Teacher not approved",
                    "code": "TEACHER_NOT_APPROVED",
                },
                status=412,
            )

        # Approve and set audit fields if available
        from django.utils import timezone

        course.is_approved = True
        if hasattr(course, "approved_at"):
            course.approved_at = timezone.now()
        if hasattr(course, "approved_by"):
            course.approved_by = request.user
        course.save()

        Notification.objects.create(
            user=course.teacher,
            message=f"Il tuo corso '{course.title}' è stato approvato!",
            notification_type="course_approved",
            related_object_id=course.pk,
        )
        return Response({"success": True, "course_id": course.pk})


class RejectCourseView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        Notification.objects.create(
            user=course.teacher,
            message=f"Il tuo corso '{course.title}' è stato rifiutato.",
            notification_type="course_rejected",
            related_object_id=course.pk,
        )
        course.delete()
        return Response(
            {"success": f"Il corso '{course.title}' è stato rifiutato e cancellato."}
        )
