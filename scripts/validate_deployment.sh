#!/bin/bash

# Production Deployment Validation Script
# Validates all performance optimizations are working correctly

echo "🚀 School Platform - Production Deployment Validation"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if service is running
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}✅ $1 is running${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 is not running${NC}"
        return 1
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url=$1
    local expected_status=$2
    local timeout=${3:-10}
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $timeout "$url")
    
    if [ "$response" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ $url responds with $response${NC}"
        return 0
    else
        echo -e "${RED}❌ $url responds with $response (expected $expected_status)${NC}"
        return 1
    fi
}

# Function to check Redis
check_redis() {
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is responding${NC}"
        return 0
    else
        echo -e "${RED}❌ Redis is not responding${NC}"
        return 1
    fi
}

# Function to check PostgreSQL
check_postgres() {
    if pg_isready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
        return 0
    else
        echo -e "${RED}❌ PostgreSQL is not ready${NC}"
        return 1
    fi
}

echo
echo "🔍 Checking Core Services..."
echo "----------------------------"

# Check services
check_service postgresql
check_service redis-server
check_service nginx

echo
echo "🔗 Checking Database Connections..."
echo "-----------------------------------"

check_redis
check_postgres

echo
echo "🌐 Checking HTTP Endpoints..."
echo "-----------------------------"

# Define base URL (change to your domain)
BASE_URL="${BASE_URL:-http://localhost}"

# Check main endpoints
check_endpoint "$BASE_URL/api/v1/core/health/" 200
check_endpoint "$BASE_URL/static/admin/css/base.css" 200
check_endpoint "$BASE_URL/" 200

echo
echo "⚡ Running Performance Tests..."
echo "------------------------------"

# Run Django performance tests
cd "$(dirname "$0")"
if [ -f "test_performance.py" ]; then
    python test_performance.py
else
    echo -e "${YELLOW}⚠️  Performance test script not found${NC}"
fi

echo
echo "📊 Checking Cache Performance..."
echo "-------------------------------"

# Test cache hit rate
if command -v redis-cli &> /dev/null; then
    redis_info=$(redis-cli info stats 2>/dev/null)
    if [ $? -eq 0 ]; then
        hits=$(echo "$redis_info" | grep "keyspace_hits" | cut -d: -f2 | tr -d '\r')
        misses=$(echo "$redis_info" | grep "keyspace_misses" | cut -d: -f2 | tr -d '\r')
        
        if [ -n "$hits" ] && [ -n "$misses" ] && [ "$hits" -gt 0 ]; then
            total=$((hits + misses))
            hit_rate=$((hits * 100 / total))
            echo -e "${GREEN}✅ Cache hit rate: ${hit_rate}%${NC}"
        else
            echo -e "${YELLOW}⚠️  No cache statistics available yet${NC}"
        fi
    fi
fi

echo
echo "🐳 Checking Docker Status..."
echo "---------------------------"

if command -v docker &> /dev/null; then
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "Up"; then
        echo -e "${GREEN}✅ Docker containers are running:${NC}"
        docker ps --format "table {{.Names}}\t{{.Status}}" | grep "Up"
    else
        echo -e "${YELLOW}⚠️  No Docker containers running${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not installed${NC}"
fi

echo
echo "📁 Checking File Permissions..."
echo "------------------------------"

# Check critical file permissions
if [ -d "logs" ]; then
    echo -e "${GREEN}✅ Logs directory exists${NC}"
    if [ -w "logs" ]; then
        echo -e "${GREEN}✅ Logs directory is writable${NC}"
    else
        echo -e "${RED}❌ Logs directory is not writable${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Logs directory not found${NC}"
fi

if [ -d "media" ]; then
    echo -e "${GREEN}✅ Media directory exists${NC}"
else
    echo -e "${YELLOW}⚠️  Media directory not found${NC}"
fi

echo
echo "🔒 Checking Security Configuration..."
echo "-----------------------------------"

# Check if DEBUG is disabled in production
if python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schoolplatform.settings_production'); from django.conf import settings; exit(0 if not settings.DEBUG else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ DEBUG is disabled in production${NC}"
else
    echo -e "${RED}❌ DEBUG is enabled (security risk!)${NC}"
fi

# Check SSL certificate (if HTTPS)
if [ "$BASE_URL" != "${BASE_URL#https://}" ]; then
    domain=$(echo "$BASE_URL" | sed 's|https://||' | sed 's|/.*||')
    if openssl s_client -connect "$domain:443" -servername "$domain" </dev/null 2>/dev/null | openssl x509 -noout -dates &>/dev/null; then
        echo -e "${GREEN}✅ SSL certificate is valid${NC}"
    else
        echo -e "${RED}❌ SSL certificate issue${NC}"
    fi
fi

echo
echo "📊 Summary"
echo "=========="

# Count successful checks
echo "Validation complete! Check the output above for any issues."
echo
echo "🔧 If any checks failed:"
echo "  1. Check service logs: journalctl -u <service-name>"
echo "  2. Verify configuration files"
echo "  3. Check firewall and network settings"
echo "  4. Review error logs in ./logs/ directory"
echo
echo "📚 For detailed troubleshooting, see:"
echo "  - OPTIMIZATION_COMPLETE_SUMMARY.md"
echo "  - PERFORMANCE_OPTIMIZATION_GUIDE.md"
