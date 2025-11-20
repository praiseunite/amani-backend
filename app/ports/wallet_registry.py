"""Wallet registry port interface."""

from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities import WalletRegistryEntry, WalletProvider


class WalletRegistryPort(ABC):
    """Port interface for wallet registry operations."""

    @abstractmethod
    async def register(
        self,
        user_id: str,
        provider: WalletProvider,
        provider_account_id: str,
        access_token: str,
    ) -> WalletRegistryEntry:
        """Register a new wallet entry.

        Args:
            user_id: The user's unique identifier.
            provider: The wallet provider.
            provider_account_id: The provider's account identifier.
            access_token: The access token for the wallet.

        Returns:
            The created WalletRegistryEntry entity.
        """
        pass

    @abstractmethod
    async def get_by_provider(
        self, user_id: str, provider: WalletProvider
    ) -> Optional[WalletRegistryEntry]:
        """Get a wallet registry entry by user ID and provider.

        Args:
            user_id: The user's unique identifier.
            provider: The wallet provider.

        Returns:
            The WalletRegistryEntry entity if found, None otherwise.
        """
        pass

    @abstractmethod
    async def get_all_for_user(self, user_id: str) -> List[WalletRegistryEntry]:
        """Get all wallet registry entries for a user.

        Args:
            user_id: The user's unique identifier.

        Returns:
            A list of WalletRegistryEntry entities.
        """
        pass
