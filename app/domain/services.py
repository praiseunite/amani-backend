"""Domain services for the Amani backend.

This module contains business logic that doesn't belong to a single entity.
"""

from typing import Optional
import uuid
from datetime import datetime, timedelta

from app.domain.entities import LinkToken, LinkTokenStatus, WalletProvider, User
from app.ports.link_token import LinkTokenPort
from app.ports.audit import AuditPort
from app.ports.user_repository import UserRepositoryPort


class PolicyEnforcer:
    """Enforces business policies and rules."""

    def can_create_link_token(self, user: User) -> bool:
        """Check if a user can create a link token.

        Args:
            user: The User entity.

        Returns:
            True if the user can create a link token, False otherwise.
        """
        # Basic policy: all authenticated users can create link tokens
        return user is not None

    def get_token_expiration_time(self) -> datetime:
        """Get the expiration time for a new token.

        Returns:
            The expiration datetime for a new token.
        """
        # Tokens expire in 1 hour
        return datetime.utcnow() + timedelta(hours=1)


class LinkTokenService:
    """Service for managing link tokens."""

    def __init__(
        self,
        link_token_port: LinkTokenPort,
        user_repository: UserRepositoryPort,
        audit_port: AuditPort,
        policy_enforcer: Optional[PolicyEnforcer] = None,
    ):
        """Initialize the LinkTokenService.

        Args:
            link_token_port: Port for link token operations.
            user_repository: Port for user repository operations.
            audit_port: Port for audit logging.
            policy_enforcer: Optional policy enforcer (creates default if None).
        """
        self.link_token_port = link_token_port
        self.user_repository = user_repository
        self.audit_port = audit_port
        self.policy_enforcer = policy_enforcer or PolicyEnforcer()

    async def create_link_token(self, user_id: str, provider: WalletProvider) -> LinkToken:
        """Create a new link token for a user.

        Args:
            user_id: The user's unique identifier.
            provider: The wallet provider.

        Returns:
            The created LinkToken entity.

        Raises:
            ValueError: If the user is not found or not authorized.
        """
        # Find the user
        user = await self.user_repository.find_by_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # Check policy
        if not self.policy_enforcer.can_create_link_token(user):
            raise ValueError(f"User not authorized to create link token: {user_id}")

        # Generate a unique token
        token_string = str(uuid.uuid4())

        # Create the link token
        link_token = await self.link_token_port.create(user_id, provider, token_string)

        # Audit the event
        await self.audit_port.record(
            event_type="link_token_created",
            user_id=user_id,
            details={
                "token_id": link_token.id,
                "provider": provider.value,
            },
        )

        return link_token

    async def consume_link_token(self, token_string: str) -> LinkToken:
        """Consume a link token.

        Args:
            token_string: The token string to consume.

        Returns:
            The consumed LinkToken entity.

        Raises:
            ValueError: If the token is not found, expired, or already consumed.
        """
        # Find the token
        link_token = await self.link_token_port.find_by_token(token_string)
        if not link_token:
            raise ValueError("Link token not found")

        # Check if already consumed
        if link_token.status == LinkTokenStatus.CONSUMED:
            raise ValueError("Link token already consumed")

        # Check if expired
        if link_token.expires_at and link_token.expires_at < datetime.utcnow():
            raise ValueError("Link token expired")

        # Consume the token
        consumed_token = await self.link_token_port.consume(link_token.id)

        # Audit the event
        await self.audit_port.record(
            event_type="link_token_consumed",
            user_id=link_token.user_id,
            details={
                "token_id": link_token.id,
                "provider": link_token.provider.value,
            },
        )

        return consumed_token
