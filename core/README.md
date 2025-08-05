# Core App - TeoArt School Platform

The **Core** app provides essential shared functionality and infrastructure for the TeoArt School Platform. This app contains reusable components, utilities, and services that are used across the entire platform.

## 📁 **App Structure**

```
core/
├── __init__.py                 # Python package initialization
├── apps.py                     # Django app configuration
├── README.md                   # This documentation file
│
├── middleware.py               # Custom middleware (JWT, timing, access control)
├── api_standards.py           # Standardized API response utilities
├── constants.py               # Platform-wide constants and choices
├── serializers.py             # Shared serializers
├── signals.py                 # Django signal handlers
├── cache_signals.py           # Cache invalidation signal handlers
├── health_check.py            # System health monitoring
├── urls.py                    # Core URL configuration
│
├── api.py                     # Legacy API views
├── dashboard.py               # Dashboard API views
├── batch_api.py               # Batch data APIs for performance
├── tasks.py                   # Celery background tasks
│
├── management/                # Django management commands
│   └── commands/
│       ├── seed_db.py         # Database seeding command
│       └── rotate_stale_reviewers.py  # Review rotation command
│
└── tests/                     # Comprehensive test suite
    ├── test_models.py
    ├── test_views.py
    ├── test_serializers.py
    ├── test_permissions.py
    ├── test_performance.py
    └── ...
```

## 🎯 **Purpose & Functionality**

### **Core Responsibilities**

1. **API Standardization**: Consistent response formats across all endpoints
2. **Performance Monitoring**: Request timing and optimization tracking
3. **Security & Access Control**: Role-based access middleware
4. **Health Monitoring**: System status and service availability checks
5. **Cache Management**: Intelligent cache invalidation and optimization
6. **Shared Utilities**: Common constants, serializers, and helpers
7. **Signal Handling**: Automated business logic triggers

### **Key Features**

- ✅ **Standardized API Responses** - Consistent JSON format across platform
- ✅ **Performance Monitoring** - Automatic API timing and slow query detection
- ✅ **Health Check System** - Comprehensive service monitoring
- ✅ **Cache Optimization** - Smart invalidation for better performance
- ✅ **Role-Based Security** - Middleware for dashboard access control
- ✅ **Signal Automation** - Automatic notifications and business logic
- ✅ **Batch APIs** - Optimized data loading for frontend

## 🔧 **Technical Components**

### **Middleware (`middleware.py`)**

| Middleware | Purpose | Features |
|------------|---------|----------|
| `AutoJWTFromSessionMiddleware` | JWT token management | Auto-generation, secure cookies, session storage |
| `DashboardAccessMiddleware` | Role-based access control | Student/Teacher/Admin area protection |
| `APITimingMiddleware` | Performance monitoring | Request timing, slow query detection |

### **API Standards (`api_standards.py`)**

Provides consistent API response formatting:

```python
# Success Response
{
    "success": true,
    "message": "Operation completed successfully",
    "status_code": 200,
    "data": { ... }
}

# Error Response
{
    "success": false,
    "message": "Error description",
    "status_code": 400,
    "errors": { ... }
}
```

**Available Response Types:**
- `APIResponse.success()` - Success responses
- `APIResponse.error()` - Error responses  
- `APIResponse.validation_error()` - Validation errors
- `APIResponse.not_found()` - 404 responses
- `APIResponse.unauthorized()` - 401 responses
- `APIResponse.forbidden()` - 403 responses
- `APIResponse.server_error()` - 500 responses

### **Constants (`constants.py`)**

Centralized platform constants:

- **User Roles**: Student, Teacher, Admin
- **Course Categories**: Painting, Drawing, Digital Art, etc.
- **Transaction Types**: TeoCoin earning/spending types
- **Notification Types**: System notification categories
- **Cache Settings**: Keys, timeouts, pagination
- **File Upload**: Allowed types and size limits

### **Health Check (`health_check.py`)**

**Endpoint**: `GET /api/v1/health/`

Monitors critical services:
- **Database**: PostgreSQL connectivity and operations
- **Cache**: Redis connectivity and read/write operations
- **Celery**: Background task processing status

**Response Format**:
```json
{
    "status": "healthy",
    "checks": {
        "database": "healthy",
        "cache": "healthy", 
        "celery": "healthy"
    }
}
```

### **Cache Management (`cache_signals.py`)**

Automatic cache invalidation on model changes:

- **Student Progress**: Auto-invalidates when lessons completed
- **Course Enrollment**: Updates student/teacher dashboards
- **Blockchain Transactions**: Refreshes balance displays
- **User Progress**: Updates achievement tracking

### **Batch APIs (`batch_api.py`)**

Performance-optimized endpoints for frontend:

- `StudentBatchDataAPI` - All student dashboard data in one request
- `CourseBatchDataAPI` - Complete course information with relations
- `LessonBatchDataAPI` - Lesson content with progress tracking

## 🚀 **Usage Examples**

### **Using Standardized API Responses**

```python
from core.api_standards import APIResponse, StandardizedAPIView

class MyAPIView(StandardizedAPIView, APIView):
    def get(self, request):
        try:
            data = {"message": "Hello World"}
            return self.handle_success(data, "Data retrieved successfully")
        except Exception as e:
            return self.handle_server_error(e)
```

### **Using Platform Constants**

```python
from core.constants import USER_ROLES, TEOCOIN_TRANSACTION_TYPES

class User(models.Model):
    role = models.CharField(max_length=20, choices=USER_ROLES)

class Transaction(models.Model):
    type = models.CharField(max_length=50, choices=TEOCOIN_TRANSACTION_TYPES)
```

### **Health Check Integration**

```bash
# Check platform health
curl http://localhost:8000/api/v1/health/

# Use in load balancer health checks
curl -f http://platform.example.com/api/v1/health/ || exit 1
```

## 🧪 **Testing**

The core app includes comprehensive tests:

```bash
# Run all core tests
python manage.py test core

# Run specific test categories
python manage.py test core.tests.test_middleware
python manage.py test core.tests.test_api_standards
python manage.py test core.tests.test_health_check
```

**Test Coverage**:
- ✅ Middleware functionality
- ✅ API response formatting
- ✅ Health check endpoints
- ✅ Cache invalidation
- ✅ Signal handlers
- ✅ Permission controls

## 📈 **Performance Monitoring**

### **API Timing Logs**

Monitor slow endpoints via logs:

```
INFO api_performance - API GET /api/v1/dashboard/student/ - 0.245s - 200
WARNING api_performance - SLOW API POST /api/v1/courses/ - 1.340s - Consider optimization
ERROR api_performance - VERY SLOW API GET /api/v1/transactions/ - 3.120s - Immediate attention required
```

### **Cache Optimization**

Cache keys and timeouts defined in constants:

```python
CACHE_KEYS = {
    'USER_PROFILE': 'user_profile_{user_id}',
    'COURSE_LIST': 'course_list_{category}_{page}',
    'TEOCOIN_BALANCE': 'teocoin_balance_{user_id}',
}

CACHE_TIMEOUTS = {
    'SHORT': 300,    # 5 minutes
    'MEDIUM': 3600,  # 1 hour  
    'LONG': 86400,   # 24 hours
}
```

## 🔒 **Security Features**

### **JWT Token Management**

- Automatic token generation for authenticated users
- Secure HTTP-only cookies
- Session storage backup
- 30-minute token expiration

### **Role-Based Access Control**

- Automatic dashboard area protection
- Student/Teacher/Admin separation
- Request logging for security auditing

## 🏗️ **Architecture Integration**

The Core app integrates with:

- **Authentication App**: JWT token management
- **Users App**: Role-based permissions
- **Courses App**: Cache invalidation, progress tracking  
- **Rewards App**: Transaction serialization
- **Notifications App**: Signal-triggered notifications
- **Blockchain App**: Performance monitoring

## 📚 **Development Guidelines**

### **Adding New API Endpoints**

1. Use `StandardizedAPIView` mixin for consistent responses
2. Follow the established URL patterns in `urls.py`
3. Add comprehensive docstrings and type hints
4. Include appropriate tests

### **Adding New Constants**

1. Add to appropriate section in `constants.py`
2. Use descriptive variable names in UPPER_CASE
3. Include comments explaining usage
4. Update documentation

### **Performance Considerations**

1. Use batch APIs for data-heavy operations
2. Implement proper cache invalidation signals
3. Monitor API timing logs for optimization opportunities
4. Consider background tasks for heavy operations

## 🐛 **Troubleshooting**

### **Common Issues**

**Health Check Failing**:
- Check database connectivity
- Verify Redis is running
- Confirm Celery workers are active

**Slow API Responses**:
- Review API timing logs
- Check for N+1 queries
- Verify cache invalidation is working

**JWT Token Issues**:
- Check middleware configuration
- Verify session backend settings
- Confirm token expiration settings

### **Monitoring & Logs**

**Log Categories**:
- `api_performance` - API timing and performance
- `health_check` - System health monitoring  
- `authentication` - JWT and access control
- `signals` - Business logic automation
- `api_responses` - API error tracking

## 📞 **Support**

For issues related to the Core app:

1. Check the comprehensive test suite
2. Review performance monitoring logs
3. Consult the health check endpoint
4. Refer to the API standards documentation

The Core app is the foundation of the TeoArt School Platform - ensuring reliability, performance, and consistency across all platform features.
