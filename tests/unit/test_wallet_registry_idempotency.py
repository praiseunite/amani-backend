"""Unit tests for wallet registry idempotency."""

import pytest
from uuid import uuid4

from app.domain.entities import WalletProvider
from app.application.services.wallet_registry_service import WalletRegistryService
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.adapters.inmemory.audit import InMemoryAudit


class TestWalletRegistryIdempotency:
    """Test suite for wallet registry idempotent behavior."""

    @pytest.fixture
    def wallet_registry_port(self):
        """Create in-memory wallet registry port."""
        return InMemoryWalletRegistry()

    @pytest.fixture
    def audit_port(self):
        """Create in-memory audit port."""
        return InMemoryAudit()

    @pytest.fixture
    def service(self, wallet_registry_port, audit_port):
        """Create wallet registry service."""
        return WalletRegistryService(
            wallet_registry_port=wallet_registry_port,
            audit_port=audit_port,
        )

    @pytest.mark.asyncio
    async def test_register_new_wallet(self, service):
        """Test registering a new wallet."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"
        idempotency_key = "idem_key_1"

        result = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        assert result is not None
        assert result.user_id == user_id
        assert result.provider == provider
        assert result.provider_account_id == provider_wallet_id
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_register_idempotent_same_idempotency_key(self, service):
        """Test that registering with same idempotency_key returns existing wallet."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"
        idempotency_key = "idem_key_1"

        # First registration
        result1 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Second registration with same idempotency_key
        result2 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Should return the same wallet
        assert result1.id == result2.id
        assert result1.user_id == result2.user_id
        assert result1.provider == result2.provider

    @pytest.mark.asyncio
    async def test_register_idempotent_same_provider_wallet(self, service):
        """Test that registering same provider+wallet returns existing wallet."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"

        # First registration without idempotency_key
        result1 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
        )

        # Second registration with same provider+wallet
        result2 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
        )

        # Should return the same wallet
        assert result1.id == result2.id
        assert result1.user_id == result2.user_id
        assert result1.provider == result2.provider

    @pytest.mark.asyncio
    async def test_register_different_wallets_same_provider(self, service):
        """Test registering different wallets for same provider."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA

        # Register first wallet
        result1 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id="wallet_123",
            idempotency_key="idem_key_1",
        )

        # Register second wallet (different wallet_id)
        result2 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id="wallet_456",
            idempotency_key="idem_key_2",
        )

        # Should be different wallets
        assert result1.id != result2.id
        assert result1.provider_account_id != result2.provider_account_id

    @pytest.mark.asyncio
    async def test_register_different_providers_same_wallet_id(self, service):
        """Test registering different providers with same wallet ID."""
        user_id = uuid4()
        provider_wallet_id = "wallet_123"

        # Register with FINCRA
        result1 = await service.register(
            user_id=user_id,
            provider=WalletProvider.FINCRA,
            provider_wallet_id=provider_wallet_id,
            idempotency_key="idem_key_1",
        )

        # Register with PAYSTACK
        result2 = await service.register(
            user_id=user_id,
            provider=WalletProvider.PAYSTACK,
            provider_wallet_id=provider_wallet_id,
            idempotency_key="idem_key_2",
        )

        # Should be different wallets
        assert result1.id != result2.id
        assert result1.provider != result2.provider

    @pytest.mark.asyncio
    async def test_register_with_metadata(self, service):
        """Test registering wallet with metadata."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"
        metadata = {"kyc_verified": True, "tier": "premium"}

        result = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            metadata=metadata,
        )

        assert result.metadata == metadata

    @pytest.mark.asyncio
    async def test_register_with_provider_customer_id(self, service):
        """Test registering wallet with provider customer ID."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"
        provider_customer_id = "customer_456"

        result = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            provider_customer_id=provider_customer_id,
        )

        assert result.provider_customer_id == provider_customer_id

    @pytest.mark.asyncio
    async def test_audit_events_recorded(self, service, audit_port):
        """Test that audit events are recorded for new registrations."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"
        idempotency_key = "idem_key_1"

        # Register wallet
        await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Check audit events
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "register_wallet"
        assert events[0]["user_id"] == user_id
        assert events[0]["resource_type"] == "wallet_registry"
        assert events[0]["details"]["provider"] == provider.value
        assert events[0]["details"]["provider_wallet_id"] == provider_wallet_id

    @pytest.mark.asyncio
    async def test_no_duplicate_audit_for_idempotent_request(self, service, audit_port):
        """Test that no duplicate audit events for idempotent requests."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = "wallet_123"
        idempotency_key = "idem_key_1"

        # First registration
        await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Second registration (idempotent)
        await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Should only have one audit event (from first registration)
        events = audit_port.get_events()
        assert len(events) == 1
