# TeoArt School Platform - API Documentation

## API Overview

The TeoArt School Platform provides a comprehensive REST API built with Django REST Framework, featuring standardized responses, authentication, and role-based access control.

### Base URL
```
Production: https://your-domain.com/api/
Development: http://localhost:8000/api/
```

### API Standards

All API responses follow a standardized format:

#### Success Response Format
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "status_code": 200,
  "data": {
    // Response data here
  }
}
```

#### Error Response Format
```json
{
  "success": false,
  "message": "Error description",
  "status_code": 400,
  "errors": {
    // Detailed error information
  }
}
```

#### Paginated Response Format
```json
{
  "success": true,
  "message": "Data retrieved successfully",
  "status_code": 200,
  "data": {
    "results": [...],
    "pagination": {
      "count": 100,
      "next": "http://api.example.org/accounts/?page=4",
      "previous": "http://api.example.org/accounts/?page=2",
      "page_size": 20,
      "current_page": 3,
      "total_pages": 5
    }
  }
}
```

## Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Tokens) for authentication.

#### Obtain Token
```http
POST /api/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 1,
      "username": "user@example.com",
      "role": "student",
      "teo_coins": 100
    }
  }
}
```

#### Refresh Token
```http
POST /api/auth/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Using Authentication Header
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## User Management API

### User Registration
```http
POST /api/users/register/
Content-Type: application/json

{
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "password": "securepassword123",
  "role": "student"
}
```

### User Profile
```http
GET /api/users/profile/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "username": "user@example.com",
    "role": "student",
    "courses": [
      {
        "course__id": 1,
        "course__title": "Digital Art Basics",
        "completed": false
      }
    ],
    "teo_coins": 150
  }
}
```

### Update User Profile
```http
PUT /api/users/profile/
Authorization: Bearer {token}
Content-Type: multipart/form-data

{
  "username": "updated@example.com",
  "bio": "Art enthusiast and student",
  "profile_image": [file]
}
```

### User Settings
```http
GET /api/users/settings/
Authorization: Bearer {token}
```

```http
PUT /api/users/settings/
Authorization: Bearer {token}
Content-Type: application/json

{
  "email_notifications": true,
  "privacy": {
    "show_progress": true,
    "show_achievements": false
  }
}
```

### User Progress
```http
GET /api/users/progress/
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_courses_enrolled": 3,
    "total_courses_completed": 1,
    "total_lessons_completed": 15,
    "average_score": 85.5,
    "last_activity_date": "2025-06-04T10:30:00Z"
  }
}
```

## Teacher Management API

### Pending Teachers (Admin Only)
```http
GET /api/users/pending-teachers/
Authorization: Bearer {admin_token}
```

### Approve Teacher (Admin Only)
```http
POST /api/users/approve-teacher/{user_id}/
Authorization: Bearer {admin_token}
```

### Reject Teacher (Admin Only)
```http
POST /api/users/reject-teacher/{user_id}/
Authorization: Bearer {admin_token}
```

## Course Management API

### List Courses
```http
GET /api/courses/
Authorization: Bearer {token}
```

**Query Parameters:**
- `category`: Filter by course category
- `level`: Filter by difficulty level
- `search`: Search in title and description
- `page`: Page number for pagination

### Course Details
```http
GET /api/courses/{course_id}/
Authorization: Bearer {token}
```

### Create Course (Teacher Only)
```http
POST /api/courses/
Authorization: Bearer {teacher_token}
Content-Type: application/json

{
  "title": "Advanced Digital Painting",
  "description": "Learn advanced digital painting techniques",
  "category": "digital_art",
  "level": "advanced",
  "teocoin_reward": 50
}
```

### Course Enrollment
```http
POST /api/courses/{course_id}/enroll/
Authorization: Bearer {token}
```

### Course Lessons
```http
GET /api/courses/{course_id}/lessons/
Authorization: Bearer {token}
```

### Lesson Details
```http
GET /api/lessons/{lesson_id}/
Authorization: Bearer {token}
```

### Complete Lesson
```http
POST /api/lessons/{lesson_id}/complete/
Authorization: Bearer {token}
Content-Type: application/json

{
  "score": 95,
  "time_spent": 1800  // seconds
}
```

## Rewards System API

### TeoCoin Balance
```http
GET /api/rewards/balance/
Authorization: Bearer {token}
```

### Transfer TeoCoins
```http
POST /api/rewards/transfer/
Authorization: Bearer {token}
Content-Type: application/json

{
  "recipient_email": "friend@example.com",
  "amount": 50,
  "description": "Great job on your project!"
}
```

### Transaction History
```http
GET /api/rewards/transactions/
Authorization: Bearer {token}
```

**Query Parameters:**
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)
- `search`: Search in transaction type
- `ordering`: Sort by date or amount

### Trigger Lesson Completion Reward
```http
POST /api/rewards/lesson-completion/
Authorization: Bearer {token}
Content-Type: application/json

{
  "lesson_id": 123,
  "course_id": 456,
  "user_id": 789  // Optional, defaults to current user
}
```

### Course Completion Check
```http
POST /api/rewards/course-completion/
Authorization: Bearer {token}
Content-Type: application/json

{
  "course_id": 456,
  "user_id": 789  // Optional
}
```

### Achievement Reward
```http
POST /api/rewards/achievement/
Authorization: Bearer {token}
Content-Type: application/json

{
  "achievement_type": "FIRST_COURSE_COMPLETED",
  "course_id": 456  // Optional, for course-specific achievements
}
```

### Reward Summary
```http
GET /api/rewards/summary/
Authorization: Bearer {token}
```

**Query Parameters:**
- `course_id`: Get summary for specific course

### Bulk Process Rewards (Admin Only)
```http
POST /api/rewards/bulk-process/
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "user_ids": [1, 2, 3, 4, 5],
  "reward_type": "MONTHLY_BONUS"
}
```

## Notifications API

### List Notifications
```http
GET /api/notifications/
Authorization: Bearer {token}
```

**Query Parameters:**
- `unread`: Filter unread notifications (true/false)
- `type`: Filter by notification type

### Mark as Read
```http
POST /api/notifications/{notification_id}/read/
Authorization: Bearer {token}
```

### Mark All as Read
```http
POST /api/notifications/mark-all-read/
Authorization: Bearer {token}
```

## Error Codes

### Standard HTTP Status Codes

- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Permission denied
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation failed
- **500 Internal Server Error**: Server error

### Custom Error Codes

The API may include custom error codes in the `errors` field:

```json
{
  "success": false,
  "message": "Validation failed",
  "status_code": 422,
  "errors": {
    "code": "INSUFFICIENT_BALANCE",
    "field": "amount",
    "message": "Insufficient TeoCoin balance for this transaction"
  }
}
```

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Admin users**: 5000 requests per hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1625097600
```

## API Versioning

The API uses URL path versioning:
```
/api/v1/users/
/api/v2/users/  // Future version
```

Current version: **v1**

## SDK and Integration

### JavaScript/React Example
```javascript
// API client setup
const api = axios.create({
  baseURL: 'http://localhost:8000/api/',
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add authentication token
api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// Example API call
const getUserProfile = async () => {
  try {
    const response = await api.get('/users/profile/');
    if (response.data.success) {
      return response.data.data;
    }
    throw new Error(response.data.message);
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

### Error Handling Best Practices
```javascript
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 401:
        // Redirect to login
        window.location.href = '/login';
        break;
      case 403:
        // Show permission denied message
        showError('Permission denied');
        break;
      case 422:
        // Handle validation errors
        showValidationErrors(data.errors);
        break;
      default:
        showError(data.message || 'An error occurred');
    }
  } else {
    // Network error
    showError('Network error. Please check your connection.');
  }
};
```

This API documentation provides comprehensive coverage of all available endpoints and their usage patterns in the TeoArt School Platform.
