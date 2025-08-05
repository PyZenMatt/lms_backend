from django.contrib import admin
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import ExerciseSubmission, ExerciseReview, User, Lesson, Exercise, Course
from django import forms
from notifications.models import Notification

class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra solo studenti per il campo students
        if 'students' in self.fields:
            self.fields['students'].queryset = User.objects.filter(role='student')
        # Filtra solo docenti per il campo teacher
        if 'teacher' in self.fields:
            self.fields['teacher'].queryset = User.objects.filter(role='teacher')

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'teacher', 'duration']
    list_editable = ['duration']
    list_filter = ['course__teacher', 'teacher']
    search_fields = ['title', 'course__title']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(teacher=request.user)
        return qs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "teacher":
            kwargs["queryset"] = User.objects.filter(role='teacher')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)

@admin.register(ExerciseSubmission)
class ExerciseSubmissionAdmin(admin.ModelAdmin):
    list_display = ['exercise', 'student', 'average_score', 'is_approved']
    list_filter = ['exercise__lesson__course', 'is_approved']
    search_fields = ['exercise__title', 'student__username']
    readonly_fields = ['average_score', 'is_approved']

    def get_queryset(self, request):
        # Filtra le submission in base al ruolo dell'utente
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(exercise__lesson__course__teacher=request.user)
        return qs

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'lesson', 'get_course', 'get_teacher']
    list_filter = ['lesson__course__teacher', 'lesson']
    search_fields = ['title', 'lesson__title', 'lesson__course__title']
    autocomplete_fields = ['lesson']

    def get_course(self, obj):
        # Mostra il corso associato alla lezione
        return obj.lesson.course.title
    get_course.short_description = "Corso"

    def get_teacher(self, obj):
        # Mostra il docente associato al corso
        return obj.lesson.course.teacher.username
    get_teacher.short_description = "Docente"
    
    def __str__(self):
        student_username = self.student.username if self.student else "Nessuno studente"
        return f"{student_username} - {self.lesson.title}"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    form = CourseAdminForm 
    list_display = ['id', 'title', 'price_eur', 'teacher', 'total_students', 'is_approved']
    list_filter = ['teacher', 'is_approved']
    search_fields = ['title']
    autocomplete_fields = ['students', 'teacher']
    actions = ['approve_courses']

    def get_students(self, obj):
        # Mostra gli studenti iscritti al corso
        students = obj.students.all()
        return ", ".join([student.username for student in students])
    get_students.short_description = "Studenti Iscritti"

    # Nuovo metodo per contare gli studenti
    def total_students(self, obj):
        return obj.students.count()
    total_students.short_description = "Studenti Iscritti"

    def get_search_results(self, request, queryset, search_term):
        if 'autocomplete' in request.path:
            field_name = request.GET.get('field_name', '')
            if field_name == 'students':
                return User.objects.filter(
                    role='student',
                    username__icontains=search_term
                ), False
            elif field_name == 'teacher':
                return User.objects.filter(
                    role='teacher',
                    username__icontains=search_term
                ), False
        return super().get_search_results(request, queryset, search_term)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and request.user.role == 'teacher':
            form.base_fields['teacher'].initial = request.user
            form.base_fields['teacher'].disabled = True
            form.base_fields['teacher'].widget.can_add_related = False
            form.base_fields['teacher'].widget.can_change_related = False
        return form

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            obj.teacher = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Approva i corsi selezionati e invia notifica")
    def approve_courses(self, request, queryset):
        updated = 0
        for course in queryset:
            if not course.is_approved:
                course.is_approved = True
                course.save()
                Notification.objects.create(
                    user=course.teacher,
                    message=f"Il tuo corso '{course.title}' è stato approvato!",
                    notification_type='course_approved',
                    related_object_id=course.pk
                )
                updated += 1
        self.message_user(request, f"{updated} corsi approvati e notifica inviata.")

@admin.register(ExerciseReview)
class ExerciseReviewAdmin(admin.ModelAdmin):
    list_display = ['submission', 'reviewer', 'score', 'created_at']
    list_filter = ['submission__exercise__lesson__course', 'reviewer']
    search_fields = ['submission__exercise__title', 'reviewer__username']
    readonly_fields = ['created_at']

    def get_queryset(self, request):
        # Filtra le review in base al ruolo dell'utente
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(submission__exercise__lesson__course__teacher=request.user)
        return qs


