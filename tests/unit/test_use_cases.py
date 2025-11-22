"""
Comprehensive unit tests for application use cases.
Tests orchestration logic and business workflows.
"""

import pytest
from uuid import uuid4
from app.domain.entities import WalletProvider
from app.application.use_cases.create_link_token import CreateLinkTokenUseCase
from app.application.use_cases.register_wallet import RegisterWalletUseCase
from app.application.use_cases.get_user_status import GetUserStatusUseCase
from app.composition import build_in_memory_services


class TestCreateLinkTokenUseCase:
    """Test suite for CreateLinkTokenUseCase."""

    @pytest.fixture
    def services(self):
        """Build in-memory services."""
        return build_in_memory_services()

    @pytest.fixture
    def use_case(self, services):
        """Create use case instance."""
        return CreateLinkTokenUseCase(services["link_token_service"])

    @pytest.mark.asyncio
    async def test_execute_creates_link_token(self, use_case):
        """Test execute creates a link token."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        result = await use_case.execute(user_id, provider)
        
        assert result.user_id == user_id
        assert result.provider == provider
        assert result.token != ""
        assert result.is_consumed is False

    @pytest.mark.asyncio
    async def test_execute_with_different_providers(self, use_case):
        """Test execute with different providers."""
        user_id = uuid4()
        
        fincra_token = await use_case.execute(user_id, WalletProvider.FINCRA)
        paystack_token = await use_case.execute(user_id, WalletProvider.PAYSTACK)
        
        assert fincra_token.provider == WalletProvider.FINCRA
        assert paystack_token.provider == WalletProvider.PAYSTACK
        assert fincra_token.token != paystack_token.token

    @pytest.mark.asyncio
    async def test_execute_generates_unique_tokens(self, use_case):
        """Test execute generates unique tokens."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        tokens = []
        for _ in range(5):
            token = await use_case.execute(user_id, provider)
            tokens.append(token.token)
        
        # All tokens should be unique
        assert len(set(tokens)) == 5

    @pytest.mark.asyncio
    async def test_execute_token_not_expired(self, use_case):
        """Test execute creates non-expired token."""
        from datetime import datetime
        
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        token = await use_case.execute(user_id, provider)
        
        assert token.expires_at > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_use_case_delegates_to_service(self, services):
        """Test use case properly delegates to service."""
        link_token_service = services["link_token_service"]
        audit_port = services["audit_port"]
        use_case = CreateLinkTokenUseCase(link_token_service)
        
        user_id = uuid4()
        await use_case.execute(user_id, WalletProvider.FINCRA)
        
        # Service should have recorded audit event
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "create_link_token"


class TestRegisterWalletUseCase:
    """Test suite for RegisterWalletUseCase."""

    @pytest.fixture
    def services(self):
        """Build in-memory services."""
        return build_in_memory_services()

    @pytest.fixture
    def use_case(self, services):
        """Create use case instance."""
        return RegisterWalletUseCase(services["wallet_registry_service"])

    @pytest.mark.asyncio
    async def test_execute_registers_wallet(self, use_case):
        """Test execute registers a wallet."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_12345"
        
        result = await use_case.execute(user_id, provider, provider_account_id)
        
        assert result.user_id == user_id
        assert result.provider == provider
        assert result.provider_account_id == provider_account_id
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_execute_with_customer_id(self, use_case):
        """Test execute with provider customer ID."""
        user_id = uuid4()
        provider = WalletProvider.PAYSTACK
        provider_account_id = "acc_123"
        provider_customer_id = "cust_456"
        
        result = await use_case.execute(
            user_id, provider, provider_account_id, provider_customer_id
        )
        
        assert result.provider_customer_id == provider_customer_id

    @pytest.mark.asyncio
    async def test_execute_with_metadata(self, use_case):
        """Test execute with metadata."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_789"
        metadata = {"source": "api", "version": "v1"}
        
        result = await use_case.execute(
            user_id, provider, provider_account_id, metadata=metadata
        )
        
        assert result.metadata == metadata

    @pytest.mark.asyncio
    async def test_execute_is_idempotent(self, use_case):
        """Test execute is idempotent."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_idempotent"
        
        # First registration
        result1 = await use_case.execute(user_id, provider, provider_account_id)
        
        # Second registration (should return same wallet)
        result2 = await use_case.execute(user_id, provider, provider_account_id)
        
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_execute_multiple_providers(self, use_case):
        """Test execute with multiple providers for same user."""
        user_id = uuid4()
        
        fincra_wallet = await use_case.execute(
            user_id, WalletProvider.FINCRA, "fincra_acc"
        )
        paystack_wallet = await use_case.execute(
            user_id, WalletProvider.PAYSTACK, "paystack_acc"
        )
        
        assert fincra_wallet.provider == WalletProvider.FINCRA
        assert paystack_wallet.provider == WalletProvider.PAYSTACK
        assert fincra_wallet.id != paystack_wallet.id

    @pytest.mark.asyncio
    async def test_use_case_creates_audit_event(self, services):
        """Test use case creates audit event."""
        wallet_registry_service = services["wallet_registry_service"]
        audit_port = services["audit_port"]
        use_case = RegisterWalletUseCase(wallet_registry_service)
        
        user_id = uuid4()
        await use_case.execute(user_id, WalletProvider.FINCRA, "acc_audit")
        
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "register_wallet"


class TestGetUserStatusUseCase:
    """Test suite for GetUserStatusUseCase."""

    @pytest.fixture
    def services(self):
        """Build in-memory services."""
        return build_in_memory_services()

    @pytest.fixture
    def use_case(self, services):
        """Create use case instance."""
        return services["get_user_status_use_case"]

    @pytest.mark.asyncio
    async def test_execute_with_existing_user(self, use_case, services):
        """Test execute with existing user."""
        from app.domain.entities import User
        
        user = User(external_id="ext_exists", email="exists@example.com")
        await services["user_repository_port"].save(user)
        
        result = await use_case.execute(user.id)
        
        # Result should be the user object or user-related data
        assert result is not None


class TestUseCaseIntegration:
    """Test suite for use case integration scenarios."""

    @pytest.fixture
    def services(self):
        """Build in-memory services."""
        return build_in_memory_services()

    @pytest.mark.asyncio
    async def test_create_token_and_register_wallet_flow(self, services):
        """Test complete flow: create link token, then register wallet."""
        from app.domain.entities import User
        
        # Setup
        user = User(external_id="ext_flow", email="flow@example.com")
        await services["user_repository_port"].save(user)
        
        # Create link token
        create_token_uc = CreateLinkTokenUseCase(services["link_token_service"])
        link_token = await create_token_uc.execute(user.id, WalletProvider.FINCRA)
        
        # Register wallet
        register_wallet_uc = RegisterWalletUseCase(services["wallet_registry_service"])
        wallet = await register_wallet_uc.execute(
            user.id, WalletProvider.FINCRA, "acc_flow"
        )
        
        # Get user status - use the pre-configured use case from services
        status = await services["get_user_status_use_case"].execute(user.id)
        
        assert status is not None
        assert wallet.user_id == user.id

    @pytest.mark.asyncio
    async def test_multiple_use_cases_share_state(self, services):
        """Test that multiple use cases share adapter state."""
        from app.domain.entities import User
        
        user = User(external_id="ext_shared", email="shared@example.com")
        await services["user_repository_port"].save(user)
        
        # Create multiple tokens
        create_token_uc = CreateLinkTokenUseCase(services["link_token_service"])
        token1 = await create_token_uc.execute(user.id, WalletProvider.FINCRA)
        token2 = await create_token_uc.execute(user.id, WalletProvider.PAYSTACK)
        
        # Both tokens should be in the same repository
        found_token1 = await services["link_token_port"].find_by_token(token1.token)
        found_token2 = await services["link_token_port"].find_by_token(token2.token)
        
        assert found_token1 is not None
        assert found_token2 is not None

    @pytest.mark.asyncio
    async def test_audit_events_accumulated(self, services):
        """Test that audit events accumulate across use cases."""
        from app.domain.entities import User
        
        user = User(external_id="ext_audit", email="audit@example.com")
        await services["user_repository_port"].save(user)
        
        # Execute multiple use cases
        create_token_uc = CreateLinkTokenUseCase(services["link_token_service"])
        await create_token_uc.execute(user.id, WalletProvider.FINCRA)
        
        register_wallet_uc = RegisterWalletUseCase(services["wallet_registry_service"])
        await register_wallet_uc.execute(user.id, WalletProvider.FINCRA, "acc_audit")
        
        # Check accumulated audit events
        events = services["audit_port"].get_events()
        assert len(events) == 2
        assert events[0]["action"] == "create_link_token"
        assert events[1]["action"] == "register_wallet"
