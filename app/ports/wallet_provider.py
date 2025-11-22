"""Wallet provider adapter - interface for fetching wallet balances from providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from app.domain.entities import WalletProvider


class WalletProviderPort(ABC):
    """Port for wallet provider operations."""

    @abstractmethod
    async def fetch_balance(
        self, wallet_id: UUID, provider: WalletProvider, provider_account_id: str
    ) -> Dict[str, Any]:
        """Fetch current balance from wallet provider.

        Args:
            wallet_id: The wallet's unique identifier
            provider: The wallet provider
            provider_account_id: The provider's account/wallet ID

        Returns:
            Dictionary with balance information:
            {
                "balance": float,
                "currency": str,
                "external_balance_id": str (optional),
                "metadata": dict (optional)
            }
        """
        pass
