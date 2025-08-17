"""
Core URL configuration for the TeoArt School Platform.

This module defines URL patterns for core platform functionality including:
- Health monitoring endpoints
- Dashboard APIs for all user roles
- Batch data APIs for performance optimization
- Notification system integration

URL Patterns:
    /health/ - Platform health check endpoint
    /dashboard/ - Dashboard APIs for student, teacher, and admin
    /api/ - Batch data APIs for optimized frontend data loading
"""
from django.urls import path, include

# Import views
from .dashboard import (
    TeacherDashboardAPI, 
    StudentDashboardView, 
    dashboard_transactions, 
    UserRoleDashboardAPI, 
    AdminDashboardAPI
)
from .api import dashboard_data
from .batch_api import StudentBatchDataAPI, CourseBatchDataAPI, LessonBatchDataAPI
from .health_check import HealthCheckView
from .analytics import analytics_dashboard, revenue_chart_data, public_stats

# URL patterns organized by functionality
urlpatterns = [
    # ============================================
    # HEALTH MONITORING
    # ============================================
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # ============================================
    # DASHBOARD APIS
    # ============================================
    path('dashboard/student/', StudentDashboardView.as_view(), name='student-dashboard'),
    path('dashboard/teacher/', TeacherDashboardAPI.as_view(), name='teacher-dashboard'),
    path('dashboard/admin/', AdminDashboardAPI.as_view(), name='admin-dashboard'),
    path('dashboard/role/', UserRoleDashboardAPI.as_view(), name='user-role-dashboard'),
    path('dashboard/transactions/', dashboard_transactions, name='dashboard-transactions'),
    path('dashboard/data/', dashboard_data, name='dashboard-data'),
    
    # ============================================
    # ANALYTICS APIS (Revenue & Platform Metrics)
    # ============================================
    path('analytics/dashboard/', analytics_dashboard, name='analytics-dashboard'),
    path('analytics/revenue-chart/', revenue_chart_data, name='revenue-chart-data'),
    path('analytics/public-stats/', public_stats, name='public-stats'),
    
    # ============================================
    # BATCH DATA APIS (Performance Optimization)
    # ============================================
    path('api/student/batch-data/', StudentBatchDataAPI.as_view(), name='student-batch-data'),
    path('api/course/<int:course_id>/batch-data/', CourseBatchDataAPI.as_view(), name='course-batch-data'),
    path('api/lesson/<int:lesson_id>/batch-data/', LessonBatchDataAPI.as_view(), name='lesson-batch-data'),
    
    # ============================================
    # INTEGRATED APPS
    # ============================================
    path('', include('notifications.urls')),  # Notification system
]
