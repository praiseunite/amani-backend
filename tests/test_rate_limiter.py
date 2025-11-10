"""
Tests for rate limiting middleware.
"""
import pytest
import time
from app.core.rate_limit import RateLimiter


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 100
        assert limiter.refill_rate == 1.0  # 60 requests / 60 seconds
    
    def test_allow_request_first_time(self):
        """Test allowing first request."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        
        allowed, headers = limiter.allow_request("client1")
        
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert headers["X-RateLimit-Limit"] == "60"
        assert "X-RateLimit-Remaining" in headers
    
    def test_allow_multiple_requests(self):
        """Test allowing multiple requests within limit."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        
        client_id = "client2"
        
        # Make 5 requests
        for i in range(5):
            allowed, headers = limiter.allow_request(client_id)
            assert allowed is True
    
    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        client_id = "client3"
        
        # Use up all tokens
        for i in range(5):
            limiter.allow_request(client_id)
        
        # Next request should be denied
        allowed, headers = limiter.allow_request(client_id)
        
        assert allowed is False
        assert "Retry-After" in headers
        assert headers["X-RateLimit-Remaining"] == "0"
    
    def test_token_refill(self):
        """Test token bucket refill over time."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        client_id = "client4"
        
        # Use up all tokens
        for i in range(5):
            limiter.allow_request(client_id)
        
        # Wait for some tokens to refill (1 request per second)
        time.sleep(2)
        
        # Should now be able to make 2 more requests
        allowed, headers = limiter.allow_request(client_id)
        assert allowed is True
    
    def test_get_stats(self):
        """Test getting rate limit stats."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        
        client_id = "client5"
        
        # Make a few requests
        for i in range(3):
            limiter.allow_request(client_id)
        
        # Get stats
        stats = limiter.get_stats(client_id)
        
        assert "available_tokens" in stats
        assert "burst_size" in stats
        assert stats["burst_size"] == 100
        assert stats["requests_per_minute_limit"] == 60
    
    def test_separate_clients(self):
        """Test that different clients have separate limits."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        
        # Client 1 uses all tokens
        for i in range(5):
            limiter.allow_request("client_a")
        
        # Client 2 should still be able to make requests
        allowed, headers = limiter.allow_request("client_b")
        assert allowed is True
