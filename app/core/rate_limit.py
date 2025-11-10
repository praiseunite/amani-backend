"""
Rate limiting middleware for API endpoints.
"""
import time
import logging
from typing import Dict, Tuple
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter implementation.
    Tracks requests per client IP address.
    """
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 100):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
            burst_size: Maximum burst size (tokens in bucket)
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        
        # Storage: {client_id: (tokens, last_refill_time)}
        self.buckets: Dict[str, Tuple[float, float]] = {}
        
        # Track request timestamps for logging
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def _refill_bucket(self, client_id: str, current_time: float) -> float:
        """
        Refill tokens in the bucket based on elapsed time.
        
        Args:
            client_id: Client identifier
            current_time: Current timestamp
            
        Returns:
            Current number of tokens
        """
        if client_id not in self.buckets:
            # Initialize new bucket
            self.buckets[client_id] = (self.burst_size, current_time)
            return self.burst_size
        
        tokens, last_refill = self.buckets[client_id]
        elapsed = current_time - last_refill
        
        # Add tokens based on elapsed time
        new_tokens = min(self.burst_size, tokens + (elapsed * self.refill_rate))
        self.buckets[client_id] = (new_tokens, current_time)
        
        return new_tokens
    
    def allow_request(self, client_id: str) -> Tuple[bool, Dict[str, str]]:
        """
        Check if a request should be allowed.
        
        Args:
            client_id: Client identifier (usually IP address)
            
        Returns:
            Tuple of (allowed, headers) where headers contain rate limit info
        """
        current_time = time.time()
        
        # Refill bucket
        tokens = self._refill_bucket(client_id, current_time)
        
        # Check if request can be allowed
        if tokens >= 1.0:
            # Consume one token
            self.buckets[client_id] = (tokens - 1.0, current_time)
            
            # Track request
            self.request_history[client_id].append(current_time)
            
            # Calculate rate limit headers
            remaining = int(tokens - 1.0)
            reset_time = int(current_time + (self.burst_size - tokens + 1.0) / self.refill_rate)
            
            headers = {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time)
            }
            
            return True, headers
        else:
            # Rate limit exceeded
            retry_after = int((1.0 - tokens) / self.refill_rate)
            headers = {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(retry_after)
            }
            
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            return False, headers
    
    def get_stats(self, client_id: str) -> Dict[str, any]:
        """
        Get rate limiting stats for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with rate limiting statistics
        """
        current_time = time.time()
        tokens = self._refill_bucket(client_id, current_time)
        
        # Count recent requests
        recent_requests = self.request_history.get(client_id, deque())
        last_minute_requests = sum(1 for t in recent_requests if current_time - t <= 60)
        
        return {
            "available_tokens": int(tokens),
            "burst_size": self.burst_size,
            "requests_last_minute": last_minute_requests,
            "requests_per_minute_limit": self.requests_per_minute
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 100,
        exempt_paths: list = None
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size
            exempt_paths: List of paths exempt from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute, burst_size)
        self.exempt_paths = exempt_paths or ["/docs", "/redoc", "/openapi.json", "/api/v1/health"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request through rate limiter.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Skip rate limiting for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_id = request.client.host if request.client else "unknown"
        
        # Check rate limit
        allowed, headers = self.rate_limiter.allow_request(client_id)
        
        if not allowed:
            # Return 429 Too Many Requests
            retry_after = headers.get("Retry-After", "60")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                headers=headers
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value
        
        return response
