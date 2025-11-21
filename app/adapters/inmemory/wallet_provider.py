"""In-memory (mock) wallet provider implementation for testing."""

from typing import Dict, Any
from uuid import UUID

from app.domain.entities import WalletProvider
from app.ports.wallet_provider import WalletProviderPort


class InMemoryWalletProvider(WalletProviderPort):
    """In-memory (mock) implementation of wallet provider."""

    def __init__(self):
        """Initialize mock provider with configurable balances."""
        # Mock balance data: {wallet_id: balance_data}
        self._balances: Dict[UUID, Dict[str, Any]] = {}
        self._fetch_count: Dict[UUID, int] = {}

    def set_balance(
        self,
        wallet_id: UUID,
        balance: float,
        currency: str = "USD",
        external_balance_id: str = None,
        metadata: dict = None,
    ):
        """Set mock balance for a wallet (for testing).

        Args:
            wallet_id: The wallet's unique identifier
            balance: The balance amount
            currency: The currency code
            external_balance_id: Optional external balance ID
            metadata: Optional metadata
        """
        self._balances[wallet_id] = {
            "balance": balance,
            "currency": currency,
            "external_balance_id": external_balance_id,
            "metadata": metadata or {},
        }

    async def fetch_balance(
        self, wallet_id: UUID, provider: WalletProvider, provider_account_id: str
    ) -> Dict[str, Any]:
        """Fetch current balance from wallet provider (mock).

        Args:
            wallet_id: The wallet's unique identifier
            provider: The wallet provider
            provider_account_id: The provider's account/wallet ID

        Returns:
            Dictionary with balance information
        """
        # Track fetch count for testing
        self._fetch_count[wallet_id] = self._fetch_count.get(wallet_id, 0) + 1

        # Return mock data or default
        if wallet_id in self._balances:
            return self._balances[wallet_id]
        
        # Default balance if not set
        return {
            "balance": 0.0,
            "currency": "USD",
            "external_balance_id": None,
            "metadata": {},
        }

    def get_fetch_count(self, wallet_id: UUID) -> int:
        """Get number of times balance was fetched for a wallet (for testing).

        Args:
            wallet_id: The wallet's unique identifier

        Returns:
            Number of fetch calls
        """
        return self._fetch_count.get(wallet_id, 0)
