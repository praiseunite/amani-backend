"""In-memory wallet registry implementation for testing."""

from typing import Dict, List, Optional
from uuid import UUID

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.ports.wallet_registry import WalletRegistryPort
from app.errors import DuplicateEntryError


class InMemoryWalletRegistry(WalletRegistryPort):
    """In-memory implementation of wallet registry."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._wallets: List[WalletRegistryEntry] = []
        self._idempotency_keys: Dict[str, WalletRegistryEntry] = {}

    async def register(
        self, entry: WalletRegistryEntry, idempotency_key: Optional[str] = None
    ) -> WalletRegistryEntry:
        """Register a new wallet.

        Args:
            entry: The wallet registry entry to register
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            The registered wallet entry

        Raises:
            DuplicateEntryError: On duplicate wallet registration
        """
        # Check for duplicate provider + provider_wallet_id
        existing = await self.get_by_provider_wallet(
            entry.user_id, entry.provider, entry.provider_account_id
        )
        if existing:
            raise DuplicateEntryError("Duplicate wallet registration")

        # Check for duplicate idempotency_key
        if idempotency_key and idempotency_key in self._idempotency_keys:
            raise DuplicateEntryError("Duplicate idempotency key")

        self._wallets.append(entry)
        if idempotency_key:
            self._idempotency_keys[idempotency_key] = entry
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

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> Optional[WalletRegistryEntry]:
        """Get wallet by idempotency key.

        Args:
            idempotency_key: The idempotency key

        Returns:
            Wallet registry entry if found, None otherwise
        """
        return self._idempotency_keys.get(idempotency_key)

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
        for wallet in self._wallets:
            if (
                wallet.user_id == user_id
                and wallet.provider == provider
                and wallet.provider_account_id == provider_wallet_id
            ):
                return wallet
        return None
