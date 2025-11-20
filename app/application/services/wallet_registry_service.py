"""
WalletRegistryService - enforces idempotency and race resolution
"""
from typing import Optional, Dict, Any
import logging

from app.ports.wallet_registry import WalletRegistryPort, WalletRegistryRecord

logger = logging.getLogger(__name__)


class WalletRegistryService:
    def __init__(self, wallet_repo: WalletRegistryPort):
        self.wallet_repo = wallet_repo

    def register(self, provider: str, provider_wallet_id: str, bot_user_id: Optional[str], metadata: Optional[Dict[str, Any]] = None, idempotency_key: Optional[str] = None) -> WalletRegistryRecord:
        """
        Idempotent wallet registration:
        - If idempotency_key provided and exists, return existing record.
        - Else attempt to create; if a unique constraint race occurs, fetch and return existing.
        """
        # 1) If idempotency key is provided, try to fetch existing
        if idempotency_key:
            existing = self.wallet_repo.get_by_idempotency_key(idempotency_key)
            if existing:
                logger.debug("Found existing registry by idempotency_key=%s -> id=%s", idempotency_key, existing.id)
                return existing

        # 2) Also check provider+provider_wallet_id to avoid duplicates created without idempotency
        existing_by_provider = self.wallet_repo.get_by_provider(provider, provider_wallet_id)
        if existing_by_provider:
            logger.debug("Found existing registry by provider %s/%s -> id=%s", provider, provider_wallet_id, existing_by_provider.id)
            return existing_by_provider

        # 3) Attempt create (SQL adapter should raise on unique violation which we catch)
        try:
            created = self.wallet_repo.create(provider=provider, provider_wallet_id=provider_wallet_id, bot_user_id=bot_user_id, metadata=metadata, idempotency_key=idempotency_key)
            logger.info("Created wallet registry id=%s for provider=%s provider_wallet_id=%s", created.id, provider, provider_wallet_id)
            return created
        except Exception as exc:
            # Handle unique constraint race: fetch existing by idempotency or provider fields and return
            logger.warning("Create failed (possible race), trying to resolve existing: %s", exc)
            if idempotency_key:
                existing = self.wallet_repo.get_by_idempotency_key(idempotency_key)
                if existing:
                    return existing
            existing = self.wallet_repo.get_by_provider(provider, provider_wallet_id)
            if existing:
                return existing
            # Unexpected error; re-raise
            raise
