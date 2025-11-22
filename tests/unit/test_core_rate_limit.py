"""
Comprehensive unit tests for app.core.rate_limit module.
Tests in-memory rate limiter using token bucket algorithm.
"""

import pytest
import time
from app.core.rate_limit import RateLimiter


class TestRateLimiter:
    """Test suite for RateLimiter class."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 100
        assert limiter.refill_rate == 1.0  # 60 / 60 = 1 token per second

    def test_rate_limiter_default_values(self):
        """Test rate limiter with default values."""
        limiter = RateLimiter()
        
        assert limiter.requests_per_minute == 60
        assert limiter.burst_size == 100

    def test_allow_request_first_request(self):
        """Test allowing first request."""
        limiter = RateLimiter()
        client_id = "192.168.1.1"
        
        allowed, headers = limiter.allow_request(client_id)
        
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers

    def test_allow_request_headers_format(self):
        """Test rate limit headers format."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        client_id = "192.168.1.1"
        
        allowed, headers = limiter.allow_request(client_id)
        
        assert headers["X-RateLimit-Limit"] == "60"
        assert int(headers["X-RateLimit-Remaining"]) >= 0
        assert int(headers["X-RateLimit-Reset"]) > 0

    def test_allow_request_consumes_token(self):
        """Test that request consumes a token."""
        limiter = RateLimiter(burst_size=10)
        client_id = "192.168.1.1"
        
        # First request
        allowed1, headers1 = limiter.allow_request(client_id)
        remaining1 = int(headers1["X-RateLimit-Remaining"])
        
        # Second request
        allowed2, headers2 = limiter.allow_request(client_id)
        remaining2 = int(headers2["X-RateLimit-Remaining"])
        
        assert allowed1 is True
        assert allowed2 is True
        assert remaining2 == remaining1 - 1

    def test_allow_request_multiple_clients(self):
        """Test rate limiting with multiple clients."""
        limiter = RateLimiter(burst_size=5)
        
        client1 = "192.168.1.1"
        client2 = "192.168.1.2"
        
        # Each client should have their own bucket
        allowed1, _ = limiter.allow_request(client1)
        allowed2, _ = limiter.allow_request(client2)
        
        assert allowed1 is True
        assert allowed2 is True
        
        # Client1 makes multiple requests
        for _ in range(4):
            limiter.allow_request(client1)
        
        # Client2 should still be allowed
        allowed2_after, _ = limiter.allow_request(client2)
        assert allowed2_after is True

    def test_rate_limit_exceeded(self):
        """Test rate limit exceeded scenario."""
        limiter = RateLimiter(burst_size=3)
        client_id = "192.168.1.1"
        
        # Consume all tokens (burst_size = 3)
        for _ in range(3):
            allowed, _ = limiter.allow_request(client_id)
            assert allowed is True
        
        # Next request should be denied
        allowed, headers = limiter.allow_request(client_id)
        
        assert allowed is False
        assert headers["X-RateLimit-Remaining"] == "0"
        assert "Retry-After" in headers

    def test_rate_limit_retry_after_header(self):
        """Test Retry-After header when rate limited."""
        limiter = RateLimiter(burst_size=2)
        client_id = "192.168.1.1"
        
        # Exhaust tokens
        limiter.allow_request(client_id)
        limiter.allow_request(client_id)
        
        # Should be rate limited
        allowed, headers = limiter.allow_request(client_id)
        
        assert allowed is False
        retry_after = int(headers["Retry-After"])
        assert retry_after >= 0  # May be 0 if fractional tokens exist

    def test_token_refill_over_time(self):
        """Test tokens refill over time."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        client_id = "192.168.1.1"
        
        # Consume tokens
        for _ in range(5):
            limiter.allow_request(client_id)
        
        # Should be rate limited
        allowed_before, _ = limiter.allow_request(client_id)
        assert allowed_before is False
        
        # Wait for tokens to refill (1 token per second for 60 req/min)
        time.sleep(1.5)
        
        # Should have refilled at least 1 token
        allowed_after, _ = limiter.allow_request(client_id)
        assert allowed_after is True

    def test_bucket_initialization_per_client(self):
        """Test bucket is initialized for new clients."""
        limiter = RateLimiter(burst_size=10)
        
        clients = ["client1", "client2", "client3"]
        
        for client in clients:
            allowed, headers = limiter.allow_request(client)
            assert allowed is True
            # First request should have nearly full bucket
            remaining = int(headers["X-RateLimit-Remaining"])
            assert remaining >= 9

    def test_get_stats_new_client(self):
        """Test getting stats for new client."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        client_id = "192.168.1.1"
        
        stats = limiter.get_stats(client_id)
        
        assert stats["available_tokens"] == 100
        assert stats["burst_size"] == 100
        assert stats["requests_last_minute"] == 0
        assert stats["requests_per_minute_limit"] == 60

    def test_get_stats_after_requests(self):
        """Test getting stats after making requests."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=100)
        client_id = "192.168.1.1"
        
        # Make some requests
        for _ in range(5):
            limiter.allow_request(client_id)
        
        stats = limiter.get_stats(client_id)
        
        # Should have consumed 5 tokens
        assert stats["available_tokens"] < 100
        assert stats["requests_last_minute"] == 5

    def test_request_history_tracking(self):
        """Test request history is tracked."""
        limiter = RateLimiter()
        client_id = "192.168.1.1"
        
        # Make multiple requests
        num_requests = 10
        for _ in range(num_requests):
            limiter.allow_request(client_id)
        
        stats = limiter.get_stats(client_id)
        
        assert stats["requests_last_minute"] == num_requests

    def test_request_history_max_length(self):
        """Test request history maintains max length."""
        limiter = RateLimiter(burst_size=150)
        client_id = "192.168.1.1"
        
        # Make more than 100 requests (max history size)
        for _ in range(150):
            limiter.allow_request(client_id)
        
        # History should be limited to 100
        history = limiter.request_history[client_id]
        assert len(history) == 100

    def test_refill_rate_calculation(self):
        """Test refill rate is calculated correctly."""
        test_cases = [
            (60, 1.0),  # 60 req/min = 1 req/sec
            (120, 2.0),  # 120 req/min = 2 req/sec
            (30, 0.5),  # 30 req/min = 0.5 req/sec
        ]
        
        for requests_per_minute, expected_rate in test_cases:
            limiter = RateLimiter(requests_per_minute=requests_per_minute)
            assert limiter.refill_rate == expected_rate

    def test_burst_size_allows_burst(self):
        """Test burst size allows burst of requests."""
        burst_size = 10
        limiter = RateLimiter(requests_per_minute=60, burst_size=burst_size)
        client_id = "192.168.1.1"
        
        # Should be able to make burst_size requests immediately
        for i in range(burst_size):
            allowed, _ = limiter.allow_request(client_id)
            assert allowed is True, f"Request {i+1} should be allowed"

    def test_tokens_dont_exceed_burst_size(self):
        """Test tokens don't exceed burst size after refill."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=5)
        client_id = "192.168.1.1"
        
        # Make one request
        limiter.allow_request(client_id)
        
        # Wait for more than enough time to refill beyond burst size
        time.sleep(10)
        
        # Check tokens are capped at burst size
        stats = limiter.get_stats(client_id)
        assert stats["available_tokens"] <= stats["burst_size"]

    def test_concurrent_requests_different_clients(self):
        """Test handling concurrent requests from different clients."""
        limiter = RateLimiter(burst_size=5)
        
        clients = [f"client{i}" for i in range(10)]
        
        for client in clients:
            allowed, _ = limiter.allow_request(client)
            assert allowed is True

    def test_zero_tokens_prevents_request(self):
        """Test that zero tokens prevents request."""
        limiter = RateLimiter(burst_size=1)
        client_id = "192.168.1.1"
        
        # Consume the only token
        allowed1, _ = limiter.allow_request(client_id)
        assert allowed1 is True
        
        # Next request should fail
        allowed2, _ = limiter.allow_request(client_id)
        assert allowed2 is False

    def test_fractional_token_refill(self):
        """Test fractional token refill."""
        limiter = RateLimiter(requests_per_minute=60, burst_size=10)
        client_id = "192.168.1.1"
        
        # Consume some tokens
        for _ in range(5):
            limiter.allow_request(client_id)
        
        # Wait for half a second (should refill 0.5 tokens at 1 token/sec)
        time.sleep(0.5)
        
        # Should still have fractional tokens refilled
        stats = limiter.get_stats(client_id)
        # After consuming 5 and waiting 0.5s, should have roughly 5.5 tokens
        # (starting from 10, consumed 5 = 5 left, then refilled 0.5)
        assert stats["available_tokens"] >= 5

    def test_client_id_isolation(self):
        """Test client IDs are properly isolated."""
        limiter = RateLimiter(burst_size=2)
        
        client1 = "192.168.1.1"
        client2 = "192.168.1.2"
        
        # Exhaust client1's tokens
        limiter.allow_request(client1)
        limiter.allow_request(client1)
        allowed1, _ = limiter.allow_request(client1)
        assert allowed1 is False
        
        # Client2 should still be allowed
        allowed2, _ = limiter.allow_request(client2)
        assert allowed2 is True
