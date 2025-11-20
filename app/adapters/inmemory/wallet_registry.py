"""In-memory implementation of WalletRegistryPort for testing."""

from typing import Dict, Optional, List
import uuid
from datetime import datetime

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.ports.wallet_registry import WalletRegistryPort


class InMemoryWalletRegistry(WalletRegistryPort):
    """In-memory implementation of the wallet registry."""

    def __init__(self):
        """Initialize the in-memory wallet registry."""
        self._entries: Dict[str, WalletRegistryEntry] = {}
        self._user_provider_index: Dict[tuple, str] = {}

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
        entry_id = str(uuid.uuid4())
        entry = WalletRegistryEntry(
            id=entry_id,
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
            access_token=access_token,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._entries[entry_id] = entry
        self._user_provider_index[(user_id, provider)] = entry_id
        return entry

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
        entry_id = self._user_provider_index.get((user_id, provider))
        if entry_id:
            return self._entries.get(entry_id)
        return None

    async def get_all_for_user(self, user_id: str) -> List[WalletRegistryEntry]:
        """Get all wallet registry entries for a user.

        Args:
            user_id: The user's unique identifier.

        Returns:
            A list of WalletRegistryEntry entities.
        """
        return [entry for entry in self._entries.values() if entry.user_id == user_id]
