"""
Rate limiting middleware for API endpoints.
Supports both in-memory and Redis-based rate limiting.
"""
import time
import logging
from typing import Dict, Tuple, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Using in-memory rate limiting.")


class RedisRateLimiter:
    """
    Redis-based rate limiter using token bucket algorithm.
    Supports distributed rate limiting across multiple application instances.
    """
    
    def __init__(self, redis_client: 'Redis', requests_per_minute: int = 60, burst_size: int = 100):
        """
        Initialize Redis rate limiter.
        
        Args:
            redis_client: Redis client instance
            requests_per_minute: Maximum requests allowed per minute
            burst_size: Maximum burst size (tokens in bucket)
        """
        self.redis_client = redis_client
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
    
    def _get_bucket_key(self, client_id: str) -> str:
        """Generate Redis key for rate limit bucket."""
        return f"rate_limit:{client_id}"
    
    def _get_history_key(self, client_id: str) -> str:
        """Generate Redis key for request history."""
        return f"rate_limit:history:{client_id}"
    
    def _refill_bucket(self, client_id: str, current_time: float) -> float:
        """
        Refill tokens in the bucket based on elapsed time.
        
        Args:
            client_id: Client identifier
            current_time: Current timestamp
            
        Returns:
            Current number of tokens
        """
        bucket_key = self._get_bucket_key(client_id)
        
        # Get bucket data from Redis
        bucket_data = self.redis_client.get(bucket_key)
        
        if bucket_data is None:
            # Initialize new bucket
            tokens = self.burst_size
            self.redis_client.setex(
                bucket_key,
                3600,  # Expire after 1 hour of inactivity
                f"{tokens},{current_time}"
            )
            return tokens
        
        # Parse bucket data
        parts = bucket_data.decode('utf-8').split(',')
        tokens = float(parts[0])
        last_refill = float(parts[1])
        
        # Calculate elapsed time and refill tokens
        elapsed = current_time - last_refill
        new_tokens = min(self.burst_size, tokens + (elapsed * self.refill_rate))
        
        # Update bucket in Redis
        self.redis_client.setex(
            bucket_key,
            3600,
            f"{new_tokens},{current_time}"
        )
        
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
        bucket_key = self._get_bucket_key(client_id)
        history_key = self._get_history_key(client_id)
        
        try:
            # Refill bucket
            tokens = self._refill_bucket(client_id, current_time)
            
            # Check if request can be allowed
            if tokens >= 1.0:
                # Consume one token
                new_tokens = tokens - 1.0
                self.redis_client.setex(
                    bucket_key,
                    3600,
                    f"{new_tokens},{current_time}"
                )
                
                # Track request in history (last 100 requests)
                self.redis_client.lpush(history_key, str(current_time))
                self.redis_client.ltrim(history_key, 0, 99)
                self.redis_client.expire(history_key, 3600)
                
                # Calculate rate limit headers
                remaining = int(new_tokens)
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
        
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}. Allowing request.")
            # On error, allow request with default headers
            return True, {
                "X-RateLimit-Limit": str(self.requests_per_minute),
                "X-RateLimit-Remaining": str(self.burst_size)
            }
    
    def get_stats(self, client_id: str) -> Dict[str, any]:
        """
        Get rate limiting stats for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dictionary with rate limiting statistics
        """
        current_time = time.time()
        bucket_key = self._get_bucket_key(client_id)
        history_key = self._get_history_key(client_id)
        
        try:
            tokens = self._refill_bucket(client_id, current_time)
            
            # Count recent requests
            history = self.redis_client.lrange(history_key, 0, -1)
            last_minute_requests = sum(
                1 for t in history 
                if current_time - float(t.decode('utf-8')) <= 60
            )
            
            return {
                "available_tokens": int(tokens),
                "burst_size": self.burst_size,
                "requests_last_minute": last_minute_requests,
                "requests_per_minute_limit": self.requests_per_minute
            }
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {
                "available_tokens": self.burst_size,
                "burst_size": self.burst_size,
                "requests_last_minute": 0,
                "requests_per_minute_limit": self.requests_per_minute
            }


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
    Supports both in-memory and Redis-based rate limiting.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 100,
        exempt_paths: list = None,
        redis_url: Optional[str] = None
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size
            exempt_paths: List of paths exempt from rate limiting
            redis_url: Redis connection URL (if None, uses in-memory rate limiting)
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or ["/docs", "/redoc", "/openapi.json", "/api/v1/health"]
        
        # Initialize rate limiter (Redis or in-memory)
        if redis_url and REDIS_AVAILABLE:
            try:
                redis_client = redis.from_url(redis_url, decode_responses=False)
                # Test connection
                redis_client.ping()
                self.rate_limiter = RedisRateLimiter(redis_client, requests_per_minute, burst_size)
                logger.info("Using Redis-based rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to in-memory rate limiting.")
                self.rate_limiter = RateLimiter(requests_per_minute, burst_size)
        else:
            self.rate_limiter = RateLimiter(requests_per_minute, burst_size)
            if not redis_url:
                logger.info("Using in-memory rate limiting (Redis URL not provided)")
            elif not REDIS_AVAILABLE:
                logger.warning("Redis library not available. Using in-memory rate limiting.")
    
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
