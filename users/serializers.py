from rest_framework import serializers
from .models import User, UserSettings, UserProgress, Achievement, UserAchievement
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q, Count, Avg


class UserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, read_only=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'address', 'role', 'avatar', 'bio', 'profession', 'artistic_aspirations', 'wallet_address']


class UserProfileSerializer(serializers.ModelSerializer):
    role = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(required=False, allow_null=True)
    date_joined = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'address', 'role', 'avatar', 'bio', 'profession', 'artistic_aspirations', 'date_joined', 'wallet_address']


class UserSettingsSerializer(serializers.ModelSerializer):
    privacy = serializers.SerializerMethodField()
    
    class Meta:
        model = UserSettings
        fields = [
            'email_notifications', 'push_notifications', 'course_reminders',
            'weekly_digest', 'marketing_emails', 'theme', 'language', 'timezone',
            'privacy'
        ]
    
    def get_privacy(self, obj):
        return {
            'show_profile': obj.show_profile,
            'show_progress': obj.show_progress,
            'show_achievements': obj.show_achievements
        }
    
    def update(self, instance, validated_data):
        privacy_data = self.context.get('privacy', {})
        if privacy_data:
            instance.show_profile = privacy_data.get('show_profile', instance.show_profile)
            instance.show_progress = privacy_data.get('show_progress', instance.show_progress)
            instance.show_achievements = privacy_data.get('show_achievements', instance.show_achievements)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'icon', 'color', 'achievement_type']


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    earned = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAchievement
        fields = ['achievement', 'earned_date', 'progress_percentage', 'earned']
    
    def get_earned(self, obj):
        return obj.progress_percentage >= 100


class UserProgressSerializer(serializers.ModelSerializer):
    overall_progress = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()
    recent_activities = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProgress
        fields = [
            'total_courses_enrolled', 'total_courses_completed', 'total_lessons_completed',
            'total_exercises_completed', 'total_hours_studied', 'average_score',
            'streak_days', 'last_activity_date', 'overall_progress', 'categories',
            'achievements', 'recent_activities'
        ]
    
    def get_overall_progress(self, obj):
        return obj.calculate_overall_progress()
    
    def get_categories(self, obj):
        from courses.models import Course, CourseEnrollment
        
        # ✅ OTTIMIZZATO - Single query con annotations invece di N queries
        category_choices = Course.CATEGORY_CHOICES if hasattr(Course, 'CATEGORY_CHOICES') else []
        
        # Single query con annotations invece di N queries
        enrollments_by_category = CourseEnrollment.objects.filter(
            student=obj.user
        ).select_related('course').values(
            'course__category'
        ).annotate(
            total_courses=Count('pk'),
            completed_courses=Count('pk', filter=Q(completed=True))
        )
        
        # Convert to dict for O(1) lookup
        category_data = {item['course__category']: item for item in enrollments_by_category}
        
        categories = []
        for category_code, category_name in category_choices:
            data = category_data.get(category_code, {'total_courses': 0, 'completed_courses': 0})
            total_courses = data['total_courses']
            completed_courses = data['completed_courses']
            progress_percentage = (completed_courses / total_courses * 100) if total_courses > 0 else 0
            
            categories.append({
                'slug': category_code,
                'name': category_name,
                'total_courses': total_courses,
                'completed_courses': completed_courses,
                'progress_percentage': round(progress_percentage, 2)
            })
        
        return categories
    
    def get_achievements(self, obj):
        user_achievements = UserAchievement.objects.filter(user=obj.user).select_related('achievement')
        return UserAchievementSerializer(user_achievements, many=True).data
    
    def get_recent_activities(self, obj):
        from courses.models import LessonCompletion, CourseEnrollment
        from django.utils import timezone
        from datetime import timedelta
        
        # Get recent activities from the last 30 days
        recent_date = timezone.now() - timedelta(days=30)
        activities = []
        
        # Recent lesson completions - ✅ OPTIMIZED
        lesson_completions = LessonCompletion.objects.filter(
            student=obj.user,
            completed_at__gte=recent_date
        ).select_related('lesson')[:10]
        
        for completion in lesson_completions:
            activities.append({
                'id': f'lesson_{completion.pk}',
                'type': 'lesson_completed',
                'title': completion.lesson.title,
                'date': completion.completed_at,
                'score': None  # LessonCompletion doesn't have score field
            })
        
        # Recent course completions - ✅ OPTIMIZED with correct field name
        course_completions = CourseEnrollment.objects.filter(
            student=obj.user,
            completed=True,
            enrolled_at__gte=recent_date  # Fixed field name: enrolled_at instead of enrollment_date
        ).select_related('course')[:5]
        
        for enrollment in course_completions:
            activities.append({
                'id': f'course_{enrollment.pk}',
                'type': 'course_completed',
                'title': enrollment.course.title,
                'date': enrollment.enrolled_at,  # Fixed field name
                'score': None
            })
        
        # Sort by date
        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[:15]

