"""Integration tests for wallet registry concurrency.

These tests require a test database and are gated by TEST_DATABASE_URL environment variable.
Run `alembic upgrade head` before running these tests.
"""

import os
import asyncio
import pytest
from uuid import uuid4
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.domain.entities import WalletProvider
from app.application.services.wallet_registry_service import WalletRegistryService
from app.adapters.sql.wallet_registry import SQLWalletRegistry
from app.adapters.inmemory.audit import InMemoryAudit


# Skip all tests if TEST_DATABASE_URL not set
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set - integration tests require database"
)


@pytest.fixture(scope="module")
async def db_engine():
    """Create test database engine."""
    database_url = os.getenv("TEST_DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="module")
async def db_metadata():
    """Create metadata for table definitions."""
    return MetaData()


@pytest.fixture
async def db_session(db_engine):
    """Create a new database session for each test."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def wallet_registry_port(db_session, db_metadata):
    """Create SQL wallet registry port."""
    return SQLWalletRegistry(session=db_session, metadata=db_metadata)


@pytest.fixture
async def service(wallet_registry_port):
    """Create wallet registry service with SQL adapter."""
    audit_port = InMemoryAudit()
    return WalletRegistryService(
        wallet_registry_port=wallet_registry_port,
        audit_port=audit_port,
    )


class TestWalletRegistryConcurrency:
    """Test suite for concurrent wallet registration."""

    @pytest.mark.asyncio
    async def test_concurrent_registration_same_idempotency_key(self, db_engine, db_metadata):
        """Test concurrent registrations with same idempotency_key resolve correctly."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = f"wallet_{uuid4()}"
        idempotency_key = f"idem_{uuid4()}"

        async def register_wallet():
            """Register wallet in separate session."""
            async_session = async_sessionmaker(
                db_engine, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                wallet_port = SQLWalletRegistry(session=session, metadata=db_metadata)
                audit_port = InMemoryAudit()
                service = WalletRegistryService(
                    wallet_registry_port=wallet_port,
                    audit_port=audit_port,
                )
                try:
                    result = await service.register(
                        user_id=user_id,
                        provider=provider,
                        provider_wallet_id=provider_wallet_id,
                        idempotency_key=idempotency_key,
                    )
                    return result
                except Exception:
                    # Expected for race condition losers
                    return None

        # Launch concurrent registrations
        tasks = [register_wallet() for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # Filter out None results (race condition losers)
        successful_results = [r for r in results if r is not None]

        # At least one should succeed
        assert len(successful_results) >= 1

        # All successful results should have same ID (same wallet)
        wallet_ids = {r.id for r in successful_results}
        assert len(wallet_ids) == 1

    @pytest.mark.asyncio
    async def test_concurrent_registration_same_provider_wallet(self, db_engine, db_metadata):
        """Test concurrent registrations with same provider+wallet resolve correctly."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = f"wallet_{uuid4()}"

        async def register_wallet(idx):
            """Register wallet in separate session."""
            async_session = async_sessionmaker(
                db_engine, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                wallet_port = SQLWalletRegistry(session=session, metadata=db_metadata)
                audit_port = InMemoryAudit()
                service = WalletRegistryService(
                    wallet_registry_port=wallet_port,
                    audit_port=audit_port,
                )
                try:
                    result = await service.register(
                        user_id=user_id,
                        provider=provider,
                        provider_wallet_id=provider_wallet_id,
                        idempotency_key=f"idem_{idx}",  # Different keys
                    )
                    return result
                except Exception:
                    # Expected for race condition losers
                    return None

        # Launch concurrent registrations with different idempotency keys
        tasks = [register_wallet(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        successful_results = [r for r in results if r is not None]

        # At least one should succeed
        assert len(successful_results) >= 1

        # All successful results should have same ID (same wallet)
        wallet_ids = {r.id for r in successful_results}
        assert len(wallet_ids) == 1

    @pytest.mark.asyncio
    async def test_concurrent_registration_different_wallets(self, db_engine, db_metadata):
        """Test concurrent registrations of different wallets succeed."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA

        async def register_wallet(idx):
            """Register unique wallet in separate session."""
            async_session = async_sessionmaker(
                db_engine, class_=AsyncSession, expire_on_commit=False
            )
            async with async_session() as session:
                wallet_port = SQLWalletRegistry(session=session, metadata=db_metadata)
                audit_port = InMemoryAudit()
                service = WalletRegistryService(
                    wallet_registry_port=wallet_port,
                    audit_port=audit_port,
                )
                result = await service.register(
                    user_id=user_id,
                    provider=provider,
                    provider_wallet_id=f"wallet_{uuid4()}",  # Unique per task
                    idempotency_key=f"idem_{idx}",
                )
                return result

        # Launch concurrent registrations of different wallets
        tasks = [register_wallet(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        assert all(r is not None for r in results)

        # All should have different IDs (different wallets)
        wallet_ids = {r.id for r in results}
        assert len(wallet_ids) == 5

    @pytest.mark.asyncio
    async def test_sequential_idempotent_requests(self, service):
        """Test sequential idempotent requests return same wallet."""
        user_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_wallet_id = f"wallet_{uuid4()}"
        idempotency_key = f"idem_{uuid4()}"

        # First registration
        result1 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Second registration (sequential)
        result2 = await service.register(
            user_id=user_id,
            provider=provider,
            provider_wallet_id=provider_wallet_id,
            idempotency_key=idempotency_key,
        )

        # Should return same wallet
        assert result1.id == result2.id
        assert result1.user_id == result2.user_id
        assert result1.provider_account_id == result2.provider_account_id
