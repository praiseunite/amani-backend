"""Unit tests for LinkTokenService.

These tests use in-memory adapters to test the domain logic.
"""

import pytest
from datetime import datetime

from app.domain.entities import User, UserRole, LinkTokenStatus, WalletProvider
from app.domain.services import LinkTokenService, PolicyEnforcer
from app.adapters.inmemory.user_repo import InMemoryUserRepository
from app.adapters.inmemory.link_token_repo import InMemoryLinkTokenRepository
from app.adapters.inmemory.audit import InMemoryAuditLog


@pytest.fixture
def user_repository():
    """Fixture for in-memory user repository."""
    return InMemoryUserRepository()


@pytest.fixture
def link_token_repository():
    """Fixture for in-memory link token repository."""
    return InMemoryLinkTokenRepository()


@pytest.fixture
def audit_log():
    """Fixture for in-memory audit log."""
    return InMemoryAuditLog()


@pytest.fixture
def policy_enforcer():
    """Fixture for policy enforcer."""
    return PolicyEnforcer()


@pytest.fixture
def link_token_service(user_repository, link_token_repository, audit_log, policy_enforcer):
    """Fixture for link token service."""
    return LinkTokenService(
        link_token_port=link_token_repository,
        user_repository=user_repository,
        audit_port=audit_log,
        policy_enforcer=policy_enforcer,
    )


@pytest.fixture
async def test_user(user_repository):
    """Fixture for a test user."""
    user = User(
        id="user-123",
        external_id="ext-123",
        email="test@example.com",
        role=UserRole.CLIENT,
        created_at=datetime.utcnow(),
    )
    await user_repository.save(user)
    return user


class TestLinkTokenServiceCreate:
    """Tests for link token creation."""

    @pytest.mark.asyncio
    async def test_create_link_token_success(self, link_token_service, test_user, audit_log):
        """Test successful link token creation."""
        # Act
        link_token = await link_token_service.create_link_token(test_user.id, WalletProvider.PLAID)

        # Assert
        assert link_token is not None
        assert link_token.user_id == test_user.id
        assert link_token.provider == WalletProvider.PLAID
        assert link_token.status == LinkTokenStatus.PENDING
        assert link_token.token is not None
        assert len(link_token.token) > 0

        # Verify audit log
        events = audit_log.get_events()
        assert len(events) == 1
        assert events[0].event_type == "link_token_created"
        assert events[0].user_id == test_user.id

    @pytest.mark.asyncio
    async def test_create_link_token_user_not_found(self, link_token_service):
        """Test link token creation with non-existent user."""
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            await link_token_service.create_link_token("non-existent-user", WalletProvider.PLAID)

    @pytest.mark.asyncio
    async def test_create_link_token_generates_unique_tokens(self, link_token_service, test_user):
        """Test that each token creation generates a unique token."""
        # Act
        token1 = await link_token_service.create_link_token(test_user.id, WalletProvider.PLAID)
        token2 = await link_token_service.create_link_token(test_user.id, WalletProvider.FINCRA)

        # Assert
        assert token1.token != token2.token


class TestLinkTokenServiceConsume:
    """Tests for link token consumption."""

    @pytest.mark.asyncio
    async def test_consume_link_token_success(self, link_token_service, test_user, audit_log):
        """Test successful link token consumption."""
        # Arrange
        link_token = await link_token_service.create_link_token(test_user.id, WalletProvider.PLAID)
        audit_log.clear()  # Clear creation event

        # Act
        consumed_token = await link_token_service.consume_link_token(link_token.token)

        # Assert
        assert consumed_token is not None
        assert consumed_token.status == LinkTokenStatus.CONSUMED
        assert consumed_token.consumed_at is not None

        # Verify audit log
        events = audit_log.get_events()
        assert len(events) == 1
        assert events[0].event_type == "link_token_consumed"
        assert events[0].user_id == test_user.id

    @pytest.mark.asyncio
    async def test_consume_link_token_not_found(self, link_token_service):
        """Test consumption of non-existent token."""
        # Act & Assert
        with pytest.raises(ValueError, match="Link token not found"):
            await link_token_service.consume_link_token("non-existent-token")

    @pytest.mark.asyncio
    async def test_consume_link_token_already_consumed(self, link_token_service, test_user):
        """Test consumption of already consumed token."""
        # Arrange
        link_token = await link_token_service.create_link_token(test_user.id, WalletProvider.PLAID)
        await link_token_service.consume_link_token(link_token.token)

        # Act & Assert
        with pytest.raises(ValueError, match="Link token already consumed"):
            await link_token_service.consume_link_token(link_token.token)


class TestPolicyEnforcer:
    """Tests for PolicyEnforcer."""

    def test_can_create_link_token_with_valid_user(self, policy_enforcer, test_user):
        """Test policy allows valid user to create link token."""
        # Act
        result = policy_enforcer.can_create_link_token(test_user)

        # Assert
        assert result is True

    def test_can_create_link_token_with_none_user(self, policy_enforcer):
        """Test policy denies None user."""
        # Act
        result = policy_enforcer.can_create_link_token(None)

        # Assert
        assert result is False

    def test_get_token_expiration_time(self, policy_enforcer):
        """Test token expiration time is in the future."""
        # Act
        expiration = policy_enforcer.get_token_expiration_time()

        # Assert
        assert expiration > datetime.utcnow()
