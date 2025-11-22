"""
Tests for FinCra KYC methods.
"""

import pytest

from app.core.fincra import FinCraClient


class TestFinCraKYCMethods:
    """Test FinCra KYC-related methods."""

    def test_submit_kyc_method_exists(self):
        """Test that submit_kyc method exists."""
        client = FinCraClient(api_key="test_key", api_secret="test_secret")
        assert hasattr(client, "submit_kyc")
        assert callable(client.submit_kyc)

    def test_verify_kyc_method_exists(self):
        """Test that verify_kyc method exists."""
        client = FinCraClient(api_key="test_key", api_secret="test_secret")
        assert hasattr(client, "verify_kyc")
        assert callable(client.verify_kyc)

    def test_get_kyc_status_method_exists(self):
        """Test that get_kyc_status method exists."""
        client = FinCraClient(api_key="test_key", api_secret="test_secret")
        assert hasattr(client, "get_kyc_status")
        assert callable(client.get_kyc_status)

    def test_submit_kyc_has_correct_signature(self):
        """Test submit_kyc method signature."""
        import inspect

        client = FinCraClient(api_key="test", api_secret="test")
        sig = inspect.signature(client.submit_kyc)

        # Check required parameters exist
        assert "user_id" in sig.parameters
        assert "kyc_type" in sig.parameters
        assert "nin_or_passport" in sig.parameters
        assert "first_name" in sig.parameters
        assert "last_name" in sig.parameters
        assert "email" in sig.parameters

        # Check optional parameters
        assert "phone" in sig.parameters
        assert "date_of_birth" in sig.parameters
        assert "address" in sig.parameters
        assert "document_image" in sig.parameters
        assert "metadata" in sig.parameters

    def test_verify_kyc_has_correct_signature(self):
        """Test verify_kyc method signature."""
        import inspect

        client = FinCraClient(api_key="test", api_secret="test")
        sig = inspect.signature(client.verify_kyc)

        # Check required parameter
        assert "kyc_id" in sig.parameters

    def test_get_kyc_status_has_correct_signature(self):
        """Test get_kyc_status method signature."""
        import inspect

        client = FinCraClient(api_key="test", api_secret="test")
        sig = inspect.signature(client.get_kyc_status)

        # Check required parameter
        assert "user_id" in sig.parameters


class TestFinCraKYCMethodDocumentation:
    """Test KYC method documentation."""

    def test_submit_kyc_has_docstring(self):
        """Test that submit_kyc has documentation."""
        client = FinCraClient(api_key="test", api_secret="test")
        assert client.submit_kyc.__doc__ is not None
        assert len(client.submit_kyc.__doc__.strip()) > 0

    def test_verify_kyc_has_docstring(self):
        """Test that verify_kyc has documentation."""
        client = FinCraClient(api_key="test", api_secret="test")
        assert client.verify_kyc.__doc__ is not None
        assert len(client.verify_kyc.__doc__.strip()) > 0

    def test_get_kyc_status_has_docstring(self):
        """Test that get_kyc_status has documentation."""
        client = FinCraClient(api_key="test", api_secret="test")
        assert client.get_kyc_status.__doc__ is not None
        assert len(client.get_kyc_status.__doc__.strip()) > 0

    def test_submit_kyc_docstring_mentions_verification(self):
        """Test that submit_kyc docstring mentions verification."""
        client = FinCraClient(api_key="test", api_secret="test")
        docstring = client.submit_kyc.__doc__.lower()
        assert "kyc" in docstring or "verification" in docstring

    def test_verify_kyc_docstring_mentions_status(self):
        """Test that verify_kyc docstring mentions status."""
        client = FinCraClient(api_key="test", api_secret="test")
        docstring = client.verify_kyc.__doc__.lower()
        assert "status" in docstring or "verification" in docstring


class TestFinCraKYCMethodsAreAsync:
    """Test that KYC methods are async."""

    def test_submit_kyc_is_async(self):
        """Test that submit_kyc is async."""
        import inspect

        client = FinCraClient(api_key="test", api_secret="test")
        assert inspect.iscoroutinefunction(client.submit_kyc)

    def test_verify_kyc_is_async(self):
        """Test that verify_kyc is async."""
        import inspect

        client = FinCraClient(api_key="test", api_secret="test")
        assert inspect.iscoroutinefunction(client.verify_kyc)

    def test_get_kyc_status_is_async(self):
        """Test that get_kyc_status is async."""
        import inspect

        client = FinCraClient(api_key="test", api_secret="test")
        assert inspect.iscoroutinefunction(client.get_kyc_status)
