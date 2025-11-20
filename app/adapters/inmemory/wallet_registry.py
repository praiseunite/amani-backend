"""In-memory wallet registry implementation for testing."""

from typing import List, Optional
from uuid import UUID

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.ports.wallet_registry import WalletRegistryPort


class InMemoryWalletRegistry(WalletRegistryPort):
    """In-memory implementation of wallet registry."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._wallets: List[WalletRegistryEntry] = []

    async def register(self, entry: WalletRegistryEntry) -> WalletRegistryEntry:
        """Register a new wallet.

        Args:
            entry: The wallet registry entry to register

        Returns:
            The registered wallet entry
        """
        self._wallets.append(entry)
        return entry

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
        for wallet in self._wallets:
            if wallet.user_id == user_id and wallet.provider == provider:
                return wallet
        return None
