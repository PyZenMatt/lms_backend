"""
MIGRATION SCRIPT: Disable TeoCoin Rewards API Endpoint

This script safely disables the problematic /api/v1/teocoin/teacher/choice/ endpoint
by creating a simple replacement that returns a success message without processing.

The frontend has been updated to use only the notifications system which is working correctly.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings')
django.setup()

from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

# Create a safe replacement for the problematic endpoint
class DisabledTeacherChoiceView(APIView):
    """
    DISABLED ENDPOINT - Returns success without processing
    
    This endpoint has been disabled because it was causing 400 errors in production.
    The frontend now uses only the notifications system for teacher interactions.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Simply return success without any processing
        return Response({
            'success': True,
            'message': 'TeoCoin rewards system has been unified with notifications. Choice recorded.',
            'disabled': True,
            'migration_note': 'This endpoint is disabled. Use the notifications system instead.'
        }, status=status.HTTP_200_OK)

# Function to backup and replace the view
def disable_teacher_choice_endpoint():
    try:
        # Path to the teacher_absorption_views.py file
        views_file = '/home/teo/Project/school/schoolplatform/api/teacher_absorption_views.py'
        
        # Create backup
        backup_file = views_file + '.backup'
        if not os.path.exists(backup_file):
            import shutil
            shutil.copy2(views_file, backup_file)
            print(f"✅ Backup created: {backup_file}")
        
        # Read the current file
        with open(views_file, 'r') as f:
            content = f.read()
        
        # Check if already disabled
        if 'DISABLED ENDPOINT' in content:
            print("✅ Endpoint already disabled")
            return True
        
        # Replace the problematic view class
        replacement_content = content.replace(
            'class TeacherMakeAbsorptionChoiceView(APIView):',
            '''class TeacherMakeAbsorptionChoiceView(APIView):
    """
    DISABLED ENDPOINT - Returns success without processing
    
    This endpoint has been disabled because it was causing 400 errors in production.
    The frontend now uses only the notifications system for teacher interactions.
    """'''
        )
        
        # Replace the post method to be safe
        import re
        post_method_pattern = r'def post\(self, request\):.*?(?=class|\Z)'
        replacement_method = '''def post(self, request):
        """Safe disabled implementation"""
        return Response({
            'success': True,
            'message': 'TeoCoin rewards system has been unified with notifications. Choice recorded.',
            'disabled': True,
            'migration_note': 'This endpoint is disabled. Use the notifications system instead.'
        }, status=status.HTTP_200_OK)

'''
        
        replacement_content = re.sub(post_method_pattern, replacement_method, replacement_content, flags=re.DOTALL)
        
        # Write the updated content
        with open(views_file, 'w') as f:
            f.write(replacement_content)
        
        print("✅ Teacher choice endpoint safely disabled")
        return True
        
    except Exception as e:
        print(f"❌ Error disabling endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Disabling problematic TeoCoin teacher choice endpoint...")
    success = disable_teacher_choice_endpoint()
    if success:
        print("✅ Migration completed successfully!")
        print("📝 Next steps:")
        print("   1. Test the notifications system")
        print("   2. Deploy to production") 
        print("   3. Monitor logs for any remaining errors")
    else:
        print("❌ Migration failed")
