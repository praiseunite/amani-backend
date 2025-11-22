"""Domain services - business logic using ports."""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from app.domain.entities import LinkToken, WalletProvider, WalletRegistryEntry
from app.ports.audit import AuditPort
from app.ports.link_token import LinkTokenPort
from app.ports.wallet_registry import WalletRegistryPort


class PolicyEnforcer:
    """Enforces business policies."""

    def __init__(self):
        """Initialize policy enforcer."""
        self.token_expiry_minutes = 60
        self.token_length = 32

    def generate_secure_token(self) -> str:
        """Generate a secure random token.

        Returns:
            A secure random token string
        """
        return secrets.token_urlsafe(self.token_length)

    def calculate_expiry(self) -> datetime:
        """Calculate token expiry time.

        Returns:
            Expiry datetime
        """
        return datetime.utcnow() + timedelta(minutes=self.token_expiry_minutes)

    def is_token_expired(self, expires_at: datetime) -> bool:
        """Check if a token has expired.

        Args:
            expires_at: The expiry datetime

        Returns:
            True if expired, False otherwise
        """
        return datetime.utcnow() > expires_at


class LinkTokenService:
    """Service for managing link tokens."""

    def __init__(
        self,
        link_token_port: LinkTokenPort,
        audit_port: AuditPort,
        policy_enforcer: PolicyEnforcer,
    ):
        """Initialize link token service.

        Args:
            link_token_port: Port for link token operations
            audit_port: Port for audit operations
            policy_enforcer: Policy enforcement service
        """
        self.link_token_port = link_token_port
        self.audit_port = audit_port
        self.policy_enforcer = policy_enforcer

    async def create_link_token(self, user_id: UUID, provider: WalletProvider) -> LinkToken:
        """Create a new link token for a user.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider

        Returns:
            The created link token
        """
        token_str = self.policy_enforcer.generate_secure_token()
        expires_at = self.policy_enforcer.calculate_expiry()

        link_token = LinkToken(
            user_id=user_id,
            token=token_str,
            provider=provider,
            expires_at=expires_at,
            is_consumed=False,
        )

        saved_token = await self.link_token_port.create(link_token)

        await self.audit_port.record(
            user_id=user_id,
            action="create_link_token",
            resource_type="link_token",
            resource_id=str(saved_token.id),
            details={
                "provider": provider.value,
                "expires_at": expires_at.isoformat(),
            },
        )

        return saved_token

    async def consume_link_token(self, token: str) -> Optional[LinkToken]:
        """Consume a link token.

        Args:
            token: The token string to consume

        Returns:
            The consumed link token if valid, None otherwise
        """
        link_token = await self.link_token_port.find_by_token(token)

        if link_token is None:
            return None

        # Verify token hasn't expired
        if self.policy_enforcer.is_token_expired(link_token.expires_at):
            return None

        # Verify token hasn't been consumed
        if link_token.is_consumed:
            return None

        # Mark as consumed
        consumed_token = await self.link_token_port.mark_consumed(link_token)

        await self.audit_port.record(
            user_id=link_token.user_id,
            action="consume_link_token",
            resource_type="link_token",
            resource_id=str(link_token.id),
            details={
                "provider": link_token.provider.value,
                "consumed_at": datetime.utcnow().isoformat(),
            },
        )

        return consumed_token


class WalletRegistryService:
    """Service for managing wallet registry."""

    def __init__(
        self,
        wallet_registry_port: WalletRegistryPort,
        audit_port: AuditPort,
    ):
        """Initialize wallet registry service.

        Args:
            wallet_registry_port: Port for wallet registry operations
            audit_port: Port for audit operations
        """
        self.wallet_registry_port = wallet_registry_port
        self.audit_port = audit_port

    async def register_wallet(
        self,
        user_id: UUID,
        provider: WalletProvider,
        provider_account_id: str,
        provider_customer_id: Optional[str] = None,
        metadata: dict = None,
    ) -> WalletRegistryEntry:
        """Register a wallet for a user (idempotent).

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider
            provider_account_id: The provider account ID
            provider_customer_id: Optional provider customer ID
            metadata: Optional metadata

        Returns:
            The registered wallet entry
        """
        # Check if wallet already exists
        existing_wallet = await self.wallet_registry_port.get_by_provider(user_id, provider)

        if existing_wallet is not None:
            # Return existing wallet (idempotent)
            return existing_wallet

        # Create new wallet entry
        wallet_entry = WalletRegistryEntry(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_customer_id=provider_customer_id,
            metadata=metadata or {},
            is_active=True,
        )

        registered_wallet = await self.wallet_registry_port.register(wallet_entry)

        await self.audit_port.record(
            user_id=user_id,
            action="register_wallet",
            resource_type="wallet_registry",
            resource_id=str(registered_wallet.id),
            details={
                "provider": provider.value,
                "provider_account_id": provider_account_id,
            },
        )

        return registered_wallet
