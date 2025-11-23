#!/bin/bash
#
# Post-Deployment Verification Script
# Runs health checks and smoke tests after deployment
#
# Usage: ./verify_deployment.sh <environment> <expected_version>
#        ./verify_deployment.sh staging v1.2.3
#        ./verify_deployment.sh production v1.2.3
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-staging}"
EXPECTED_VERSION="${2:-}"
MAX_RETRIES=30
RETRY_DELAY=5

# Set base URL based on environment
case "$ENVIRONMENT" in
    "production"|"prod")
        BASE_URL="${PRODUCTION_URL:-https://api.amani.com}"
        ;;
    "staging"|"stage")
        BASE_URL="${STAGING_URL:-https://staging-api.amani.com}"
        ;;
    "local"|"dev")
        BASE_URL="${LOCAL_URL:-http://localhost:8000}"
        ;;
    *)
        echo -e "${RED}Unknown environment: $ENVIRONMENT${NC}"
        echo "Valid environments: production, staging, local"
        exit 1
        ;;
esac

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Wait for service to be ready
wait_for_service() {
    local url="$1"
    local retry=0
    
    log "Waiting for service to be ready at $url..."
    
    while [ $retry -lt $MAX_RETRIES ]; do
        if curl -sf "$url/api/v1/ping" > /dev/null 2>&1; then
            success "Service is responding"
            return 0
        fi
        
        retry=$((retry + 1))
        log "Service not ready yet (attempt $retry/$MAX_RETRIES)..."
        sleep $RETRY_DELAY
    done
    
    error "Service did not become ready after $MAX_RETRIES attempts"
    return 1
}

# Check health endpoint
check_health() {
    local url="$1"
    
    log "Checking health endpoint..."
    
    local response=$(curl -sf "$url/api/v1/health")
    if [ $? -ne 0 ]; then
        error "Health check failed - endpoint not responding"
        return 1
    fi
    
    # Check if status is healthy
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    if [ "$status" != "healthy" ]; then
        error "Health check failed - status: $status"
        echo "$response" | jq . 2>/dev/null || echo "$response"
        return 1
    fi
    
    success "Health check passed"
    return 0
}

# Verify version
verify_version() {
    local url="$1"
    local expected="$2"
    
    if [ -z "$expected" ]; then
        warning "No expected version specified, skipping version verification"
        return 0
    fi
    
    log "Verifying deployment version..."
    
    local response=$(curl -sf "$url/api/v1/version")
    if [ $? -ne 0 ]; then
        error "Version endpoint not responding"
        return 1
    fi
    
    local version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
    local commit_sha=$(echo "$response" | grep -o '"commit_sha":"[^"]*"' | cut -d'"' -f4)
    
    log "Deployed version: $version"
    log "Commit SHA: $commit_sha"
    
    if [ "$version" != "$expected" ]; then
        error "Version mismatch - Expected: $expected, Got: $version"
        return 1
    fi
    
    success "Version verified: $version"
    return 0
}

# Check readiness
check_readiness() {
    local url="$1"
    
    log "Checking readiness probe..."
    
    local response=$(curl -sf "$url/api/v1/readiness")
    if [ $? -ne 0 ]; then
        error "Readiness check failed - endpoint not responding"
        return 1
    fi
    
    # Check if ready
    local ready=$(echo "$response" | grep -o '"ready":[^,}]*' | cut -d':' -f2 | tr -d ' ')
    if [ "$ready" != "true" ]; then
        error "Readiness check failed - application not ready"
        echo "$response" | jq . 2>/dev/null || echo "$response"
        return 1
    fi
    
    success "Readiness check passed"
    return 0
}

# Run smoke tests
run_smoke_tests() {
    local url="$1"
    
    log "Running smoke tests..."
    
    # Test 1: Root endpoint
    log "Test 1/5: Root endpoint..."
    if curl -sf "$url/" | grep -q "Hello World"; then
        success "Root endpoint test passed"
    else
        error "Root endpoint test failed"
        return 1
    fi
    
    # Test 2: Health check
    log "Test 2/5: Health check..."
    if curl -sf "$url/api/v1/health" | grep -q '"status":"healthy"'; then
        success "Health check test passed"
    else
        error "Health check test failed"
        return 1
    fi
    
    # Test 3: Ping endpoint
    log "Test 3/5: Ping endpoint..."
    if curl -sf "$url/api/v1/ping" | grep -q '"message":"pong"'; then
        success "Ping test passed"
    else
        error "Ping test failed"
        return 1
    fi
    
    # Test 4: Version endpoint
    log "Test 4/5: Version endpoint..."
    if curl -sf "$url/api/v1/version" | grep -q '"version"'; then
        success "Version endpoint test passed"
    else
        error "Version endpoint test failed"
        return 1
    fi
    
    # Test 5: OpenAPI docs (if not production)
    if [ "$ENVIRONMENT" != "production" ] && [ "$ENVIRONMENT" != "prod" ]; then
        log "Test 5/5: OpenAPI docs..."
        if curl -sf "$url/docs" > /dev/null 2>&1; then
            success "OpenAPI docs test passed"
        else
            warning "OpenAPI docs test failed (may be disabled)"
        fi
    else
        log "Test 5/5: Skipped (production environment)"
    fi
    
    success "All smoke tests passed"
    return 0
}

# Check metrics endpoint (if available)
check_metrics() {
    local url="$1"
    
    log "Checking metrics endpoint..."
    
    if curl -sf "$url/metrics" > /dev/null 2>&1; then
        success "Metrics endpoint is accessible"
    else
        warning "Metrics endpoint not accessible (may be restricted)"
    fi
}

# Main verification flow
main() {
    log "=== Post-Deployment Verification ==="
    log "Environment: $ENVIRONMENT"
    log "Base URL: $BASE_URL"
    if [ -n "$EXPECTED_VERSION" ]; then
        log "Expected Version: $EXPECTED_VERSION"
    fi
    echo ""
    
    # Wait for service to be ready
    if ! wait_for_service "$BASE_URL"; then
        error "Service failed to start"
        exit 1
    fi
    echo ""
    
    # Check health
    if ! check_health "$BASE_URL"; then
        error "Health check failed"
        exit 1
    fi
    echo ""
    
    # Verify version
    if ! verify_version "$BASE_URL" "$EXPECTED_VERSION"; then
        error "Version verification failed"
        exit 1
    fi
    echo ""
    
    # Check readiness
    if ! check_readiness "$BASE_URL"; then
        error "Readiness check failed"
        exit 1
    fi
    echo ""
    
    # Run smoke tests
    if ! run_smoke_tests "$BASE_URL"; then
        error "Smoke tests failed"
        exit 1
    fi
    echo ""
    
    # Check metrics (optional)
    check_metrics "$BASE_URL"
    echo ""
    
    # Final summary
    success "=== Deployment Verification Complete ==="
    log "All checks passed successfully!"
    log "Deployment to $ENVIRONMENT is verified and healthy"
    
    # Print summary
    echo ""
    echo "Summary:"
    echo "  Environment: $ENVIRONMENT"
    echo "  URL: $BASE_URL"
    if [ -n "$EXPECTED_VERSION" ]; then
        echo "  Version: $EXPECTED_VERSION"
    fi
    echo "  Status: ✅ Healthy"
}

# Run main function
main
