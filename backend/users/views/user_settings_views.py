"""
User settings and progress management views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import UserSettings, UserProgress
from users.serializers import UserSettingsSerializer, UserProgressSerializer


class UserSettingsView(APIView):
    """User settings management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)
    
    def put(self, request):
        """Update user settings"""
        settings, created = UserSettings.objects.get_or_create(user=request.user)
        
        # Handle nested privacy data
        privacy_data = request.data.pop('privacy', {})
        
        serializer = UserSettingsSerializer(
            settings, 
            data=request.data, 
            partial=True,
            context={'privacy': privacy_data}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class UserProgressView(APIView):
    """User progress tracking"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user progress with updated statistics"""
        progress, created = UserProgress.objects.get_or_create(user=request.user)
        
        # Update progress data before returning
        self.update_progress_data(request.user, progress)
        
        serializer = UserProgressSerializer(progress)
        return Response(serializer.data)
    
    def update_progress_data(self, user, progress):
        """Update user progress with current data"""
        from courses.models import CourseEnrollment, LessonCompletion
        from django.db.models import Avg
        from django.utils import timezone
        
        # Update course statistics
        enrollments = CourseEnrollment.objects.filter(student=user)
        progress.total_courses_enrolled = enrollments.count()
        progress.total_courses_completed = enrollments.filter(completed=True).count()
        
        # Update lesson statistics
        lesson_completions = LessonCompletion.objects.filter(student=user)
        progress.total_lessons_completed = lesson_completions.count()
        
        # Calculate average score (if score field exists)
        if lesson_completions.exists():
            avg_score = lesson_completions.aggregate(
                avg=Avg('score')
            )['avg'] if hasattr(LessonCompletion, 'score') else 0
            progress.average_score = avg_score or 0
        
        # Update last activity
        last_completion = lesson_completions.order_by('-completed_at').first()
        if last_completion:
            progress.last_activity_date = last_completion.completed_at
        
        progress.save()
