from courses.models import Course
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.action(description="Approva i teacher selezionati")
def make_teachers_approved(modeladmin, request, queryset):
    queryset.filter(role="teacher").update(is_approved=True)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Informazioni Personali", {"fields": ("first_name", "last_name", "email")}),
        ("Contatto & Indirizzo", {"fields": ("phone", "address", "via", "cap", "city")}),
        (
            "Permessi",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Ruolo & Blockchain", {"fields": ("role", "wallet_address")}),
        ("Profilo Social & Competenze", {"fields": ("linkedin", "github", "instagram", "facebook", "skills")}),
        ("Date importanti", {"fields": ("last_login", "date_joined")}),
    )

    def email_link(self, obj):
        from django.utils.html import format_html

        url = f"/admin/users/user/{obj.pk}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.email)

    email_link.short_description = "Email"

    list_display = (
        "username",
        "email_link",
        "role",
        "city",
        "get_skills",
        "wallet_address",
        "is_staff",
        "is_approved",
        "is_active",
    )
    list_filter = ("role", "is_approved", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email", "first_name", "last_name", "city")
    actions = [make_teachers_approved]

    def get_search_results(self, request, queryset, search_term):
        """
        Filtra i risultati di ricerca per l'autocomplete nei campi correlati.
        """
        if "autocomplete" in request.path:
            model_name = request.GET.get("model_name", "")
            field_name = request.GET.get("field_name", "")
            if model_name == "course" and field_name == "students":
                queryset = queryset.filter(role="student")
            elif model_name == "course" and field_name == "teacher":
                queryset = queryset.filter(role="teacher")
        return super().get_search_results(request, queryset, search_term)

    def get_courses(self, obj):
        """
        Mostra i corsi a cui lo studente è iscritto.
        """
        if obj.role == "student":
            courses = Course.objects.filter(students=obj)
            return ", ".join([course.title for course in courses])
        return "N/A"

    get_courses.short_description = "Corsi Iscritti"

    readonly_fields = ["get_courses"]

    def get_skills(self, obj):
        return obj.skills or ""

    get_skills.short_description = "Skills"
    get_skills.admin_order_field = "skills"
