#!/bin/bash
# filepath: /home/teo/Project/school/schoolplatform/scripts/dev-setup.sh

# Development Setup Script for TeoArt School Platform
# This script sets up the development environment

echo "🎨 TeoArt School Platform - Development Setup"
echo "============================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi
echo "✅ Python version: $python_version"

# Check if Node.js 16+ is installed
if command -v node &> /dev/null; then
    node_version=$(node --version | grep -Po '(?<=v)\d+')
    if [[ $node_version -lt 16 ]]; then
        echo "❌ Node.js 16+ is required. Current version: $(node --version)"
        exit 1
    fi
    echo "✅ Node.js version: $(node --version)"
else
    echo "❌ Node.js is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install frontend dependencies
echo "🎭 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Set up database
echo "🗄️ Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@teoart.com', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

# Set up test data
echo "🧪 Setting up test data..."
python setup_user_data.py

# Build frontend for development
echo "🏗️ Building frontend..."
cd frontend
npm run build
cd ..

echo ""
echo "🎉 Development setup complete!"
echo ""
echo "To start the development servers:"
echo "  Backend:  python manage.py runserver"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Happy coding! 🚀"
