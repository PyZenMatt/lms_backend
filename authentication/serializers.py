from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

# Get the custom User model
User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that adds user-specific data to the token response.
    
    Extends the default TokenObtainPairSerializer to include additional user claims
    like username, role, and teo_coins balance in the JWT token payload.
    """
    
    @classmethod
    def get_token(cls, user):
        """
        Generate JWT token with custom claims.
        
        Args:
            user: User instance for whom to generate the token
            
        Returns:
            JWT token with custom claims added
        """
        token = super().get_token(user)
        
        # Add custom claims to the token payload
        token['username'] = user.username
        token['role'] = user.role
        
        # Get TEO balance from blockchain if wallet is connected
        teo_balance = 0
        if user.wallet_address:
            try:
                from blockchain.blockchain import teocoin_service
                balance = teocoin_service.get_balance(user.wallet_address)
                teo_balance = float(balance) if balance else 0
            except Exception:
                teo_balance = 0
        
        token['teo_coins'] = teo_balance
        
        return token

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles the creation of new user accounts with email verification.
    Password is write-only for security purposes.
    """
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')

    def create(self, validated_data):
        """
        Create a new user account and send email verification.
        
        Args:
            validated_data: Validated user registration data
            
        Returns:
            Created User instance
        """
        # Create new user with provided data
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role'],
            is_active=True,  # User is active but email not verified
        )
        
        # Send email verification
        request = self.context.get('request')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        verify_url = f"{request.scheme}://{request.get_host()}/api/auth/verify-email/{uid}/{token}/" # type: ignore
        
        # Send verification email to user
        user.email_user(
            subject='Verifica la tua email',  # Subject: Verify your email
            message=f'Visita {verify_url} per verificare la tua email.'  # Message: Visit URL to verify email
        )
        return user

class EmailVerifySerializer(serializers.Serializer):
    """
    Serializer for email verification process.
    
    Validates the UID and token sent via email verification link.
    """
    uid = serializers.CharField()  # Base64 encoded user ID
    token = serializers.CharField()  # Email verification token

class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Validates email and password for authentication.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class LogoutSerializer(serializers.Serializer):
    """
    Serializer for user logout.
    
    Handles the refresh token for JWT token blacklisting.
    """
    refresh = serializers.CharField()  # JWT refresh token to be blacklisted

