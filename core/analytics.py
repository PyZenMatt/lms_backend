from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from decimal import Decimal
from datetime import datetime, timedelta
from courses.models import Course, CourseEnrollment
from users.models import User
import json


@csrf_exempt
@require_http_methods(["GET"])
def analytics_dashboard(request):
    """
    Analytics dashboard for admin users - Revenue and TeoCoin metrics
    """
    # For development, we'll allow unauthenticated access temporarily
    # In production, uncomment these lines:
    # if not request.user.is_authenticated or not request.user.is_staff:
    #     return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Calculate analytics data
    analytics_data = get_analytics_data()
    return JsonResponse(analytics_data)


def get_analytics_data():
    """Get comprehensive analytics data for dashboard"""
    
    # Revenue Analytics
    total_revenue_eur = CourseEnrollment.objects.filter(
        payment_method='fiat'
    ).aggregate(
        total=Sum('amount_paid_eur')
    )['total'] or Decimal('0')
    
    teocoin_payments = CourseEnrollment.objects.filter(
        payment_method='teocoin'
    ).aggregate(
        total=Sum('amount_paid_teocoin')
    )['total'] or Decimal('0')
    
    # TEO Rewards Distributed
    total_teo_rewards = CourseEnrollment.objects.filter(
        teocoin_reward_given__gt=0
    ).aggregate(
        total=Sum('teocoin_reward_given')
    )['total'] or Decimal('0')
    
    # Course Statistics
    total_courses = Course.objects.filter(is_approved=True).count()
    paid_courses = Course.objects.filter(is_approved=True, price_eur__gt=0).count()
    free_courses = Course.objects.filter(is_approved=True, price_eur=0).count()
    
    # Enrollment Statistics
    total_enrollments = CourseEnrollment.objects.count()
    fiat_enrollments = CourseEnrollment.objects.filter(payment_method='fiat').count()
    teocoin_enrollments = CourseEnrollment.objects.filter(payment_method='teocoin').count()
    free_enrollments = CourseEnrollment.objects.filter(payment_method='free').count()
    
    # Top Courses by Revenue
    top_courses = Course.objects.filter(
        enrollments__payment_method='fiat'
    ).annotate(
        revenue=Sum('enrollments__amount_paid_eur'),
        enrollment_count=Count('enrollments')
    ).order_by('-revenue')[:5]
    
    # Recent Activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_enrollments = CourseEnrollment.objects.filter(
        enrolled_at__gte=week_ago
    ).count()
    
    recent_revenue = CourseEnrollment.objects.filter(
        enrolled_at__gte=week_ago,
        payment_method='fiat'
    ).aggregate(
        total=Sum('amount_paid_eur')
    )['total'] or Decimal('0')
    
    # Payment Method Distribution
    payment_distribution = {
        'fiat': fiat_enrollments,
        'teocoin': teocoin_enrollments,
        'free': free_enrollments
    }
    
    # Calculate conversion rates
    total_users = User.objects.count()
    paying_users = CourseEnrollment.objects.filter(
        Q(payment_method='fiat') | Q(payment_method='teocoin')
    ).values('student').distinct().count()
    
    conversion_rate = (paying_users / total_users * 100) if total_users > 0 else 0
    
    # Average order value
    aov = (total_revenue_eur / fiat_enrollments) if fiat_enrollments > 0 else Decimal('0')
    
    return {
        'overview': {
            'total_revenue_eur': float(total_revenue_eur),
            'teocoin_payments': float(teocoin_payments),
            'total_teo_rewards': float(total_teo_rewards),
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'conversion_rate': round(conversion_rate, 2),
            'average_order_value': float(aov),
        },
        'courses': {
            'total': total_courses,
            'paid': paid_courses,
            'free': free_courses,
        },
        'enrollments': {
            'total': total_enrollments,
            'by_payment_method': payment_distribution,
        },
        'recent_activity': {
            'enrollments_7d': recent_enrollments,
            'revenue_7d': float(recent_revenue),
        },
        'top_courses': [
            {
                'title': course.title,
                'revenue': float(course.revenue or 0),
                'enrollments': course.enrollment_count,
                'price': float(course.price_eur),
            }
            for course in top_courses if hasattr(course, 'revenue')
        ],
        'teo_economics': {
            'total_rewards_distributed': float(total_teo_rewards),
            'teocoin_payments_value': float(teocoin_payments),
            'fiat_to_teo_ratio': float(total_revenue_eur / teocoin_payments) if teocoin_payments > 0 else 0,
        }
    }


@csrf_exempt
@require_http_methods(["GET"])
def revenue_chart_data(request):
    """API endpoint for revenue chart data"""
    # For development, we'll allow unauthenticated access temporarily
    # In production, uncomment these lines:
    # if not request.user.is_authenticated or not request.user.is_staff:
    #     return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get daily revenue for last 30 days
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    daily_revenue = {}
    enrollments = CourseEnrollment.objects.filter(
        enrolled_at__gte=thirty_days_ago,
        payment_method='fiat'
    ).order_by('enrolled_at')
    
    for enrollment in enrollments:
        date_key = enrollment.enrolled_at.strftime('%Y-%m-%d')
        if date_key not in daily_revenue:
            daily_revenue[date_key] = 0
        daily_revenue[date_key] += float(enrollment.amount_paid_eur)
    
    # Fill missing dates with 0
    chart_data = []
    current_date = thirty_days_ago.date()
    end_date = datetime.now().date()
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        chart_data.append({
            'date': date_str,
            'revenue': daily_revenue.get(date_str, 0)
        })
        current_date += timedelta(days=1)
    
    return JsonResponse({
        'chart_data': chart_data,
        'total_revenue': sum(daily_revenue.values()),
        'days_count': len(chart_data)
    })


@csrf_exempt
@require_http_methods(["GET"])
def public_stats(request):
    """Public statistics for marketing/investor pages"""
    
    stats = {
        'total_courses': Course.objects.filter(is_approved=True).count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_teachers': User.objects.filter(role='teacher', is_approved=True).count(),
        'categories_count': Course.objects.filter(
            is_approved=True
        ).values('category').distinct().count(),
        'success_stories': {
            'courses_completed': CourseEnrollment.objects.filter(
                teocoin_reward_given__gt=0
            ).count(),
            'teo_rewards_distributed': float(
                CourseEnrollment.objects.aggregate(
                    total=Sum('teocoin_reward_given')
                )['total'] or 0
            )
        }
    }
    
    return JsonResponse(stats)
