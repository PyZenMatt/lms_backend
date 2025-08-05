#!/bin/bash

# Production Deployment Script for SchoolPlatform
# ===============================================

set -e  # Exit on any error

echo "🚀 Starting SchoolPlatform production deployment..."

# Configuration
PROJECT_DIR="/var/www/schoolplatform"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="/var/backups/schoolplatform"
LOG_DIR="/var/log/schoolplatform"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    error "Please run this script as root or with sudo"
fi

# Create necessary directories
log "Creating directories..."
mkdir -p $PROJECT_DIR
mkdir -p $BACKUP_DIR
mkdir -p $LOG_DIR
mkdir -p /var/www/schoolplatform/static
mkdir -p /var/www/schoolplatform/media

# Create log files with proper permissions
touch $LOG_DIR/django.log
touch $LOG_DIR/performance.log
touch $LOG_DIR/errors.log
chown -R www-data:www-data $LOG_DIR
chmod 644 $LOG_DIR/*.log

# Install system dependencies
log "Installing system dependencies..."
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor \
    git \
    curl \
    nodejs \
    npm

# Install Python dependencies
log "Setting up Python virtual environment..."
cd $PROJECT_DIR
python3 -m venv $VENV_DIR
source $VENV_DIR/bin/activate

# Install Python packages
pip install --upgrade pip
pip install \
    django \
    djangorestframework \
    djangorestframework-simplejwt \
    django-cors-headers \
    django-debug-toolbar \
    django-redis \
    celery \
    sentry-sdk \
    psycopg2-binary \
    gunicorn \
    python-dotenv \
    Pillow

# PostgreSQL setup
log "Setting up PostgreSQL..."
sudo -u postgres createdb schoolplatform_prod 2>/dev/null || warning "Database already exists"
sudo -u postgres psql -c "CREATE USER schoolplatform WITH PASSWORD 'changeme123';" 2>/dev/null || warning "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE schoolplatform_prod TO schoolplatform;" 2>/dev/null || warning "Privileges already granted"

# Redis setup
log "Starting Redis..."
systemctl enable redis-server
systemctl start redis-server

# Copy application files (assuming they're in current directory)
if [ -d "./schoolplatform" ]; then
    log "Copying application files..."
    cp -r ./schoolplatform/* $PROJECT_DIR/
    chown -R www-data:www-data $PROJECT_DIR
fi

# Django setup
log "Running Django migrations..."
cd $PROJECT_DIR
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=schoolplatform.settings_production

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    log "Creating .env file from template..."
    cp .env.production.template .env
    warning "Please edit .env file with your production values!"
fi

python manage.py migrate
python manage.py collectstatic --noinput

# Create superuser (interactive)
log "Creating Django superuser..."
python manage.py createsuperuser || warning "Superuser creation skipped"

# Gunicorn configuration
log "Setting up Gunicorn..."
cat > /etc/systemd/system/schoolplatform.service << EOF
[Unit]
Description=SchoolPlatform Django Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/schoolplatform.sock schoolplatform.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Celery configuration
log "Setting up Celery..."
cat > /etc/systemd/system/schoolplatform-celery.service << EOF
[Unit]
Description=SchoolPlatform Celery Worker
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/celery -A schoolplatform worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat configuration
cat > /etc/systemd/system/schoolplatform-celerybeat.service << EOF
[Unit]
Description=SchoolPlatform Celery Beat
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
EnvironmentFile=$PROJECT_DIR/.env
ExecStart=$VENV_DIR/bin/celery -A schoolplatform beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Nginx configuration
log "Setting up Nginx..."
cat > /etc/nginx/sites-available/schoolplatform << EOF
server {
    listen 80;
    server_name yourdomainhere.com www.yourdomainhere.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/schoolplatform;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        root /var/www/schoolplatform;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/schoolplatform.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/schoolplatform /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t || error "Nginx configuration test failed"

# Start services
log "Starting services..."
systemctl daemon-reload
systemctl enable schoolplatform
systemctl enable schoolplatform-celery
systemctl enable schoolplatform-celerybeat
systemctl enable nginx

systemctl start schoolplatform
systemctl start schoolplatform-celery
systemctl start schoolplatform-celerybeat
systemctl restart nginx

# Create backup script
log "Creating backup script..."
cat > /usr/local/bin/backup-schoolplatform << EOF
#!/bin/bash
BACKUP_DIR="/var/backups/schoolplatform"
TIMESTAMP=\$(date +"%Y%m%d_%H%M%S")

# Create backup directory
mkdir -p \$BACKUP_DIR

# Backup database
sudo -u postgres pg_dump schoolplatform_prod > \$BACKUP_DIR/db_backup_\$TIMESTAMP.sql

# Backup media files
tar -czf \$BACKUP_DIR/media_backup_\$TIMESTAMP.tar.gz -C /var/www/schoolplatform media/

# Backup application code
tar -czf \$BACKUP_DIR/code_backup_\$TIMESTAMP.tar.gz -C /var/www schoolplatform/ --exclude='*.pyc' --exclude='__pycache__'

# Keep only last 7 days of backups
find \$BACKUP_DIR -type f -mtime +7 -delete

echo "Backup completed: \$TIMESTAMP"
EOF

chmod +x /usr/local/bin/backup-schoolplatform

# Add cron job for daily backups
log "Setting up daily backups..."
echo "0 2 * * * root /usr/local/bin/backup-schoolplatform" > /etc/cron.d/schoolplatform-backup

# Frontend build
if [ -d "./frontend" ]; then
    log "Building frontend..."
    cd $PROJECT_DIR/frontend
    npm install
    npm run build
    
    # Copy built files to static directory
    cp -r dist/* /var/www/schoolplatform/static/
fi

# Set proper permissions
log "Setting permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod -R 755 $PROJECT_DIR
chmod -R 644 $PROJECT_DIR/static
chmod -R 644 $PROJECT_DIR/media

# Final checks
log "Performing final checks..."
systemctl is-active --quiet schoolplatform || error "SchoolPlatform service is not running"
systemctl is-active --quiet schoolplatform-celery || error "Celery service is not running"
systemctl is-active --quiet nginx || error "Nginx is not running"
systemctl is-active --quiet redis-server || error "Redis is not running"

log "✅ Production deployment completed successfully!"
echo ""
echo "🔧 Next steps:"
echo "1. Edit $PROJECT_DIR/.env with your production settings"
echo "2. Update the domain name in /etc/nginx/sites-available/schoolplatform"
echo "3. Set up SSL certificate (Let's Encrypt recommended)"
echo "4. Configure monitoring (Sentry, New Relic, etc.)"
echo "5. Test the application at http://yourdomainhere.com"
echo ""
echo "📊 Service status:"
systemctl status schoolplatform --no-pager -l
echo ""
echo "📁 Important paths:"
echo "  - Application: $PROJECT_DIR"
echo "  - Logs: $LOG_DIR"
echo "  - Backups: $BACKUP_DIR"
echo "  - Static files: /var/www/schoolplatform/static"
echo ""
echo "🔧 Useful commands:"
echo "  - Restart app: sudo systemctl restart schoolplatform"
echo "  - View logs: sudo journalctl -u schoolplatform -f"
echo "  - Manual backup: sudo /usr/local/bin/backup-schoolplatform"
