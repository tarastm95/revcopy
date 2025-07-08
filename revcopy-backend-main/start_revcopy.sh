#!/bin/bash

# RevCopy Startup Script
# This script starts the complete RevCopy system with all services

set -e

echo "🚀 Starting RevCopy System..."
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    print_error "docker-compose.yml not found. Please run this script from the backend directory."
    exit 1
fi

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    print_warning ".env file not found. Creating a default one..."
    cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql+asyncpg://revcopy_user:revcopy_password@localhost:5432/revcopy_db
POSTGRES_SERVER=localhost
POSTGRES_USER=revcopy_user
POSTGRES_PASSWORD=revcopy_password
POSTGRES_DB=revcopy_db

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET=your-jwt-secret-change-in-production

# AI Configuration
DEEPSEEK_API_KEY=your-deepseek-api-key
DEFAULT_AI_PROVIDER=deepseek

# Amazon Crawler Integration
AMAZON_CRAWLER_URL=http://localhost:8080
AMAZON_CRAWLER_TIMEOUT=30
AMAZON_CRAWLER_USERNAME=crawler
AMAZON_CRAWLER_PASSWORD=crawler123

# Environment
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175
EOF
    print_status ".env file created with default values. Please update it with your actual credentials."
fi

# Parse command line arguments
START_MODE="docker"
BACKGROUND=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --manual)
            START_MODE="manual"
            shift
            ;;
        --background|-d)
            BACKGROUND=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --manual     Start services manually (not recommended for first-time users)"
            echo "  --background Start services in background"
            echo "  --help       Show this help message"
            echo ""
            echo "Services started:"
            echo "  - PostgreSQL Database (port 5432)"
            echo "  - Redis Cache (port 6379)"
            echo "  - Amazon Crawler Service (port 8080)"
            echo "  - RevCopy Backend API (port 8000)"
            echo "  - Background Workers"
            echo ""
            echo "Optional tools (with --profile tools):"
            echo "  - pgAdmin (port 8082)"
            echo "  - Redis Commander (port 8081)"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

if [[ "$START_MODE" == "docker" ]]; then
    print_header "🐳 Starting with Docker Compose..."
    
    # Stop any existing containers
    print_status "Stopping existing containers..."
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # Build and start services
    print_status "Building and starting services..."
    if [[ "$BACKGROUND" == true ]]; then
        docker-compose up --build -d
    else
        docker-compose up --build
    fi
    
    if [[ "$BACKGROUND" == true ]]; then
        print_status "Services started in background mode"
        print_status "Check logs with: docker-compose logs -f"
        print_status "Stop services with: docker-compose down"
        
        # Wait a bit for services to start
        sleep 10
        
        # Check service health
        print_header "🔍 Checking service health..."
        
        services=("postgres" "redis" "amazon-crawler" "api")
        for service in "${services[@]}"; do
            if docker-compose ps -q "$service" > /dev/null; then
                status=$(docker-compose ps "$service" --format "table {{.State}}" | tail -n1)
                if [[ "$status" == *"Up"* ]]; then
                    print_status "$service: ✅ Running"
                else
                    print_warning "$service: ⚠️  $status"
                fi
            else
                print_error "$service: ❌ Not found"
            fi
        done
        
        print_header "🌐 Service URLs:"
        echo "  • Backend API: http://localhost:8000"
        echo "  • Amazon Crawler: http://localhost:8080"
        echo "  • API Documentation: http://localhost:8000/docs"
        echo "  • Amazon Crawler Docs: http://localhost:8080/docs"
        echo ""
        echo "Optional tools (start with: docker-compose --profile tools up -d):"
        echo "  • pgAdmin: http://localhost:8082 (admin@revcopy.com / admin123)"
        echo "  • Redis Commander: http://localhost:8081"
        
        print_header "🚀 Next Steps:"
        echo "1. Start the frontend: cd ../frontend && npm run dev"
        echo "2. Open http://localhost:5173 in your browser"
        echo "3. Try analyzing an Amazon product URL"
    fi
    
elif [[ "$START_MODE" == "manual" ]]; then
    print_header "⚙️  Manual startup mode (Advanced users only)"
    print_warning "This mode requires you to have PostgreSQL, Redis, and Go installed locally"
    
    echo ""
    echo "Please start services in this order:"
    echo ""
    echo "1. PostgreSQL Database:"
    echo "   sudo service postgresql start"
    echo "   # or: brew services start postgresql"
    echo ""
    echo "2. Redis Cache:"
    echo "   sudo service redis start"
    echo "   # or: brew services start redis"
    echo ""
    echo "3. Amazon Crawler Service:"
    echo "   cd ../crawlers/amazon"
    echo "   make run"
    echo "   # or: go run main.go"
    echo ""
    echo "4. RevCopy Backend (in new terminal):"
    echo "   cd backend"
    echo "   python run.py"
    echo ""
    echo "5. Frontend (in new terminal):"
    echo "   cd frontend"
    echo "   npm run dev"
    echo ""
fi

print_status "RevCopy startup script completed!" 