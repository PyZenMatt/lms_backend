"""
Integration test for UserService in views

Test che le views funzionino correttamente con i services.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import json

User = get_user_model()


class UserServiceIntegrationTest(TestCase):
    """Test integration of UserService with views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.student = User.objects.create_user(
            username='integration_student',
            email='integration@test.com',
            password='testpass123',
            role='student'
        )
        
        self.teacher = User.objects.create_user(
            username='integration_teacher',
            email='integration_teacher@test.com',
            password='testpass123',
            role='teacher',
            is_approved=False
        )
    
    def test_user_profile_endpoint_with_service(self):
        """Test user profile endpoint using UserService"""
        # Login as student
        self.client.force_authenticate(user=self.student)
        
        # Call the endpoint (correct URL path)
        response = self.client.get('/api/v1/profile/')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], 'integration_student')
        self.assertEqual(data['email'], 'integration@test.com')
        self.assertEqual(data['role'], 'student')
        self.assertIn('courses', data)
        self.assertIsInstance(data['courses'], list)
        
        print("✅ User profile endpoint works with UserService!")
    
    def test_user_profile_endpoint_teacher(self):
        """Test user profile endpoint for teacher"""
        # Login as teacher
        self.client.force_authenticate(user=self.teacher)
        
        # Call the endpoint (correct URL path)
        response = self.client.get('/api/v1/profile/')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], 'integration_teacher')
        self.assertEqual(data['role'], 'teacher')
        self.assertEqual(data['is_approved'], False)
        
        print("✅ Teacher profile endpoint works with UserService!")
    
    def test_pending_teachers_endpoint(self):
        """Test pending teachers endpoint using UserService"""
        # Create admin user
        admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=admin_user)
        
        # Call the endpoint
        response = self.client.get('/api/v1/pending-teachers/')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('data', data)
        self.assertIsInstance(data['data'], list)
        
        # Should contain our pending teacher
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['email'], 'integration_teacher@test.com')
        
        print("✅ Pending teachers endpoint works with UserService!")
    
    def test_approve_teacher_endpoint(self):
        """Test approve teacher endpoint using UserService"""
        # Create admin user
        admin_user = User.objects.create_user(
            username='admin_user2',
            email='admin2@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_authenticate(user=admin_user)
        
        # Call the approve endpoint
        response = self.client.post(f'/api/v1/approve-teacher/{self.teacher.id}/')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('data', data)
        self.assertEqual(data['data']['teacher_email'], 'integration_teacher@test.com')
        
        # Verify teacher is approved in database
        self.teacher.refresh_from_db()
        self.assertTrue(self.teacher.is_approved)
        
        print("✅ Approve teacher endpoint works with UserService!")
    
    def test_reject_teacher_endpoint(self):
        """Test reject teacher endpoint using UserService"""
        # Create admin user
        admin_user = User.objects.create_user(
            username='admin_user3',
            email='admin3@test.com',
            password='testpass123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Create another teacher for rejection test
        teacher_to_reject = User.objects.create_user(
            username='reject_teacher',
            email='reject@test.com',
            password='testpass123',
            role='teacher',
            is_approved=False
        )
        
        self.client.force_authenticate(user=admin_user)
        
        # Call the reject endpoint with reason
        response = self.client.post(
            f'/api/v1/reject-teacher/{teacher_to_reject.id}/',
            data={'reason': 'Test rejection reason'},
            format='json'
        )
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('data', data)
        self.assertEqual(data['data']['teacher_email'], 'reject@test.com')
        self.assertEqual(data['data']['rejection_reason'], 'Test rejection reason')
        
        print("✅ Reject teacher endpoint works with UserService!")
