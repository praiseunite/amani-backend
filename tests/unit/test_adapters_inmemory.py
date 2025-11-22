"""
Comprehensive unit tests for in-memory adapter implementations.
Tests adapter behavior, interface conformance, and edge cases.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from app.domain.entities import (
    LinkToken,
    WalletRegistryEntry,
    WalletProvider,
    User,
)
from app.adapters.inmemory.link_token_repo import InMemoryLinkTokenRepository
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.adapters.inmemory.user_repo import InMemoryUserRepository
from app.adapters.inmemory.audit import InMemoryAudit
from app.errors import DuplicateEntryError


class TestInMemoryLinkTokenRepository:
    """Test suite for InMemoryLinkTokenRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance."""
        return InMemoryLinkTokenRepository()

    @pytest.mark.asyncio
    async def test_create_link_token(self, repository):
        """Test creating a link token."""
        token = LinkToken(
            user_id=uuid4(),
            token="test_token_123",
            provider=WalletProvider.FINCRA,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        
        result = await repository.create(token)
        
        assert result.token == token.token
        assert result.user_id == token.user_id

    @pytest.mark.asyncio
    async def test_find_by_token_existing(self, repository):
        """Test finding an existing token."""
        token = LinkToken(
            user_id=uuid4(),
            token="findable_token",
            provider=WalletProvider.FINCRA,
        )
        await repository.create(token)
        
        found = await repository.find_by_token("findable_token")
        
        assert found is not None
        assert found.token == "findable_token"

    @pytest.mark.asyncio
    async def test_find_by_token_nonexistent(self, repository):
        """Test finding a nonexistent token."""
        found = await repository.find_by_token("nonexistent_token")
        
        assert found is None

    @pytest.mark.asyncio
    async def test_mark_consumed(self, repository):
        """Test marking a token as consumed."""
        token = LinkToken(
            user_id=uuid4(),
            token="consume_me",
            provider=WalletProvider.FINCRA,
        )
        await repository.create(token)
        
        marked = await repository.mark_consumed(token)
        
        assert marked.is_consumed is True
        assert marked.consumed_at is not None

    @pytest.mark.asyncio
    async def test_mark_consumed_updates_storage(self, repository):
        """Test that marking consumed updates the stored token."""
        token = LinkToken(
            user_id=uuid4(),
            token="update_test",
            provider=WalletProvider.FINCRA,
        )
        await repository.create(token)
        await repository.mark_consumed(token)
        
        # Retrieve again
        found = await repository.find_by_token("update_test")
        
        assert found.is_consumed is True

    @pytest.mark.asyncio
    async def test_multiple_tokens(self, repository):
        """Test storing and retrieving multiple tokens."""
        tokens = [
            LinkToken(user_id=uuid4(), token=f"token_{i}", provider=WalletProvider.FINCRA)
            for i in range(5)
        ]
        
        for token in tokens:
            await repository.create(token)
        
        # All should be findable
        for i in range(5):
            found = await repository.find_by_token(f"token_{i}")
            assert found is not None

    @pytest.mark.asyncio
    async def test_overwrite_token(self, repository):
        """Test that creating with same token overwrites."""
        token1 = LinkToken(user_id=uuid4(), token="same_token", provider=WalletProvider.FINCRA)
        token2 = LinkToken(user_id=uuid4(), token="same_token", provider=WalletProvider.PAYSTACK)
        
        await repository.create(token1)
        await repository.create(token2)
        
        found = await repository.find_by_token("same_token")
        assert found.provider == WalletProvider.PAYSTACK


class TestInMemoryWalletRegistry:
    """Test suite for InMemoryWalletRegistry."""

    @pytest.fixture
    def registry(self):
        """Create registry instance."""
        return InMemoryWalletRegistry()

    @pytest.mark.asyncio
    async def test_register_wallet(self, registry):
        """Test registering a wallet."""
        entry = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_123",
        )
        
        result = await registry.register(entry)
        
        assert result.provider_account_id == "acc_123"

    @pytest.mark.asyncio
    async def test_register_duplicate_raises_error(self, registry):
        """Test that duplicate registration raises error."""
        user_id = uuid4()
        entry = WalletRegistryEntry(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_duplicate",
        )
        
        await registry.register(entry)
        
        # Try to register same wallet again
        with pytest.raises(DuplicateEntryError):
            await registry.register(entry)

    @pytest.mark.asyncio
    async def test_register_with_idempotency_key(self, registry):
        """Test registering wallet with idempotency key."""
        entry = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_idem",
        )
        
        result = await registry.register(entry, idempotency_key="idem_key_123")
        
        assert result.provider_account_id == "acc_idem"

    @pytest.mark.asyncio
    async def test_register_duplicate_idempotency_key_raises_error(self, registry):
        """Test that duplicate idempotency key raises error."""
        entry1 = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_1",
        )
        entry2 = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.PAYSTACK,
            provider_account_id="acc_2",
        )
        
        await registry.register(entry1, idempotency_key="same_key")
        
        with pytest.raises(DuplicateEntryError):
            await registry.register(entry2, idempotency_key="same_key")

    @pytest.mark.asyncio
    async def test_get_by_provider(self, registry):
        """Test getting wallet by provider."""
        user_id = uuid4()
        entry = WalletRegistryEntry(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_provider",
        )
        await registry.register(entry)
        
        found = await registry.get_by_provider(user_id, WalletProvider.FINCRA)
        
        assert found is not None
        assert found.provider_account_id == "acc_provider"

    @pytest.mark.asyncio
    async def test_get_by_provider_not_found(self, registry):
        """Test getting nonexistent wallet by provider."""
        user_id = uuid4()
        
        found = await registry.get_by_provider(user_id, WalletProvider.FINCRA)
        
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_idempotency_key(self, registry):
        """Test getting wallet by idempotency key."""
        entry = WalletRegistryEntry(
            user_id=uuid4(),
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_key",
        )
        await registry.register(entry, idempotency_key="find_me")
        
        found = await registry.get_by_idempotency_key("find_me")
        
        assert found is not None
        assert found.provider_account_id == "acc_key"

    @pytest.mark.asyncio
    async def test_get_by_idempotency_key_not_found(self, registry):
        """Test getting nonexistent idempotency key."""
        found = await registry.get_by_idempotency_key("not_found")
        
        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_provider_wallet(self, registry):
        """Test getting wallet by provider wallet ID."""
        user_id = uuid4()
        entry = WalletRegistryEntry(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_account_id="acc_specific",
        )
        await registry.register(entry)
        
        found = await registry.get_by_provider_wallet(
            user_id, WalletProvider.FINCRA, "acc_specific"
        )
        
        assert found is not None
        assert found.provider_account_id == "acc_specific"

    @pytest.mark.asyncio
    async def test_get_by_provider_wallet_not_found(self, registry):
        """Test getting nonexistent provider wallet."""
        found = await registry.get_by_provider_wallet(
            uuid4(), WalletProvider.FINCRA, "nonexistent"
        )
        
        assert found is None

    @pytest.mark.asyncio
    async def test_multiple_providers_same_user(self, registry):
        """Test registering multiple providers for same user."""
        user_id = uuid4()
        
        entry1 = WalletRegistryEntry(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_account_id="fincra_acc",
        )
        entry2 = WalletRegistryEntry(
            user_id=user_id,
            provider=WalletProvider.PAYSTACK,
            provider_account_id="paystack_acc",
        )
        
        await registry.register(entry1)
        await registry.register(entry2)
        
        found_fincra = await registry.get_by_provider(user_id, WalletProvider.FINCRA)
        found_paystack = await registry.get_by_provider(user_id, WalletProvider.PAYSTACK)
        
        assert found_fincra.provider_account_id == "fincra_acc"
        assert found_paystack.provider_account_id == "paystack_acc"


class TestInMemoryUserRepository:
    """Test suite for InMemoryUserRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance."""
        return InMemoryUserRepository()

    @pytest.mark.asyncio
    async def test_save_user(self, repository):
        """Test saving a user."""
        user = User(
            external_id="ext_123",
            email="test@example.com",
            full_name="Test User",
        )
        
        result = await repository.save(user)
        
        assert result.email == "test@example.com"
        assert result.external_id == "ext_123"

    @pytest.mark.asyncio
    async def test_find_by_external_id(self, repository):
        """Test finding user by external ID."""
        user = User(external_id="find_me", email="user@example.com")
        await repository.save(user)
        
        found = await repository.find_by_external_id("find_me")
        
        assert found is not None
        assert found.external_id == "find_me"

    @pytest.mark.asyncio
    async def test_find_by_external_id_not_found(self, repository):
        """Test finding nonexistent external ID."""
        found = await repository.find_by_external_id("nonexistent")
        
        assert found is None

    @pytest.mark.asyncio
    async def test_find_by_id(self, repository):
        """Test finding user by ID."""
        user = User(external_id="ext", email="find@example.com")
        saved = await repository.save(user)
        
        found = await repository.find_by_id(saved.id)
        
        assert found is not None
        assert found.id == saved.id

    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository):
        """Test finding nonexistent ID."""
        found = await repository.find_by_id(uuid4())
        
        assert found is None

    @pytest.mark.asyncio
    async def test_multiple_users(self, repository):
        """Test storing multiple users."""
        users = [
            User(external_id=f"ext_{i}", email=f"user{i}@example.com")
            for i in range(5)
        ]
        
        for user in users:
            await repository.save(user)
        
        # All should be findable
        for i in range(5):
            found = await repository.find_by_external_id(f"ext_{i}")
            assert found is not None

    @pytest.mark.asyncio
    async def test_update_user(self, repository):
        """Test updating an existing user."""
        user = User(external_id="ext_update", email="original@example.com")
        saved = await repository.save(user)
        
        # Update the user
        saved.email = "updated@example.com"
        updated = await repository.save(saved)
        
        # Should reflect the update
        found = await repository.find_by_id(saved.id)
        assert found.email == "updated@example.com"


class TestInMemoryAudit:
    """Test suite for InMemoryAudit."""

    @pytest.fixture
    def audit(self):
        """Create audit instance."""
        return InMemoryAudit()

    @pytest.mark.asyncio
    async def test_record_audit_event(self, audit):
        """Test recording an audit event."""
        user_id = uuid4()
        
        await audit.record(
            user_id=user_id,
            action="test_action",
            resource_type="test_resource",
            resource_id="res_123",
            details={"key": "value"},
        )
        
        events = audit.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "test_action"

    @pytest.mark.asyncio
    async def test_record_multiple_events(self, audit):
        """Test recording multiple audit events."""
        user_id = uuid4()
        
        for i in range(5):
            await audit.record(
                user_id=user_id,
                action=f"action_{i}",
                resource_type="test",
                resource_id=f"res_{i}",
                details={},
            )
        
        events = audit.get_events()
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_get_events_returns_list(self, audit):
        """Test that get_events returns a list."""
        events = audit.get_events()
        
        assert isinstance(events, list)
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_audit_event_structure(self, audit):
        """Test audit event has correct structure."""
        user_id = uuid4()
        
        await audit.record(
            user_id=user_id,
            action="test_action",
            resource_type="test_resource",
            resource_id="res_123",
            details={"detail_key": "detail_value"},
        )
        
        events = audit.get_events()
        event = events[0]
        
        assert "user_id" in event
        assert "action" in event
        assert "resource_type" in event
        assert "resource_id" in event
        assert "details" in event
        assert event["user_id"] == user_id
        assert event["details"]["detail_key"] == "detail_value"

    @pytest.mark.asyncio
    async def test_events_ordered_chronologically(self, audit):
        """Test that events are stored in chronological order."""
        user_id = uuid4()
        
        await audit.record(user_id=user_id, action="first", resource_type="test", resource_id="1", details={})
        await audit.record(user_id=user_id, action="second", resource_type="test", resource_id="2", details={})
        await audit.record(user_id=user_id, action="third", resource_type="test", resource_id="3", details={})
        
        events = audit.get_events()
        
        assert events[0]["action"] == "first"
        assert events[1]["action"] == "second"
        assert events[2]["action"] == "third"
