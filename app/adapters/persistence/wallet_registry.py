"""SQLAlchemy-based WalletRegistry adapter."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import WalletRegistryEntry, WalletProvider
from app.models.wallet_registry import WalletRegistry as WalletRegistryModel
from app.ports.wallet_registry import WalletRegistryPort


class SQLWalletRegistry(WalletRegistryPort):
    """SQLAlchemy implementation of WalletRegistryPort."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def register_wallet(
        self,
        user_id: UUID,
        provider: WalletProvider,
        provider_account_id: str,
        provider_customer_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> WalletRegistryEntry:
        """Register a wallet idempotently.

        Uses ON CONFLICT DO NOTHING or similar for idempotency based on unique constraints.
        """
        # Check if already exists
        stmt = select(WalletRegistryModel).where(
            WalletRegistryModel.user_id == user_id,
            WalletRegistryModel.provider == provider,
            WalletRegistryModel.provider_account_id == provider_account_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # Return existing entry
            return WalletRegistryEntry(
                id=existing.external_id,
                user_id=existing.user_id,
                provider=existing.provider,
                provider_account_id=existing.provider_account_id,
                provider_customer_id=existing.provider_customer_id,
                metadata=existing.extra_data or {},
                is_active=existing.is_active,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
            )

        # Create new entry
        new_entry = WalletRegistryModel(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
            provider_customer_id=provider_customer_id,
            extra_data=metadata or {},
        )
        self.session.add(new_entry)
        await self.session.commit()  # Commit to trigger insert
        await self.session.refresh(new_entry)

        return WalletRegistryEntry(
            id=new_entry.external_id,
            user_id=new_entry.user_id,
            provider=new_entry.provider,
            provider_account_id=new_entry.provider_account_id,
            provider_customer_id=new_entry.provider_customer_id,
            metadata=new_entry.extra_data or {},
            is_active=new_entry.is_active,
            created_at=new_entry.created_at,
            updated_at=new_entry.updated_at,
        )

    async def get_wallet(self, wallet_id: UUID) -> Optional[WalletRegistryEntry]:
        """Get a wallet by external ID."""
        stmt = select(WalletRegistryModel).where(WalletRegistryModel.external_id == wallet_id)
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry:
            return WalletRegistryEntry(
                id=entry.external_id,
                user_id=entry.user_id,
                provider=entry.provider,
                provider_account_id=entry.provider_account_id,
                provider_customer_id=entry.provider_customer_id,
                metadata=entry.extra_data or {},
                is_active=entry.is_active,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
        return None

    async def list_wallets_for_user(self, user_id: UUID) -> List[WalletRegistryEntry]:
        """List wallets for a user."""
        stmt = select(WalletRegistryModel).where(WalletRegistryModel.user_id == user_id)
        result = await self.session.execute(stmt)
        entries = result.scalars().all()

        return [
            WalletRegistryEntry(
                id=entry.external_id,
                user_id=entry.user_id,
                provider=entry.provider,
                provider_account_id=entry.provider_account_id,
                provider_customer_id=entry.provider_customer_id,
                metadata=entry.extra_data or {},
                is_active=entry.is_active,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
            for entry in entries
        ]

    async def deactivate_wallet(self, wallet_id: UUID) -> bool:
        """Deactivate a wallet."""
        stmt = select(WalletRegistryModel).where(WalletRegistryModel.external_id == wallet_id)
        result = await self.session.execute(stmt)
        entry = result.scalar_one_or_none()

        if entry:
            entry.is_active = False
            await self.session.commit()
            return True
        return False
