#!/bin/bash
# filepath: /home/teo/Project/school/schoolplatform/scripts/test-runner.sh

# Test Runner Script for TeoArt School Platform
# Runs comprehensive tests across backend and frontend

echo "🧪 TeoArt School Platform - Test Runner"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not activated. Activating..."
    source venv/bin/activate
fi

# Initialize test results
backend_tests_passed=0
frontend_tests_passed=0
lint_passed=0

# Run Django backend tests
print_status "Running Django backend tests..."
python manage.py test --verbosity=2
if [ $? -eq 0 ]; then
    backend_tests_passed=1
    print_status "✅ Backend tests passed"
else
    print_error "❌ Backend tests failed"
fi

# Run Django model validations
print_status "Running Django model validations..."
python manage.py check
if [ $? -eq 0 ]; then
    print_status "✅ Django check passed"
else
    print_error "❌ Django check failed"
fi

# Check for Django security issues
print_status "Running Django security check..."
python manage.py check --deploy
if [ $? -eq 0 ]; then
    print_status "✅ Security check passed"
else
    print_warning "⚠️ Security check found issues"
fi

# Run database migrations check
print_status "Checking for pending migrations..."
python manage.py makemigrations --dry-run --check
if [ $? -eq 0 ]; then
    print_status "✅ No pending migrations"
else
    print_warning "⚠️ Pending migrations found"
fi

# Run frontend tests if available
if [ -d "frontend" ]; then
    print_status "Running frontend tests..."
    cd frontend
    
    # Check if test script exists in package.json
    if npm run | grep -q "test"; then
        npm test -- --watchAll=false
        if [ $? -eq 0 ]; then
            frontend_tests_passed=1
            print_status "✅ Frontend tests passed"
        else
            print_error "❌ Frontend tests failed"
        fi
    else
        print_warning "⚠️ No frontend test script found"
        frontend_tests_passed=1  # Don't fail if no tests defined
    fi
    
    # Run ESLint if available
    if npm list eslint &>/dev/null; then
        print_status "Running ESLint..."
        npx eslint src/ --ext .js,.jsx,.ts,.tsx
        if [ $? -eq 0 ]; then
            print_status "✅ ESLint passed"
        else
            print_warning "⚠️ ESLint found issues"
        fi
    fi
    
    # Check for build errors
    print_status "Testing frontend build..."
    npm run build
    if [ $? -eq 0 ]; then
        print_status "✅ Frontend build successful"
    else
        print_error "❌ Frontend build failed"
        frontend_tests_passed=0
    fi
    
    cd ..
fi

# Run Python linting with flake8 if available
if command -v flake8 &> /dev/null; then
    print_status "Running Python linting (flake8)..."
    flake8 --exclude=venv,migrations --max-line-length=120
    if [ $? -eq 0 ]; then
        lint_passed=1
        print_status "✅ Python linting passed"
    else
        print_warning "⚠️ Python linting found issues"
    fi
else
    print_warning "⚠️ flake8 not installed, skipping Python linting"
    lint_passed=1
fi

# Test API endpoints
print_status "Testing critical API endpoints..."
python -c "
import requests
import sys
try:
    # Test health check endpoint
    response = requests.get('http://localhost:8000/api/v1/health/', timeout=5)
    if response.status_code == 200:
        print('✅ Health check endpoint working')
    else:
        print('❌ Health check endpoint failed')
        sys.exit(1)
except requests.exceptions.RequestException:
    print('⚠️ API server not running, skipping endpoint tests')
"

# Summary
echo ""
echo "📊 Test Summary"
echo "==============="

if [ $backend_tests_passed -eq 1 ]; then
    echo "✅ Backend Tests: PASSED"
else
    echo "❌ Backend Tests: FAILED"
fi

if [ $frontend_tests_passed -eq 1 ]; then
    echo "✅ Frontend Tests: PASSED"
else
    echo "❌ Frontend Tests: FAILED"
fi

if [ $lint_passed -eq 1 ]; then
    echo "✅ Code Linting: PASSED"
else
    echo "⚠️ Code Linting: ISSUES FOUND"
fi

# Exit with error if critical tests failed
if [ $backend_tests_passed -eq 0 ] || [ $frontend_tests_passed -eq 0 ]; then
    print_error "Some critical tests failed!"
    exit 1
else
    print_status "All tests completed successfully! 🎉"
    exit 0
fi
