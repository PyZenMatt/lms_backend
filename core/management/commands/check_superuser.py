from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate

User = get_user_model()

class Command(BaseCommand):
    help = 'Check superuser status and test authentication'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email to check')
        parser.add_argument('--password', type=str, help='Password to test')

    def handle(self, *args, **options):
        self.stdout.write("=== SUPERUSER CHECK ===")
        
        # List all superusers
        superusers = User.objects.filter(is_superuser=True)
        self.stdout.write(f"Found {superusers.count()} superuser(s):")
        
        for user in superusers:
            self.stdout.write(f"  - {user.email} (PK: {user.pk}, is_active: {user.is_active}, is_staff: {user.is_staff})")
        
        # Test authentication if credentials provided
        if options['email'] and options['password']:
            self.stdout.write(f"\n=== TESTING AUTHENTICATION ===")
            email = options['email']
            password = options['password']
            
            try:
                user = User.objects.get(email=email)
                self.stdout.write(f"User found: {user.email}")
                self.stdout.write(f"  - is_active: {user.is_active}")
                self.stdout.write(f"  - is_staff: {user.is_staff}")
                self.stdout.write(f"  - is_superuser: {user.is_superuser}")
                self.stdout.write(f"  - last_login: {user.last_login}")
                
                # Test password
                if user.check_password(password):
                    self.stdout.write(self.style.SUCCESS("✓ Password is correct"))
                else:
                    self.stdout.write(self.style.ERROR("✗ Password is incorrect"))
                
                # Test authentication
                auth_user = authenticate(email=email, password=password)
                if auth_user:
                    self.stdout.write(self.style.SUCCESS("✓ Authentication successful"))
                else:
                    self.stdout.write(self.style.ERROR("✗ Authentication failed"))
                    
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with email {email} not found"))
        
        self.stdout.write("\n=== END CHECK ===")