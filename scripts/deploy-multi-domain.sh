#!/bin/bash

# Multi-Domain Dashboard Deployment Script
# This script helps deploy the multi-domain dashboard with proper configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_DIR/.env"
DOMAINS_CONFIG="$PROJECT_DIR/backend/domains.json"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating .env file from template..."
        cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
        log_warning "Please edit .env file with your specific configuration"
    else
        log_info ".env file already exists"
    fi
}

validate_domains_config() {
    log_info "Validating domains configuration..."
    
    if [ ! -f "$DOMAINS_CONFIG" ]; then
        log_error "Domains configuration file not found: $DOMAINS_CONFIG"
        exit 1
    fi
    
    # Basic JSON validation
    if ! python3 -m json.tool "$DOMAINS_CONFIG" > /dev/null 2>&1; then
        log_error "Invalid JSON in domains configuration file"
        exit 1
    fi
    
    # Check if domains are configured
    domain_count=$(python3 -c "
import json
with open('$DOMAINS_CONFIG', 'r') as f:
    config = json.load(f)
print(len(config.get('domains', {})))
" 2>/dev/null || echo "0")
    
    if [ "$domain_count" -eq 0 ]; then
        log_warning "No domains configured in domains.json"
    else
        log_success "$domain_count domains configured"
    fi
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$PROJECT_DIR/data"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/ssl"
    
    log_success "Directories created"
}

deploy_services() {
    local mode="$1"
    
    log_info "Deploying services in $mode mode..."
    
    cd "$PROJECT_DIR"
    
    case "$mode" in
        "dev")
            docker-compose -f docker-compose.dev.yml down
            docker-compose -f docker-compose.dev.yml up -d --build
            ;;
        "prod")
            docker-compose -f docker-compose.prod.yml down
            docker-compose -f docker-compose.prod.yml up -d --build
            ;;
        "simple")
            docker-compose down
            docker-compose up -d --build
            ;;
        *)
            log_error "Invalid deployment mode: $mode"
            exit 1
            ;;
    esac
    
    log_success "Services deployed successfully"
}

wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "healthy"; then
            log_success "Services are healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting for services..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Services failed to become healthy within timeout"
    return 1
}

run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    # Check basic connectivity
    if curl -f http://localhost:5001/api/health > /dev/null 2>&1; then
        log_success "Basic health check passed"
    else
        log_error "Basic health check failed"
        return 1
    fi
    
    # Check domains health
    if curl -f http://localhost:5001/api/admin/domains/health > /dev/null 2>&1; then
        log_success "Domains health check passed"
    else
        log_error "Domains health check failed"
        return 1
    fi
    
    log_success "All health checks passed"
}

show_status() {
    log_info "Current deployment status:"
    echo
    docker-compose ps
    echo
    
    log_info "Service URLs:"
    echo "  Backend API: http://localhost:5001"
    echo "  Frontend: http://localhost:3000"
    echo "  Health Check: http://localhost:5001/api/health"
    echo "  Domains Health: http://localhost:5001/api/admin/domains/health"
    echo
    
    log_info "Logs:"
    echo "  View all logs: docker-compose logs -f"
    echo "  Backend logs: docker-compose logs -f backend"
    echo "  Frontend logs: docker-compose logs -f frontend"
}

show_help() {
    echo "Multi-Domain Dashboard Deployment Script"
    echo
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo
    echo "Commands:"
    echo "  deploy [dev|prod|simple]  Deploy the application"
    echo "  status                    Show current deployment status"
    echo "  health                    Run health checks"
    echo "  logs [service]            Show logs for all services or specific service"
    echo "  stop                      Stop all services"
    echo "  restart [dev|prod|simple] Restart services"
    echo "  help                      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 deploy dev             Deploy in development mode"
    echo "  $0 deploy prod            Deploy in production mode"
    echo "  $0 status                 Show current status"
    echo "  $0 logs backend           Show backend logs"
}

# Main script logic
case "${1:-help}" in
    "deploy")
        mode="${2:-simple}"
        check_prerequisites
        setup_environment
        validate_domains_config
        create_directories
        deploy_services "$mode"
        wait_for_services
        run_health_checks
        show_status
        ;;
    "status")
        show_status
        ;;
    "health")
        run_health_checks
        ;;
    "logs")
        service="${2:-}"
        if [ -n "$service" ]; then
            docker-compose logs -f "$service"
        else
            docker-compose logs -f
        fi
        ;;
    "stop")
        log_info "Stopping all services..."
        docker-compose down
        log_success "Services stopped"
        ;;
    "restart")
        mode="${2:-simple}"
        log_info "Restarting services..."
        docker-compose down
        deploy_services "$mode"
        wait_for_services
        run_health_checks
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac