"""Wallet registry port - interface for wallet registry operations."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import WalletProvider, WalletRegistryEntry


class WalletRegistryPort(ABC):
    """Port for wallet registry operations."""

    @abstractmethod
    async def register(
        self, entry: WalletRegistryEntry, idempotency_key: Optional[str] = None
    ) -> WalletRegistryEntry:
        """Register a new wallet.

        Args:
            entry: The wallet registry entry to register
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The registered wallet entry
        """
        pass

    @abstractmethod
    async def get_by_provider(
        self, user_id: UUID, provider: WalletProvider
    ) -> Optional[WalletRegistryEntry]:
        """Get wallet by user ID and provider.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider

        Returns:
            Wallet registry entry if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[WalletRegistryEntry]:
        """Get wallet by idempotency key.

        Args:
            idempotency_key: The idempotency key

        Returns:
            Wallet registry entry if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_provider_wallet(
        self, user_id: UUID, provider: WalletProvider, provider_wallet_id: str
    ) -> Optional[WalletRegistryEntry]:
        """Get wallet by user ID, provider, and provider wallet ID.

        Args:
            user_id: The user's unique identifier
            provider: The wallet provider
            provider_wallet_id: The provider's wallet/account ID

        Returns:
            Wallet registry entry if found, None otherwise
        """
        pass
