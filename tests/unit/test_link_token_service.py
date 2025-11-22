"""Unit tests for LinkTokenService."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.composition import build_in_memory_services
from app.domain.entities import WalletProvider
from app.domain.services import PolicyEnforcer


class TestLinkTokenService:
    """Test suite for LinkTokenService."""

    @pytest.fixture
    def services(self):
        """Build services for testing."""
        return build_in_memory_services()

    @pytest.fixture
    def link_token_service(self, services):
        """Get link token service."""
        return services["link_token_service"]

    @pytest.fixture
    def audit_port(self, services):
        """Get audit port."""
        return services["audit_port"]

    @pytest.mark.asyncio
    async def test_create_link_token(self, link_token_service, audit_port):
        """Test creating a link token."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA

        # Create link token
        link_token = await link_token_service.create_link_token(user_id, provider)

        # Verify token properties
        assert link_token.user_id == user_id
        assert link_token.provider == provider
        assert link_token.token != ""
        assert len(link_token.token) > 0
        assert link_token.is_consumed is False
        assert link_token.expires_at > datetime.utcnow()

        # Verify audit was recorded
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "create_link_token"
        assert events[0]["user_id"] == user_id
        assert events[0]["resource_type"] == "link_token"

    @pytest.mark.asyncio
    async def test_consume_valid_link_token(self, link_token_service, audit_port):
        """Test consuming a valid link token."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA

        # Create link token
        created_token = await link_token_service.create_link_token(user_id, provider)

        # Consume the token
        consumed_token = await link_token_service.consume_link_token(created_token.token)

        # Verify token was consumed
        assert consumed_token is not None
        assert consumed_token.id == created_token.id
        assert consumed_token.is_consumed is True
        assert consumed_token.consumed_at is not None

        # Verify audit events
        events = audit_port.get_events()
        assert len(events) == 2
        assert events[1]["action"] == "consume_link_token"

    @pytest.mark.asyncio
    async def test_consume_nonexistent_token(self, link_token_service):
        """Test consuming a token that doesn't exist."""
        consumed_token = await link_token_service.consume_link_token("nonexistent-token")

        assert consumed_token is None

    @pytest.mark.asyncio
    async def test_consume_already_consumed_token(self, link_token_service):
        """Test consuming a token that has already been consumed."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA

        # Create and consume token
        created_token = await link_token_service.create_link_token(user_id, provider)
        await link_token_service.consume_link_token(created_token.token)

        # Try to consume again
        second_consume = await link_token_service.consume_link_token(created_token.token)

        assert second_consume is None

    @pytest.mark.asyncio
    async def test_consume_expired_token(self, services):
        """Test consuming an expired token."""
        link_token_service = services["link_token_service"]
        link_token_port = services["link_token_port"]

        user_id = uuid4()
        provider = WalletProvider.FINCRA

        # Create link token
        created_token = await link_token_service.create_link_token(user_id, provider)

        # Manually expire the token by setting expires_at in the past
        token_from_repo = await link_token_port.find_by_token(created_token.token)
        # Set expired time
        token_from_repo.expires_at = datetime.utcnow() - timedelta(hours=1)
        await link_token_port.create(token_from_repo)

        # Try to consume expired token
        consumed_token = await link_token_service.consume_link_token(created_token.token)

        assert consumed_token is None


class TestPolicyEnforcer:
    """Test suite for PolicyEnforcer."""

    @pytest.fixture
    def policy_enforcer(self):
        """Get policy enforcer."""
        return PolicyEnforcer()

    def test_generate_secure_token(self, policy_enforcer):
        """Test token generation."""
        token1 = policy_enforcer.generate_secure_token()
        token2 = policy_enforcer.generate_secure_token()

        # Tokens should be non-empty and different
        assert len(token1) > 0
        assert len(token2) > 0
        assert token1 != token2

    def test_calculate_expiry(self, policy_enforcer):
        """Test expiry calculation."""
        expiry = policy_enforcer.calculate_expiry()

        # Expiry should be in the future
        assert expiry > datetime.utcnow()

        # Expiry should be approximately 60 minutes from now
        expected_expiry = datetime.utcnow() + timedelta(
            minutes=policy_enforcer.token_expiry_minutes
        )
        time_diff = abs((expiry - expected_expiry).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    def test_is_token_expired(self, policy_enforcer):
        """Test token expiry checking."""
        # Test future date
        future_date = datetime.utcnow() + timedelta(hours=1)
        assert policy_enforcer.is_token_expired(future_date) is False

        # Test past date
        past_date = datetime.utcnow() - timedelta(hours=1)
        assert policy_enforcer.is_token_expired(past_date) is True
