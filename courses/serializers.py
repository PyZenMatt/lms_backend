from rest_framework import serializers
from .models import (
    Lesson, Exercise, Course, CourseEnrollment, ExerciseSubmission,
    TeacherDiscountDecision, TeacherChoicePreference
)
from users.models import User
from users.serializers import UserSerializer

class LessonListSerializer(serializers.ModelSerializer):
    exercises_count = serializers.SerializerMethodField()
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'order', 'duration', 'lesson_type', 'lesson_type_display', 'exercises_count']
    
    def get_exercises_count(self, obj):
        return obj.exercises.count()

class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    average_score = serializers.FloatField(read_only=True)
    is_approved = serializers.BooleanField(read_only=True)
    reviewed = serializers.BooleanField(read_only=True)
    passed = serializers.BooleanField(read_only=True)
    reviews = serializers.SerializerMethodField()
    exercise = serializers.SerializerMethodField()
    reward_amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = ExerciseSubmission
        fields = [
            'id', 'exercise', 'content', 'created_at',
            'average_score', 'is_approved', 'reviewed', 'passed', 'reviews', 'reward_amount'
        ]

    def get_exercise(self, obj):
        if obj.exercise:
            return {
                'id': obj.exercise.id,
                'title': obj.exercise.title,
                'description': obj.exercise.description,
                'difficulty': obj.exercise.difficulty,
                'time_estimate': obj.exercise.time_estimate,
                'materials': obj.exercise.materials,
                'instructions': obj.exercise.instructions,
                'exercise_type': obj.exercise.exercise_type,
            }
        return None

    def get_reviews(self, obj):
        return [
            {
                'reviewer': r.reviewer.username,
                'score': r.score,
                'reviewed_at': r.reviewed_at
            }
            for r in obj.reviews.all()
        ]

    def validate(self, attrs):
        # Verifica che il contenuto non sia vuoto
        if not attrs.get('content'):
            raise serializers.ValidationError({"content": "Il contenuto della sottomissione è obbligatorio."})
        return attrs
    
class TeacherLessonSerializer(serializers.ModelSerializer):
    total_students = serializers.SerializerMethodField()
    total_earnings = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'total_students', 'total_earnings']

    def get_total_students(self, obj):
        return obj.students.count()

    def get_total_earnings(self, obj):
        return obj.price_eur * obj.students.count() * 0.9  # 10% fee to platform

class TeacherCourseSerializer(serializers.ModelSerializer):
    total_earnings = serializers.SerializerMethodField()
    total_students = serializers.SerializerMethodField()
    enrolled_students = serializers.SerializerMethodField()
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price_eur', 'category', 'category_display', 
                  'cover_image', 'cover_image_url', 'is_approved', 'created_at', 'updated_at',
                  'total_earnings', 'total_students', 'enrolled_students', 'lessons']

    def get_total_earnings(self, obj):
        from decimal import Decimal
        return str(obj.price_eur * obj.students.count() * Decimal('0.9'))

    def get_total_students(self, obj):
        return obj.students.count()
        
    def get_enrolled_students(self, obj):
        return obj.students.count()
        
    def get_cover_image_url(self, obj):
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
        return None
    
    def get_lessons(self, obj):
        # Restituisce le lezioni del corso con informazioni di base
        lessons = obj.lessons.all().order_by('order', 'created_at')
        lesson_data = []
        for lesson in lessons:
            lesson_data.append({
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.content[:100] + '...' if lesson.content and len(lesson.content) > 100 else lesson.content,
                'duration': lesson.duration,
                'order': lesson.order,
                'lesson_type': lesson.lesson_type,
                'created_at': lesson.created_at,
                'exercises_count': lesson.exercises.count(),
                'course_id': obj.id,  # Aggiungiamo esplicitamente il course_id
                'course': obj.id      # Per compatibilità
            })
        return lesson_data
    
class LessonSerializer(serializers.ModelSerializer):
    course_id = serializers.IntegerField(source='course.id', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_type_display = serializers.CharField(source='get_lesson_type_display', read_only=True)
    video_file_url = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'lesson_type', 'lesson_type_display', 
                  'video_file', 'video_file_url', 'course', 'duration', 'teacher',
                  'materials', 'order', 'created_at', 'course_id', 'course_title']
        read_only_fields = ['id', 'created_at', 'teacher']
    
    def get_video_file_url(self, obj):
        if obj.video_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video_file.url)
        return None
    
    def validate_course(self, value):
        if value and value.teacher != self.context['request'].user:
            raise serializers.ValidationError("Non sei il teacher di questo corso")
        return value

class ExerciseSerializer(serializers.ModelSerializer):
    exercise_type_display = serializers.CharField(source='get_exercise_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    reference_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Exercise
        fields = [
            'id', 'title', 'description', 'lesson', 'exercise_type', 'exercise_type_display',
            'difficulty', 'difficulty_display', 'time_estimate', 'materials', 'instructions', 
            'reference_image', 'reference_image_url', 'status', 'score', 'feedback', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'score', 'feedback', 'status']
    
    def get_reference_image_url(self, obj):
        if obj.reference_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.reference_image.url)
        return None
        

    def validate_lesson(self, value):
        # Verifica che la lezione appartenga al corso del teacher
        if value.course.teacher != self.context['request'].user:
            raise serializers.ValidationError("Non sei il proprietario del corso associato a questa lezione.")
        return value

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    teacher = UserSerializer(read_only=True)
    total_duration = serializers.SerializerMethodField()
    students = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    is_enrolled = serializers.SerializerMethodField()
    is_approved = serializers.BooleanField(read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    student_count = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    teocoin_price = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'category', 'category_display', 'cover_image', 'cover_image_url',
            'price_eur', 'teocoin_price', 'teocoin_discount_percent', 'teocoin_reward', 'teacher', 'lessons', 'total_duration', 'students', 'student_count',
            'created_at', 'updated_at', 'is_enrolled', 'is_approved'
        ]
        read_only_fields = ['teacher', 'students']
        extra_kwargs = {
            'lessons': {'read_only': True}
        }
    def get_teocoin_price(self, obj):
        return obj.get_teocoin_price() if hasattr(obj, 'get_teocoin_price') else None

    # Removed validate_price since 'price' field is gone

    def get_total_duration(self, obj):
        return sum(lesson.duration for lesson in obj.lessons.all())

    def get_is_enrolled(self, obj):
        user = self.context['request'].user
        return obj.students.filter(pk=user.pk).exists()
    
    def get_student_count(self, obj):
    
        return obj.students.count()

    def get_cover_image_url(self, obj):
       
        if obj.cover_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_image.url)
            return obj.cover_image.url
        return None
    
class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student = serializers.StringRelatedField(read_only=True)
    course = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CourseEnrollment
        fields = [
            'id',
            'student',
            'course',
            'enrolled_at',
            'completed',
        ]
        read_only_fields = ['id', 'student', 'course', 'enrolled_at', 'completed']
    
class StudentCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'price_eur']


class TeacherDiscountDecisionSerializer(serializers.ModelSerializer):
    """
    Serializer for teacher discount decisions
    """
    student_email = serializers.CharField(source='student.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    teo_cost_display = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    teacher_bonus_display = serializers.DecimalField(max_digits=10, decimal_places=4, read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    teacher_earnings_if_accepted = serializers.SerializerMethodField()
    teacher_earnings_if_declined = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    time_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = TeacherDiscountDecision
        fields = [
            'id', 'student_email', 'course_title', 'course_price', 'discount_percentage',
            'teo_cost_display', 'teacher_bonus_display', 'discounted_price',
            'teacher_commission_rate', 'teacher_staking_tier', 'decision',
            'decision_made_at', 'expires_at', 'created_at', 'is_expired',
            'time_remaining', 'teacher_earnings_if_accepted', 'teacher_earnings_if_declined'
        ]
        read_only_fields = [
            'id', 'student_email', 'course_title', 'created_at',
            'teo_cost_display', 'teacher_bonus_display', 'discounted_price', 'is_expired'
        ]
    
    def get_teacher_earnings_if_accepted(self, obj):
        return obj.teacher_earnings_if_accepted
    
    def get_teacher_earnings_if_declined(self, obj):
        return obj.teacher_earnings_if_declined
    
    def get_time_remaining(self, obj):
        if obj.is_expired:
            return 'Expired'
        
        from django.utils import timezone
        remaining = obj.expires_at - timezone.now()
        hours = remaining.total_seconds() / 3600
        
        if hours < 1:
            minutes = remaining.total_seconds() / 60
            return f'{int(minutes)} minutes'
        elif hours < 24:
            return f'{int(hours)} hours'
        else:
            days = hours / 24
            return f'{int(days)} days'


class TeacherChoicePreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for teacher choice preferences
    """
    teacher_email = serializers.CharField(source='teacher.email', read_only=True)
    preference_display = serializers.CharField(source='get_preference_display', read_only=True)
    
    class Meta:
        model = TeacherChoicePreference
        fields = [
            'id', 'teacher_email', 'preference', 'preference_display',
            'minimum_teo_threshold', 'email_notifications', 'immediate_notifications',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'teacher_email', 'created_at', 'updated_at']
    
    def validate_minimum_teo_threshold(self, value):
        """Validate threshold is positive if provided"""
        if value is not None and value <= 0:
            raise serializers.ValidationError('Threshold must be positive')
        return value