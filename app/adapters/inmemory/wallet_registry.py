"""
In-memory WalletRegistry adapter for tests
"""
from typing import Optional, Dict, Any, List
import threading

from app.ports.wallet_registry import WalletRegistryPort, WalletRegistryRecord


class InMemoryWalletRegistryAdapter(WalletRegistryPort):
    def __init__(self):
        self._lock = threading.Lock()
        self._rows: List[Dict[str, Any]] = []
        self._next_id = 1

    def create(self, provider: str, provider_wallet_id: str, bot_user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None) -> WalletRegistryRecord:
        with self._lock:
            # simulate unique constraints
            for r in self._rows:
                if idempotency_key and r.get("idempotency_key") == idempotency_key:
                    raise Exception("unique_violation_idempotency")
                if r["provider"] == provider and r["provider_wallet_id"] == provider_wallet_id:
                    raise Exception("unique_violation_provider")

            row = {
                "id": self._next_id,
                "provider": provider,
                "provider_wallet_id": provider_wallet_id,
                "bot_user_id": bot_user_id,
                "metadata": metadata or {},
                "idempotency_key": idempotency_key,
            }
            self._rows.append(row)
            self._next_id += 1
            return WalletRegistryRecord(**row)

    def get_by_idempotency_key(self, idempotency_key: str) -> Optional[WalletRegistryRecord]:
        with self._lock:
            for r in self._rows:
                if r.get("idempotency_key") == idempotency_key:
                    return WalletRegistryRecord(**r)
        return None

    def get_by_provider(self, provider: str, provider_wallet_id: str) -> Optional[WalletRegistryRecord]:
        with self._lock:
            for r in self._rows:
                if r["provider"] == provider and r["provider_wallet_id"] == provider_wallet_id:
                    return WalletRegistryRecord(**r)
        return None
