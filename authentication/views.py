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

class LogoutView(views.APIView):
    """
    API view for user logout.
    
    Blacklists the provided refresh token to prevent further use.
    Requires user to be authenticated to access this endpoint.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
        Logout user by blacklisting their refresh token.
        
        Args:
            request: HTTP request containing refresh token
            
        Returns:
            Empty response with 204 status on success, 400 on error
        """
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Blacklist the refresh token to prevent further use
            token = RefreshToken(serializer.validated_data['refresh']) # type: ignore
            token.blacklist()
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_204_NO_CONTENT)

