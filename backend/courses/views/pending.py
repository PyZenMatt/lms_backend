from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from courses.models import Course
from courses.serializers import CourseSerializer
from django.shortcuts import get_object_or_404
from notifications.models import Notification

class PendingCoursesView(ListAPIView):
    queryset = Course.objects.filter(is_approved=False)
    serializer_class = CourseSerializer
    permission_classes = [IsAdminUser]

class ApproveCourseView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        course.is_approved = True
        course.save()
        Notification.objects.create(
            user=course.teacher,
            message=f"Il tuo corso '{course.title}' è stato approvato!",
            notification_type='course_approved',
            related_object_id=course.pk
        )
        return Response({'success': f"Il corso '{course.title}' è stato approvato."})

class RejectCourseView(APIView):
    permission_classes = [IsAdminUser]
    def post(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        Notification.objects.create(
            user=course.teacher,
            message=f"Il tuo corso '{course.title}' è stato rifiutato.",
            notification_type='course_rejected',
            related_object_id=course.pk
        )
        course.delete()
        return Response({'success': f"Il corso '{course.title}' è stato rifiutato e cancellato."})
