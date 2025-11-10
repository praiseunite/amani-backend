"""
Tests for FinCra API client.
"""
import pytest
from decimal import Decimal
from app.core.fincra import FinCraClient, FinCraError


class TestFinCraClient:
    """Test FinCra API client functionality."""
    
    def test_client_initialization(self):
        """Test FinCra client initialization."""
        client = FinCraClient(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://api.fincra.test"
        )
        
        assert client.api_key == "test_key"
        assert client.api_secret == "test_secret"
        assert client.base_url == "https://api.fincra.test"
        assert client.max_retries == 3
    
    def test_client_with_custom_retries(self):
        """Test client with custom retry settings."""
        client = FinCraClient(
            api_key="test_key",
            api_secret="test_secret",
            max_retries=5,
            retry_delay=2.0
        )
        
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
    
    def test_fincra_error_creation(self):
        """Test FinCraError exception creation."""
        error = FinCraError(
            message="Payment failed",
            status_code=400,
            response_data={"error": "Invalid request"}
        )
        
        assert error.message == "Payment failed"
        assert error.status_code == 400
        assert error.response_data == {"error": "Invalid request"}
        assert str(error) == "Payment failed"
