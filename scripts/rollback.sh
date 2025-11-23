#!/bin/bash
#
# Rollback Script for Amani Backend
# Automates rollback to a previous deployment version
#
# Usage: ./rollback.sh [target_version] [--auto-confirm]
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_HISTORY_FILE="${PROJECT_ROOT}/.deployment-history"
ROLLBACK_LOG_FILE="${PROJECT_ROOT}/logs/rollback-$(date +%Y%m%d-%H%M%S).log"

# Parse arguments
TARGET_VERSION="${1:-}"
AUTO_CONFIRM="${2:-}"

# Functions
log() {
    local message="$1"
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $message" | tee -a "$ROLLBACK_LOG_FILE"
}

error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} $message" | tee -a "$ROLLBACK_LOG_FILE"
}

success() {
    local message="$1"
    echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$ROLLBACK_LOG_FILE"
}

warning() {
    local message="$1"
    echo -e "${YELLOW}[WARNING]${NC} $message" | tee -a "$ROLLBACK_LOG_FILE"
}

show_usage() {
    echo "Usage: $0 [target_version] [--auto-confirm]"
    echo ""
    echo "Arguments:"
    echo "  target_version    Version to rollback to (e.g., v1.2.3, staging-abc123)"
    echo "  --auto-confirm    Skip confirmation prompts"
    echo ""
    echo "Examples:"
    echo "  $0 v1.2.3                  # Interactive rollback to v1.2.3"
    echo "  $0 v1.2.3 --auto-confirm   # Automated rollback to v1.2.3"
    echo "  $0                         # Show deployment history and exit"
    exit 1
}

get_current_version() {
    # Try to get current version from deployed application
    local health_url="${HEALTH_CHECK_URL:-http://localhost:8000/api/v1/version}"
    
    if command -v curl &> /dev/null; then
        local version=$(curl -sf "$health_url" | grep -o '"version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "unknown")
        echo "$version"
    else
        echo "unknown"
    fi
}

show_deployment_history() {
    if [ ! -f "$DEPLOYMENT_HISTORY_FILE" ]; then
        warning "No deployment history found"
        return
    fi
    
    echo ""
    log "Recent Deployment History:"
    echo "----------------------------------------"
    tail -n 10 "$DEPLOYMENT_HISTORY_FILE" | tac
    echo "----------------------------------------"
    echo ""
}

create_pre_rollback_backup() {
    log "Creating pre-rollback backup..."
    
    # Create database backup before rollback
    if [ -f "$SCRIPT_DIR/backup_database.sh" ]; then
        bash "$SCRIPT_DIR/backup_database.sh" "${PROJECT_ROOT}/backups/pre-rollback" || {
            error "Failed to create pre-rollback backup"
            return 1
        }
        success "Pre-rollback backup created"
    else
        warning "Backup script not found, skipping backup"
    fi
}

perform_rollback() {
    local target_version="$1"
    
    log "Starting rollback to version: $target_version"
    
    # Check deployment method and perform appropriate rollback
    if command -v docker &> /dev/null && docker ps | grep -q amani-backend; then
        rollback_docker "$target_version"
    elif command -v kubectl &> /dev/null; then
        rollback_kubernetes "$target_version"
    elif command -v flyctl &> /dev/null; then
        rollback_flyio "$target_version"
    else
        error "No supported deployment method detected"
        return 1
    fi
}

rollback_docker() {
    local target_version="$1"
    
    log "Performing Docker rollback..."
    
    # Stop current container
    log "Stopping current container..."
    docker stop amani-backend || true
    docker rm amani-backend || true
    
    # Pull target version
    log "Pulling image: amani-backend:$target_version"
    docker pull "amani-backend:$target_version" || {
        error "Failed to pull image"
        return 1
    }
    
    # Start with target version
    log "Starting container with version $target_version..."
    docker run -d \
        --name amani-backend \
        -p 8000:8000 \
        --env-file .env \
        --restart unless-stopped \
        "amani-backend:$target_version" || {
        error "Failed to start container"
        return 1
    }
    
    success "Docker rollback completed"
}

rollback_kubernetes() {
    local target_version="$1"
    
    log "Performing Kubernetes rollback..."
    
    # Get deployment name
    local deployment_name="amani-backend"
    
    # Rollback using kubectl
    kubectl rollout undo deployment/"$deployment_name" || {
        error "Failed to rollback Kubernetes deployment"
        return 1
    }
    
    # Wait for rollout to complete
    kubectl rollout status deployment/"$deployment_name" --timeout=5m || {
        error "Rollback rollout failed"
        return 1
    }
    
    success "Kubernetes rollback completed"
}

rollback_flyio() {
    local target_version="$1"
    
    log "Performing Fly.io rollback..."
    
    # List releases and rollback
    flyctl releases list
    
    # Rollback to previous version
    flyctl releases rollback --yes || {
        error "Failed to rollback Fly.io deployment"
        return 1
    }
    
    success "Fly.io rollback completed"
}

verify_rollback() {
    local target_version="$1"
    
    log "Verifying rollback..."
    
    # Wait for application to be ready
    local max_attempts=30
    local attempt=0
    local health_url="${HEALTH_CHECK_URL:-http://localhost:8000/api/v1/health}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$health_url" > /dev/null 2>&1; then
            success "Application is responding"
            break
        fi
        
        attempt=$((attempt + 1))
        log "Waiting for application to be ready (attempt $attempt/$max_attempts)..."
        sleep 5
    done
    
    if [ $attempt -eq $max_attempts ]; then
        error "Application did not become ready after rollback"
        return 1
    fi
    
    # Verify version
    local current_version=$(get_current_version)
    log "Current running version: $current_version"
    
    # Run smoke tests
    log "Running smoke tests..."
    if curl -sf "$health_url" | grep -q '"status":"healthy"'; then
        success "Health check passed"
    else
        error "Health check failed"
        return 1
    fi
    
    success "Rollback verification completed"
}

record_rollback() {
    local target_version="$1"
    local timestamp=$(date -u +'%Y-%m-%d %H:%M:%S UTC')
    
    mkdir -p "$(dirname "$DEPLOYMENT_HISTORY_FILE")"
    echo "$timestamp - ROLLBACK to $target_version by $(whoami)" >> "$DEPLOYMENT_HISTORY_FILE"
}

# Main execution
main() {
    log "=== Amani Backend Rollback Script ==="
    log "Log file: $ROLLBACK_LOG_FILE"
    
    # Create logs directory
    mkdir -p "${PROJECT_ROOT}/logs"
    
    # Show deployment history if no version specified
    if [ -z "$TARGET_VERSION" ]; then
        show_deployment_history
        show_usage
    fi
    
    # Get current version
    local current_version=$(get_current_version)
    log "Current version: $current_version"
    log "Target version: $TARGET_VERSION"
    
    # Confirm rollback unless auto-confirm is set
    if [ "$AUTO_CONFIRM" != "--auto-confirm" ]; then
        echo ""
        warning "This will rollback from $current_version to $TARGET_VERSION"
        read -p "Are you sure you want to proceed? (yes/no): " confirmation
        
        if [ "$confirmation" != "yes" ]; then
            log "Rollback cancelled by user"
            exit 0
        fi
    fi
    
    # Show deployment history
    show_deployment_history
    
    # Create pre-rollback backup
    create_pre_rollback_backup || {
        error "Failed to create backup"
        exit 1
    }
    
    # Perform rollback
    perform_rollback "$TARGET_VERSION" || {
        error "Rollback failed"
        exit 1
    }
    
    # Verify rollback
    verify_rollback "$TARGET_VERSION" || {
        error "Rollback verification failed"
        warning "You may need to investigate and potentially rollback manually"
        exit 1
    }
    
    # Record rollback
    record_rollback "$TARGET_VERSION"
    
    success "=== Rollback completed successfully ==="
    log "Rolled back from $current_version to $TARGET_VERSION"
    log "Rollback log: $ROLLBACK_LOG_FILE"
}

# Run main function
main
