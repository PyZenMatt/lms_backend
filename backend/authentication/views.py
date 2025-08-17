"""
Authentication views for the school platform.

This module contains all the views for user authentication including:
- User registration with email verification
- Email verification handling
- Login (both API and template-based)
- Logout with JWT token blacklisting
"""

from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import status, generics, views, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    RegisterSerializer, EmailVerifySerializer,
    LoginSerializer, LogoutSerializer
)
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Get the custom User model
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    API view for user registration.
    
    Allows new users to register by providing username, email, password, and role.
    Automatically sends email verification after successful registration.
    No authentication required (public endpoint).
    """
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    
    def create(self, request, *args, **kwargs):
        """Override create to provide custom response"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"📝 Registration attempt for: {request.data.get('username', 'unknown')}")
            
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            logger.info(f"✅ Registration successful for: {user.username}")
            
            # Custom success response
            return Response({
                'success': True,
                'message': 'Registrazione completata con successo',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role,
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"❌ Registration failed: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(views.APIView):
    """
    API view for email verification.
    
    Handles GET requests with UID and token from email verification links.
    Activates user account and marks email as verified upon successful verification.
    No authentication required (public endpoint).
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, uid, token):
        """
        Verify user email using UID and token from verification link.
        
        Args:
            request: HTTP request object
            uid: Base64 encoded user ID
            token: Email verification token
            
        Returns:
            JSON response indicating success or failure of verification
        """
        # Validate the provided UID and token using serializer
        serializer = EmailVerifySerializer(data={'uid': uid, 'token': token})
        serializer.is_valid(raise_exception=True)

        try:
            # Decode the user ID from base64
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid'])) # type: ignore
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Link non valido.'},  # Invalid link
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify the token and activate user if valid
        if default_token_generator.check_token(user, serializer.validated_data['token']): # type: ignore
            user.is_active = True
            user.is_email_verified = True # type: ignore
            user.save()
            return Response(
                {'detail': 'Email verificata con successo.'},  # Email verified successfully
                status=status.HTTP_200_OK
            )

        return Response(
            {'detail': 'Token non valido.'},  # Invalid token
            status=status.HTTP_400_BAD_REQUEST
        )


class LoginApiView(views.APIView):
    """
    API view for user login.
    
    Authenticates users with email and password, returns JWT tokens upon success.
    Handles account activation checks and provides appropriate error messages.
    No authentication required (public endpoint).
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """
        Authenticate user and return JWT tokens.
        
        Args:
            request: HTTP request containing email and password
            
        Returns:
            JSON response with access and refresh tokens, or error message
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email'] # type: ignore
        password = serializer.validated_data['password'] # type: ignore
        
        # Attempt to authenticate user
        user = authenticate(request, username=email, password=password)

        # Debug logging (consider using proper logging in production)
        print(f"Email: {email}, Password: {password}")
        print(f"Utente autenticato: {user}")  # Authenticated user

        if not user:
            # Log authentication failure for debugging
            print(f"Autenticazione fallita per email: {email}")  # Authentication failed for email
            return Response(
                {'detail': 'Credenziali non valide.'},  # Invalid credentials
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'Account non attivo. Verifica la tua email.'},  # Account inactive. Verify your email
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens for authenticated user
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })

class LoginTemplateView(TemplateView):
    """
    Template-based view for user login.
    
    Provides HTML login form and handles form submission.
    Redirects to user profile upon successful login.
    Used for web interface rather than API.
    """
    template_name = 'login.html'

    def post(self, request, *args, **kwargs):
        """
        Handle login form submission.
        
        Args:
            request: HTTP request containing form data
            
        Returns:
            Redirect to profile page or render login form with error
        """
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate the user with provided credentials
        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                # Login user and redirect to profile page
                login(request, user)
                return redirect('account-profile')  # Replace with appropriate URL name
            else:
                # Account not active - needs email verification
                return render(request, self.template_name, {
                    'error': 'Account non attivo. Verifica la tua email.'  # Account inactive. Verify your email
                })
        else:
            # Invalid credentials provided
            return render(request, self.template_name, {
                'error': 'Credenziali non valide.'  # Invalid credentials
            })


from django.contrib.auth import logout as django_logout
import logging

logger = logging.getLogger('authentication')

class LogoutView(views.APIView):
    """
    API view for user logout.
    Invalida sia la sessione Django che il refresh token JWT (se presente).
    Forza l'eliminazione di tutte le sessioni dell'utente.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        logger.info(f"🔓 Logout started for user: {request.user.username}")
        logger.info(f"🔓 Request headers: {dict(request.headers)}")
        logger.info(f"🔓 Request data: {request.data}")
        logger.info(f"🔓 Session key before logout: {request.session.session_key}")
        
        # Forza eliminazione di tutte le sessioni dell'utente
        from django.contrib.sessions.models import Session
        from django.contrib.auth import get_user_model
        
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
        
        logger.info(f"🔓 Found {len(user_sessions)} sessions for user: {user_sessions}")
        
        # Elimina tutte le sessioni dell'utente
        Session.objects.filter(session_key__in=user_sessions).delete()
        logger.info(f"🔓 Deleted {len(user_sessions)} sessions for user")
        
        # Logout sessione Django corrente
        django_logout(request)
        logger.info("🔓 Django session logout completed")
        logger.info(f"🔓 Session key after logout: {request.session.session_key}")
        
        # Blacklist refresh token se presente
        refresh = request.data.get('refresh') or request.data.get('refreshToken')
        if refresh:
            from rest_framework_simplejwt.tokens import RefreshToken
            try:
                token = RefreshToken(refresh)
                token.blacklist()
                logger.info("🔓 JWT refresh token blacklisted successfully")
            except Exception as e:
                logger.error(f"🔓 Failed to blacklist JWT token: {e}")
        else:
            logger.warning("🔓 No refresh token provided in request")
        
        response = Response({'detail': 'Logout successful'}, status=status.HTTP_200_OK)
        
        # Cancellazione cookie di autenticazione
        response.delete_cookie('sessionid', path='/', domain=None)
        response.delete_cookie('csrftoken', path='/', domain=None)
        
        logger.info("🔓 Logout completed successfully")
        return response

