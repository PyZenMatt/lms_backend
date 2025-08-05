"""
Custom admin views for the school platform.
Overrides default Django admin behavior.
"""

from django.contrib import admin
from django.contrib.auth import logout as django_logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.sessions.models import Session
import logging

logger = logging.getLogger('authentication')

def custom_admin_logout(request):
    """
    Custom logout view for Django admin that forces session cleanup.
    """
    if request.user.is_authenticated:
        logger.info(f"🔓 Admin logout started for user: {request.user.username}")
        
        user = request.user
        user_sessions = []
        
        # Trova tutte le sessioni dell'utente
        for session in Session.objects.all():
            try:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user.id):
                    user_sessions.append(session.session_key)
            except:
                continue
        
        logger.info(f"🔓 Admin found {len(user_sessions)} sessions for user: {user_sessions}")
        
        # Elimina tutte le sessioni dell'utente
        Session.objects.filter(session_key__in=user_sessions).delete()
        logger.info(f"🔓 Admin deleted {len(user_sessions)} sessions for user")
        
        # Logout standard Django
        django_logout(request)
        logger.info("🔓 Admin logout completed successfully")
    
    # Redirect alla pagina di login dell'admin
    return HttpResponseRedirect(reverse('admin:login'))
