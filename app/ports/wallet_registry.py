"""
Port: WalletRegistryPort
"""
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class WalletRegistryRecord:
    def __init__(self, id: int, provider: str, provider_wallet_id: str, bot_user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None):
        self.id = id
        self.provider = provider
        self.provider_wallet_id = provider_wallet_id
        self.bot_user_id = bot_user_id
        self.metadata = metadata or {}
        self.idempotency_key = idempotency_key


class WalletRegistryPort(ABC):
    @abstractmethod
    def create(self, provider: str, provider_wallet_id: str, bot_user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None) -> WalletRegistryRecord:
        """Persist a new wallet registry row. Should raise on DB error (unique constraint)"""
        raise NotImplementedError

    @abstractmethod
    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[WalletRegistryRecord]:
        """Return existing registry by idempotency key, or None"""
        raise NotImplementedError

    @abstractmethod
    def get_by_provider(self, provider: str, provider_wallet_id: str) -> Optional[WalletRegistryRecord]:
        """Return existing registry by provider+provider_wallet_id, or None"""
        raise NotImplementedError
