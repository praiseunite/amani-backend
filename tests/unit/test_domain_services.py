"""
Comprehensive unit tests for app.domain.services module.
Tests business logic services including PolicyEnforcer, LinkTokenService, and WalletRegistryService.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from app.domain.entities import WalletProvider
from app.domain.services import PolicyEnforcer, LinkTokenService, WalletRegistryService
from app.composition import build_in_memory_services


class TestPolicyEnforcer:
    """Test suite for PolicyEnforcer service."""

    @pytest.fixture
    def policy_enforcer(self):
        """Create PolicyEnforcer instance."""
        return PolicyEnforcer()

    def test_initialization(self, policy_enforcer):
        """Test PolicyEnforcer initialization."""
        assert policy_enforcer.token_expiry_minutes == 60
        assert policy_enforcer.token_length == 32

    def test_generate_secure_token_uniqueness(self, policy_enforcer):
        """Test that generated tokens are unique."""
        tokens = [policy_enforcer.generate_secure_token() for _ in range(100)]
        
        # All tokens should be unique
        assert len(set(tokens)) == 100

    def test_generate_secure_token_length(self, policy_enforcer):
        """Test that generated tokens have reasonable length."""
        token = policy_enforcer.generate_secure_token()
        
        # URL-safe base64 tokens should have reasonable length
        assert len(token) > 30
        assert isinstance(token, str)

    def test_generate_secure_token_url_safe(self, policy_enforcer):
        """Test that generated tokens are URL-safe."""
        token = policy_enforcer.generate_secure_token()
        
        # Should only contain URL-safe characters
        import string
        url_safe_chars = string.ascii_letters + string.digits + '-_'
        assert all(c in url_safe_chars for c in token)

    def test_calculate_expiry(self, policy_enforcer):
        """Test expiry calculation."""
        before = datetime.utcnow()
        expiry = policy_enforcer.calculate_expiry()
        after = datetime.utcnow()
        
        # Expiry should be in the future
        assert expiry > before
        assert expiry > after
        
        # Expiry should be approximately 60 minutes from now
        expected_min = before + timedelta(minutes=59)
        expected_max = after + timedelta(minutes=61)
        assert expected_min <= expiry <= expected_max

    def test_is_token_expired_future_date(self, policy_enforcer):
        """Test token expiry check with future date."""
        future_date = datetime.utcnow() + timedelta(hours=2)
        
        assert policy_enforcer.is_token_expired(future_date) is False

    def test_is_token_expired_past_date(self, policy_enforcer):
        """Test token expiry check with past date."""
        past_date = datetime.utcnow() - timedelta(hours=2)
        
        assert policy_enforcer.is_token_expired(past_date) is True

    def test_is_token_expired_just_expired(self, policy_enforcer):
        """Test token expiry check with just expired date."""
        just_expired = datetime.utcnow() - timedelta(seconds=1)
        
        assert policy_enforcer.is_token_expired(just_expired) is True

    def test_is_token_expired_just_not_expired(self, policy_enforcer):
        """Test token expiry check with date just in future."""
        just_future = datetime.utcnow() + timedelta(seconds=1)
        
        assert policy_enforcer.is_token_expired(just_future) is False


class TestLinkTokenService:
    """Test suite for LinkTokenService."""

    @pytest.fixture
    def services(self):
        """Build in-memory services."""
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
    async def test_create_link_token_success(self, link_token_service, audit_port):
        """Test successful link token creation."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        link_token = await link_token_service.create_link_token(user_id, provider)
        
        assert link_token.user_id == user_id
        assert link_token.provider == provider
        assert link_token.token != ""
        assert link_token.is_consumed is False
        assert link_token.expires_at > datetime.utcnow()
        
        # Verify audit was recorded
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "create_link_token"

    @pytest.mark.asyncio
    async def test_create_link_token_different_providers(self, link_token_service):
        """Test creating tokens for different providers."""
        user_id = uuid4()
        
        token_fincra = await link_token_service.create_link_token(user_id, WalletProvider.FINCRA)
        token_paystack = await link_token_service.create_link_token(user_id, WalletProvider.PAYSTACK)
        token_flutter = await link_token_service.create_link_token(user_id, WalletProvider.FLUTTERWAVE)
        
        assert token_fincra.provider == WalletProvider.FINCRA
        assert token_paystack.provider == WalletProvider.PAYSTACK
        assert token_flutter.provider == WalletProvider.FLUTTERWAVE
        
        # All tokens should be different
        assert token_fincra.token != token_paystack.token
        assert token_fincra.token != token_flutter.token

    @pytest.mark.asyncio
    async def test_create_multiple_link_tokens(self, link_token_service):
        """Test creating multiple link tokens."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        tokens = []
        for _ in range(5):
            token = await link_token_service.create_link_token(user_id, provider)
            tokens.append(token)
        
        # All tokens should be unique
        token_strings = [t.token for t in tokens]
        assert len(set(token_strings)) == 5

    @pytest.mark.asyncio
    async def test_consume_valid_link_token(self, link_token_service, audit_port):
        """Test consuming a valid link token."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        created_token = await link_token_service.create_link_token(user_id, provider)
        consumed_token = await link_token_service.consume_link_token(created_token.token)
        
        assert consumed_token is not None
        assert consumed_token.id == created_token.id
        assert consumed_token.is_consumed is True
        assert consumed_token.consumed_at is not None
        assert consumed_token.consumed_at > created_token.created_at
        
        # Verify audit events
        events = audit_port.get_events()
        assert len(events) == 2
        assert events[1]["action"] == "consume_link_token"

    @pytest.mark.asyncio
    async def test_consume_nonexistent_token(self, link_token_service):
        """Test consuming a token that doesn't exist."""
        result = await link_token_service.consume_link_token("nonexistent-token-12345")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_consume_already_consumed_token(self, link_token_service):
        """Test consuming a token that's already been consumed."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        created_token = await link_token_service.create_link_token(user_id, provider)
        await link_token_service.consume_link_token(created_token.token)
        
        # Try to consume again
        second_result = await link_token_service.consume_link_token(created_token.token)
        
        assert second_result is None

    @pytest.mark.asyncio
    async def test_consume_expired_token(self, services):
        """Test consuming an expired token."""
        link_token_service = services["link_token_service"]
        link_token_port = services["link_token_port"]
        
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        
        # Create token
        created_token = await link_token_service.create_link_token(user_id, provider)
        
        # Manually expire it
        token_from_repo = await link_token_port.find_by_token(created_token.token)
        token_from_repo.expires_at = datetime.utcnow() - timedelta(hours=1)
        await link_token_port.create(token_from_repo)
        
        # Try to consume expired token
        result = await link_token_service.consume_link_token(created_token.token)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_audit_logging_on_create(self, link_token_service, audit_port):
        """Test that audit events are logged on token creation."""
        user_id = uuid4()
        
        await link_token_service.create_link_token(user_id, WalletProvider.FINCRA)
        
        events = audit_port.get_events()
        assert len(events) == 1
        
        event = events[0]
        assert event["action"] == "create_link_token"
        assert event["user_id"] == user_id
        assert event["resource_type"] == "link_token"
        assert "provider" in event["details"]
        assert "expires_at" in event["details"]

    @pytest.mark.asyncio
    async def test_audit_logging_on_consume(self, link_token_service, audit_port):
        """Test that audit events are logged on token consumption."""
        user_id = uuid4()
        
        created_token = await link_token_service.create_link_token(user_id, WalletProvider.FINCRA)
        await link_token_service.consume_link_token(created_token.token)
        
        events = audit_port.get_events()
        assert len(events) == 2
        
        consume_event = events[1]
        assert consume_event["action"] == "consume_link_token"
        assert consume_event["user_id"] == user_id
        assert "consumed_at" in consume_event["details"]


class TestWalletRegistryService:
    """Test suite for WalletRegistryService."""

    @pytest.fixture
    def services(self):
        """Build in-memory services."""
        return build_in_memory_services()

    @pytest.fixture
    def wallet_registry_service(self, services):
        """Get wallet registry service."""
        return services["wallet_registry_service"]

    @pytest.fixture
    def audit_port(self, services):
        """Get audit port."""
        return services["audit_port"]

    @pytest.mark.asyncio
    async def test_register_wallet_success(self, wallet_registry_service, audit_port):
        """Test successful wallet registration."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_123456"
        
        wallet = await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id
        )
        
        assert wallet.user_id == user_id
        assert wallet.provider == provider
        assert wallet.provider_account_id == provider_account_id
        assert wallet.is_active is True
        
        # Verify audit event
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "register_wallet"

    @pytest.mark.asyncio
    async def test_register_wallet_with_customer_id(self, wallet_registry_service):
        """Test registering wallet with provider customer ID."""
        user_id = uuid4()
        provider = WalletProvider.PAYSTACK
        provider_account_id = "acc_123"
        provider_customer_id = "cust_456"
        
        wallet = await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id, provider_customer_id
        )
        
        assert wallet.provider_customer_id == provider_customer_id

    @pytest.mark.asyncio
    async def test_register_wallet_with_metadata(self, wallet_registry_service):
        """Test registering wallet with metadata."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_789"
        metadata = {"account_type": "business", "verified": True}
        
        wallet = await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id, metadata=metadata
        )
        
        assert wallet.metadata == metadata

    @pytest.mark.asyncio
    async def test_register_wallet_idempotency(self, wallet_registry_service):
        """Test wallet registration is idempotent."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_idempotent"
        
        # Register wallet first time
        wallet1 = await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id
        )
        
        # Register same wallet again
        wallet2 = await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id
        )
        
        # Should return the same wallet (idempotent)
        assert wallet1.id == wallet2.id
        assert wallet1.provider_account_id == wallet2.provider_account_id

    @pytest.mark.asyncio
    async def test_register_wallet_multiple_providers(self, wallet_registry_service):
        """Test registering wallets with different providers."""
        user_id = uuid4()
        
        wallet_fincra = await wallet_registry_service.register_wallet(
            user_id, WalletProvider.FINCRA, "fincra_acc_123"
        )
        wallet_paystack = await wallet_registry_service.register_wallet(
            user_id, WalletProvider.PAYSTACK, "paystack_acc_456"
        )
        
        assert wallet_fincra.provider == WalletProvider.FINCRA
        assert wallet_paystack.provider == WalletProvider.PAYSTACK
        assert wallet_fincra.id != wallet_paystack.id

    @pytest.mark.asyncio
    async def test_register_wallet_different_users(self, wallet_registry_service):
        """Test registering wallets for different users."""
        user1_id = uuid4()
        user2_id = uuid4()
        provider = WalletProvider.FINCRA
        
        wallet1 = await wallet_registry_service.register_wallet(
            user1_id, provider, "acc_user1"
        )
        wallet2 = await wallet_registry_service.register_wallet(
            user2_id, provider, "acc_user2"
        )
        
        assert wallet1.user_id == user1_id
        assert wallet2.user_id == user2_id
        assert wallet1.id != wallet2.id

    @pytest.mark.asyncio
    async def test_audit_logging_on_register(self, wallet_registry_service, audit_port):
        """Test audit logging on wallet registration."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_audit_test"
        
        await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id
        )
        
        events = audit_port.get_events()
        assert len(events) == 1
        
        event = events[0]
        assert event["action"] == "register_wallet"
        assert event["user_id"] == user_id
        assert event["resource_type"] == "wallet_registry"
        assert event["details"]["provider"] == provider.value
        assert event["details"]["provider_account_id"] == provider_account_id

    @pytest.mark.asyncio
    async def test_no_audit_on_idempotent_registration(self, wallet_registry_service, audit_port):
        """Test no new audit event on idempotent registration."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_account_id = "acc_idempotent_audit"
        
        # First registration
        await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id
        )
        
        # Second registration (idempotent)
        await wallet_registry_service.register_wallet(
            user_id, provider, provider_account_id
        )
        
        # Should only have one audit event (first registration)
        events = audit_port.get_events()
        assert len(events) == 1
