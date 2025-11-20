"""Wallet registry port - interface for wallet registry operations."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.entities import WalletRegistryEntry, WalletProvider


class WalletRegistryPort(ABC):
    """Port for wallet registry operations."""

    @abstractmethod
    async def register(self, entry: WalletRegistryEntry) -> WalletRegistryEntry:
        """Register a new wallet.

        Args:
            entry: The wallet registry entry to register

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
