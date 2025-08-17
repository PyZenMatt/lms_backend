# Authentication App

The authentication app handles user registration, login, logout, email verification, and JWT token management for the SchoolPlatform.

## 📁 Structure

```
authentication/
├── __init__.py           # Python package initialization
├── apps.py              # Django app configuration
├── serializers.py       # DRF serializers for API data validation
├── urls.py              # URL routing configuration
├── views.py             # API and template views
├── migrations/          # Database migrations (empty - uses core User model)
└── __pycache__/         # Python bytecode cache
```

## 🔐 Features

### User Registration
- **Endpoint**: `POST /api/auth/register/`
- **Functionality**: 
  - Creates new user accounts
  - Automatically sends email verification
  - Supports role-based registration (student, teacher, admin)
  - Password is securely hashed

### Email Verification
- **Endpoint**: `GET /api/auth/verify-email/<uid>/<token>/`
- **Functionality**:
  - Verifies user email addresses via secure tokens
  - Activates user accounts upon successful verification
  - Uses Django's built-in token generator for security

### Login System
- **API Login**: `POST /api/auth/login/`
  - Returns JWT access and refresh tokens
  - Validates email and password
  - Checks account activation status
- **Template Login**: HTML form-based login (legacy)
  - Redirects to user profile upon success
  - Uses Django session authentication

### JWT Token Management
- **Token Obtain**: `POST /api/auth/token/`
  - Standard JWT token endpoint
  - Returns access and refresh tokens
- **Token Refresh**: `POST /api/auth/token/refresh/`
  - Refreshes expired access tokens
- **Custom Token Claims**: Includes user data in token payload
  - Username
  - User role
  - TeoCoin balance

### Logout
- **Endpoint**: `POST /api/auth/logout/`
- **Functionality**:
  - Blacklists refresh tokens to prevent reuse
  - Secure logout implementation

## 📋 API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register/` | User registration | No |
| GET | `/api/auth/verify-email/<uid>/<token>/` | Email verification | No |
| POST | `/api/auth/login/` | API login (JWT) | No |
| POST | `/api/auth/logout/` | Logout (blacklist token) | Yes |
| POST | `/api/auth/token/` | Obtain JWT tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |

## 🏗️ Components

### Serializers (`serializers.py`)

#### `CustomTokenObtainPairSerializer`
- Extends JWT token with custom user claims
- Adds username, role, and TeoCoin balance to token payload

#### `RegisterSerializer`
- Validates registration data
- Creates user accounts with email verification
- Handles password security (write-only)

#### `EmailVerifySerializer`
- Validates email verification tokens
- Processes UID and token from verification links

#### `LoginSerializer`
- Validates login credentials
- Handles email and password input

#### `LogoutSerializer`
- Processes refresh token for blacklisting

### Views (`views.py`)

#### `RegisterView`
- **Type**: `generics.CreateAPIView`
- **Permission**: `AllowAny`
- **Purpose**: User registration with automatic email verification

#### `VerifyEmailView`
- **Type**: `views.APIView`
- **Permission**: `AllowAny`
- **Purpose**: Email verification via GET request with tokens

#### `LoginApiView`
- **Type**: `views.APIView`
- **Permission**: `AllowAny`
- **Purpose**: JWT-based authentication

#### `LoginTemplateView`
- **Type**: `TemplateView`
- **Purpose**: HTML form-based login (legacy support)

#### `LogoutView`
- **Type**: `views.APIView`
- **Permission**: `IsAuthenticated`
- **Purpose**: Secure logout with token blacklisting

## 🔒 Security Features

### Email Verification
- Uses Django's built-in token generator
- Base64 encoded user IDs
- Time-limited verification tokens
- Automatic account activation

### JWT Security
- Secure token-based authentication
- Refresh token blacklisting on logout
- Custom claims for enhanced functionality
- Protection against token replay attacks

### Password Security
- Uses Django's built-in password hashing
- Write-only password fields in serializers
- No plain text password storage

### Account Activation
- Prevents login until email verification
- Clear error messages for inactive accounts
- Automatic activation upon email verification

## 📝 Usage Examples

### User Registration
```python
# POST /api/auth/register/
{
    "username": "student1",
    "email": "student1@example.com",
    "password": "securepassword123",
    "role": "student"
}
```

### User Login
```python
# POST /api/auth/login/
{
    "email": "student1@example.com",
    "password": "securepassword123"
}

# Response:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Token Refresh
```python
# POST /api/auth/token/refresh/
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Logout
```python
# POST /api/auth/logout/
# Headers: Authorization: Bearer <access_token>
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## 🔧 Configuration

### Dependencies
- `djangorestframework`
- `djangorestframework-simplejwt`
- Django's built-in authentication system
- Email backend for verification emails

### Settings Requirements
```python
# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'BLACKLIST_AFTER_ROTATION': True,
}

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Configure SMTP settings for email verification
```

## 🔍 Error Handling

### Common Error Responses

#### Invalid Credentials (401)
```json
{"detail": "Credenziali non valide."}
```

#### Account Not Active (403)
```json
{"detail": "Account non attivo. Verifica la tua email."}
```

#### Invalid Verification Link (400)
```json
{"detail": "Link non valido."}
```

#### Invalid Token (400)
```json
{"detail": "Token non valido."}
```

## 🧪 Testing

### Test Registration Flow
1. Register new user via API
2. Check email for verification link
3. Visit verification link
4. Attempt login with credentials

### Test Authentication Flow
1. Login with valid credentials
2. Use access token for authenticated requests
3. Refresh token when expired
4. Logout and verify token blacklisting

## 📚 Related Documentation

- [Core User Model](../core/README.md) - Custom user model used by authentication
- [API Standards](../core/api_standards.py) - API response standards
- [Frontend Integration](../frontend/README.md) - Frontend authentication integration

## 🚀 Future Enhancements

- Two-factor authentication (2FA)
- Social media login integration
- Password reset functionality
- Account lockout after failed attempts
- OAuth2 provider implementation

---

**Note**: This app integrates with the custom User model defined in the `core` app and uses JWT tokens for stateless authentication across the platform.
