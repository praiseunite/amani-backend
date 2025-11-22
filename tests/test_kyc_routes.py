"""
Tests for KYC routes.
"""

import pytest

from app.routes import kyc


class TestKYCRoutesExist:
    """Test that KYC routes exist and are properly configured."""

    def test_kyc_router_exists(self):
        """Test that KYC router exists."""
        assert hasattr(kyc, "router")
        assert kyc.router is not None

    def test_router_has_correct_prefix(self):
        """Test that router has correct prefix."""
        assert kyc.router.prefix == "/kyc"

    def test_router_has_correct_tags(self):
        """Test that router has correct tags."""
        assert "kyc" in kyc.router.tags


class TestKYCEndpoints:
    """Test KYC endpoint functions."""

    def test_submit_kyc_endpoint_exists(self):
        """Test that submit_kyc endpoint exists."""
        assert hasattr(kyc, "submit_kyc")
        assert callable(kyc.submit_kyc)

    def test_get_kyc_status_endpoint_exists(self):
        """Test that get_kyc_status endpoint exists."""
        assert hasattr(kyc, "get_kyc_status")
        assert callable(kyc.get_kyc_status)

    def test_resubmit_kyc_endpoint_exists(self):
        """Test that resubmit_kyc endpoint exists."""
        assert hasattr(kyc, "resubmit_kyc")
        assert callable(kyc.resubmit_kyc)


class TestKYCEndpointSignatures:
    """Test KYC endpoint signatures."""

    def test_submit_kyc_has_correct_parameters(self):
        """Test submit_kyc endpoint parameters."""
        import inspect

        sig = inspect.signature(kyc.submit_kyc)

        assert "kyc_data" in sig.parameters
        assert "current_user" in sig.parameters
        assert "db" in sig.parameters

    def test_get_kyc_status_has_correct_parameters(self):
        """Test get_kyc_status endpoint parameters."""
        import inspect

        sig = inspect.signature(kyc.get_kyc_status)

        assert "current_user" in sig.parameters
        assert "db" in sig.parameters
        assert "status_filter" in sig.parameters

    def test_resubmit_kyc_has_correct_parameters(self):
        """Test resubmit_kyc endpoint parameters."""
        import inspect

        sig = inspect.signature(kyc.resubmit_kyc)

        assert "kyc_id" in sig.parameters
        assert "kyc_data" in sig.parameters
        assert "current_user" in sig.parameters
        assert "db" in sig.parameters


class TestKYCEndpointsAreAsync:
    """Test that KYC endpoints are async."""

    def test_submit_kyc_is_async(self):
        """Test that submit_kyc is async."""
        import inspect

        assert inspect.iscoroutinefunction(kyc.submit_kyc)

    def test_get_kyc_status_is_async(self):
        """Test that get_kyc_status is async."""
        import inspect

        assert inspect.iscoroutinefunction(kyc.get_kyc_status)

    def test_resubmit_kyc_is_async(self):
        """Test that resubmit_kyc is async."""
        import inspect

        assert inspect.iscoroutinefunction(kyc.resubmit_kyc)


class TestKYCEndpointDocumentation:
    """Test KYC endpoint documentation."""

    def test_submit_kyc_has_docstring(self):
        """Test that submit_kyc has documentation."""
        assert kyc.submit_kyc.__doc__ is not None
        assert len(kyc.submit_kyc.__doc__.strip()) > 0

    def test_get_kyc_status_has_docstring(self):
        """Test that get_kyc_status has documentation."""
        assert kyc.get_kyc_status.__doc__ is not None
        assert len(kyc.get_kyc_status.__doc__.strip()) > 0

    def test_resubmit_kyc_has_docstring(self):
        """Test that resubmit_kyc has documentation."""
        assert kyc.resubmit_kyc.__doc__ is not None
        assert len(kyc.resubmit_kyc.__doc__.strip()) > 0

    def test_submit_kyc_docstring_mentions_verification(self):
        """Test that submit_kyc docstring mentions verification."""
        docstring = kyc.submit_kyc.__doc__.lower()
        assert "kyc" in docstring or "verification" in docstring

    def test_get_kyc_status_docstring_mentions_status(self):
        """Test that get_kyc_status docstring mentions status."""
        docstring = kyc.get_kyc_status.__doc__.lower()
        assert "status" in docstring or "kyc" in docstring

    def test_resubmit_kyc_docstring_mentions_resubmit(self):
        """Test that resubmit_kyc docstring mentions resubmit."""
        docstring = kyc.resubmit_kyc.__doc__.lower()
        assert "resubmit" in docstring or "rejected" in docstring


class TestKYCRouterRegistration:
    """Test that KYC router is properly registered in main app."""

    def test_kyc_routes_in_main_app(self):
        """Test that KYC routes are registered in main app."""
        from app.main import app

        # Get all routes
        routes = [route.path for route in app.routes if hasattr(route, "path")]

        # Check KYC routes are present
        assert any("/kyc/submit" in route for route in routes)
        assert any("/kyc/status" in route for route in routes)
        assert any("/kyc/resubmit" in route for route in routes)

    def test_kyc_submit_route_method(self):
        """Test that KYC submit route uses POST method."""
        from app.main import app

        for route in app.routes:
            if hasattr(route, "path") and "/kyc/submit" in route.path:
                assert "POST" in route.methods
                break
        else:
            pytest.fail("KYC submit route not found")

    def test_kyc_status_route_method(self):
        """Test that KYC status route uses GET method."""
        from app.main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/api/v1/kyc/status":
                assert "GET" in route.methods
                break
        else:
            pytest.fail("KYC status route not found")

    def test_kyc_resubmit_route_method(self):
        """Test that KYC resubmit route uses POST method."""
        from app.main import app

        for route in app.routes:
            if hasattr(route, "path") and "/kyc/resubmit" in route.path:
                assert "POST" in route.methods
                break
        else:
            pytest.fail("KYC resubmit route not found")
