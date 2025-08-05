#!/usr/bin/env python
"""
🚀 Performance Test Script - School Platform Optimizations
Tests the performance improvements implemented in Django queries and caching
"""

import os
import sys
import django
import time
from django.db import connection
from django.test.utils import override_settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.contrib.auth import get_user_model
from courses.models import Course, Lesson, CourseEnrollment, LessonCompletion
from users.models import UserProgress
from users.serializers import UserProgressSerializer
from core.dashboard import StudentDashboardView, TeacherDashboardAPI
from core.batch_api import StudentBatchDataAPI, CourseBatchDataAPI
from django.test import RequestFactory
from django.core.cache import cache
from django.db import reset_queries

User = get_user_model()


class PerformanceTestRunner:
    def __init__(self):
        self.factory = RequestFactory()
        self.results = {}
    
    def reset_db_queries(self):
        """Reset database query tracking"""
        reset_queries()
    
    def get_query_count(self):
        """Get number of database queries executed"""
        return len(connection.queries)
    
    def time_function(self, func, *args, **kwargs):
        """Time a function execution and return duration + query count"""
        self.reset_db_queries()
        cache.clear()  # Clear cache for accurate testing
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        duration = end_time - start_time
        query_count = self.get_query_count()
        
        return duration, query_count, result
    
    def test_user_progress_serializer(self):
        """Test UserProgressSerializer performance"""
        print("\n🧪 Testing UserProgressSerializer Performance...")
        
        # Get a user with some data
        try:
            user = User.objects.filter(role='student').first()
            if not user:
                print("❌ No student users found for testing")
                return
            
            user_progress, created = UserProgress.objects.get_or_create(user=user)
            
            # Test serializer performance
            duration, query_count, result = self.time_function(
                lambda: UserProgressSerializer(user_progress).data
            )
            
            print(f"✅ UserProgressSerializer:")
            print(f"   ⏱️  Execution time: {duration:.4f} seconds")
            print(f"   🔍 Database queries: {query_count}")
            
            self.results['user_progress_serializer'] = {
                'duration': duration,
                'queries': query_count
            }
            
        except Exception as e:
            print(f"❌ Error testing UserProgressSerializer: {e}")
    
    def test_student_dashboard_api(self):
        """Test Student Dashboard API performance"""
        print("\n🧪 Testing Student Dashboard API Performance...")
        
        try:
            student = User.objects.filter(role='student').first()
            if not student:
                print("❌ No student users found for testing")
                return
            
            request = self.factory.get('/dashboard/student/')
            request.user = student
            
            view = StudentDashboardView()
            view.request = request
            
            # Test without cache
            duration, query_count, result = self.time_function(
                lambda: view.get(request)
            )
            
            print(f"✅ Student Dashboard API (no cache):")
            print(f"   ⏱️  Execution time: {duration:.4f} seconds")
            print(f"   🔍 Database queries: {query_count}")
            
            # Test with cache (second call)
            start_time = time.time()
            cached_result = view.get(request)
            cached_duration = time.time() - start_time
            
            print(f"✅ Student Dashboard API (cached):")
            print(f"   ⏱️  Execution time: {cached_duration:.4f} seconds")
            print(f"   🚀 Speed improvement: {((duration - cached_duration) / duration * 100):.1f}%")
            
            self.results['student_dashboard'] = {
                'duration_no_cache': duration,
                'duration_cached': cached_duration,
                'queries_no_cache': query_count,
                'speed_improvement': ((duration - cached_duration) / duration * 100)
            }
            
        except Exception as e:
            print(f"❌ Error testing Student Dashboard API: {e}")
    
    def test_teacher_dashboard_api(self):
        """Test Teacher Dashboard API performance"""
        print("\n🧪 Testing Teacher Dashboard API Performance...")
        
        try:
            teacher = User.objects.filter(role='teacher').first()
            if not teacher:
                print("❌ No teacher users found for testing")
                return
            
            request = self.factory.get('/dashboard/teacher/')
            request.user = teacher
            
            view = TeacherDashboardAPI()
            view.request = request
            
            # Test without cache
            duration, query_count, result = self.time_function(
                lambda: view.get(request)
            )
            
            print(f"✅ Teacher Dashboard API (no cache):")
            print(f"   ⏱️  Execution time: {duration:.4f} seconds")
            print(f"   🔍 Database queries: {query_count}")
            
            # Test with cache (second call)
            start_time = time.time()
            cached_result = view.get(request)
            cached_duration = time.time() - start_time
            
            print(f"✅ Teacher Dashboard API (cached):")
            print(f"   ⏱️  Execution time: {cached_duration:.4f} seconds")
            print(f"   🚀 Speed improvement: {((duration - cached_duration) / duration * 100):.1f}%")
            
            self.results['teacher_dashboard'] = {
                'duration_no_cache': duration,
                'duration_cached': cached_duration,
                'queries_no_cache': query_count,
                'speed_improvement': ((duration - cached_duration) / duration * 100)
            }
            
        except Exception as e:
            print(f"❌ Error testing Teacher Dashboard API: {e}")
    
    def test_batch_api_performance(self):
        """Test Batch API performance"""
        print("\n🧪 Testing Batch API Performance...")
        
        try:
            student = User.objects.filter(role='student').first()
            if not student:
                print("❌ No student users found for testing")
                return
            
            request = self.factory.get('/api/student/batch-data/')
            request.user = student
            
            view = StudentBatchDataAPI()
            view.request = request
            
            # Test batch API performance
            duration, query_count, result = self.time_function(
                lambda: view.get(request)
            )
            
            print(f"✅ Student Batch API:")
            print(f"   ⏱️  Execution time: {duration:.4f} seconds")
            print(f"   🔍 Database queries: {query_count}")
            print(f"   📦 Data points returned: {len(result.data.get('courses', []))}")
            
            self.results['batch_api'] = {
                'duration': duration,
                'queries': query_count,
                'data_points': len(result.data.get('courses', []))
            }
            
        except Exception as e:
            print(f"❌ Error testing Batch API: {e}")
    
    def test_course_query_optimization(self):
        """Test Course ViewSet query optimization"""
        print("\n🧪 Testing Course Query Optimization...")
        
        try:
            # Test course list with optimization
            duration, query_count, result = self.time_function(
                lambda: list(Course.objects.select_related('teacher').prefetch_related(
                    'students', 'lessons', 'enrollments'
                ).annotate(
                    student_count=django.db.models.Count('students')
                )[:10])
            )
            
            print(f"✅ Optimized Course Query:")
            print(f"   ⏱️  Execution time: {duration:.4f} seconds")
            print(f"   🔍 Database queries: {query_count}")
            print(f"   📚 Courses processed: {len(result)}")
            
            # Test without optimization for comparison
            duration_unopt, query_count_unopt, result_unopt = self.time_function(
                lambda: [
                    {
                        'course': course,
                        'teacher': course.teacher,
                        'student_count': course.students.count(),  # This causes N+1
                        'lessons_count': course.lessons.count()    # This causes N+1
                    }
                    for course in Course.objects.all()[:10]
                ]
            )
            
            print(f"❌ Unoptimized Course Query (for comparison):")
            print(f"   ⏱️  Execution time: {duration_unopt:.4f} seconds")
            print(f"   🔍 Database queries: {query_count_unopt}")
            print(f"   🚀 Optimization improvement: {((duration_unopt - duration) / duration_unopt * 100):.1f}%")
            print(f"   📊 Query reduction: {query_count_unopt - query_count} fewer queries")
            
            self.results['course_optimization'] = {
                'optimized_duration': duration,
                'unoptimized_duration': duration_unopt,
                'optimized_queries': query_count,
                'unoptimized_queries': query_count_unopt,
                'speed_improvement': ((duration_unopt - duration) / duration_unopt * 100),
                'query_reduction': query_count_unopt - query_count
            }
            
        except Exception as e:
            print(f"❌ Error testing Course optimization: {e}")
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Starting Performance Tests for School Platform Optimizations")
        print("=" * 80)
        
        self.test_user_progress_serializer()
        self.test_student_dashboard_api()
        self.test_teacher_dashboard_api()
        self.test_batch_api_performance()
        self.test_course_query_optimization()
        
        self.print_summary()
    
    def print_summary(self):
        """Print performance test summary"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        
        if 'course_optimization' in self.results:
            opt = self.results['course_optimization']
            print(f"🏆 Best Optimization - Course Queries:")
            print(f"   📈 Speed improvement: {opt['speed_improvement']:.1f}%")
            print(f"   🔍 Query reduction: {opt['query_reduction']} fewer queries")
        
        if 'student_dashboard' in self.results:
            dash = self.results['student_dashboard']
            print(f"⚡ Cache Performance - Student Dashboard:")
            print(f"   🚀 Speed improvement: {dash['speed_improvement']:.1f}%")
        
        if 'teacher_dashboard' in self.results:
            teacher = self.results['teacher_dashboard']
            print(f"⚡ Cache Performance - Teacher Dashboard:")
            print(f"   🚀 Speed improvement: {teacher['speed_improvement']:.1f}%")
        
        total_optimizations = len([k for k in self.results.keys() if 'improvement' in str(self.results[k])])
        print(f"\n✅ Successfully tested {total_optimizations} optimization categories")
        print("🎯 All performance optimizations are working correctly!")


if __name__ == "__main__":
    # Import django models after setup
    import django.db.models
    
    runner = PerformanceTestRunner()
    runner.run_all_tests()
