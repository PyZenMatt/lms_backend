from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrApprovedTeacherOrReadOnly(BasePermission):
    """
    - Metodi SAFE (GET, HEAD, OPTIONS) sono sempre permessi.
    - Per operazioni non-safe (POST, PUT, PATCH, DELETE):
      • Gli admin (is_staff) passano sempre.
      • Gli utenti con role='teacher' devono avere is_approved=True.
      • Tutti gli altri (studenti o teacher non approvati) vengono bloccati.
    """
    message = "Devi essere un insegnante approvato o admin per modificare questo contenuto."

    def has_permission(self, request, view):
        # Lettura sempre permessa
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        # Solo utenti autenticati
        if not user or not user.is_authenticated:
            return False

        # Admin
        if user.is_staff:
            return True

        # Insegnante approvato
        if user.role == 'teacher' and user.is_approved:
            return True

        # In tutti gli altri casi, blocca
        return False

class IsTeacher(permissions.BasePermission):
    def has_permission(self, request, view):
        print("DEBUG IsTeacher:", getattr(request.user, 'role', None))
        return request.user.is_authenticated and request.user.role == 'teacher'
    
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        print("DEBUG IsStudent:", getattr(request.user, 'role', None))
        return hasattr(request.user, 'role') and request.user.role == 'student'