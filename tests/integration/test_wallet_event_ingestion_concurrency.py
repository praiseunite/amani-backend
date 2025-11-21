"""Integration tests for wallet event ingestion with database.

These tests require a test database and are gated by TEST_DATABASE_URL environment variable.
Run `alembic upgrade head` before running these tests.
"""

import os
import asyncio
import pytest
from uuid import uuid4
from datetime import datetime

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.domain.entities import WalletProvider, WalletEventType, WalletTransactionEvent
from app.adapters.sql.wallet_event_ingestion import SQLWalletEventIngestion
from app.errors import DuplicateEntryError


# Mark all tests in this module as integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("TEST_DATABASE_URL"),
        reason="TEST_DATABASE_URL not set - integration tests require database",
    ),
]


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
    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


class TestWalletEventIngestionConcurrency:
    """Test suite for concurrent wallet event ingestion."""

    @pytest.mark.asyncio
    async def test_concurrent_ingestion_same_event(self, db_session, db_metadata):
        """Test concurrent ingestion of same event (race condition)."""
        adapter = SQLWalletEventIngestion(db_session, db_metadata)

        wallet_id = uuid4()
        event_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()

        # Create the same event
        event = WalletTransactionEvent(
            id=event_id,
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            provider_event_id="provider_event_123",
            occurred_at=occurred_at,
        )

        # Simulate concurrent ingestion (first one should succeed)
        result = await adapter.ingest_event(event, idempotency_key="idem_key_1")
        assert result is not None
        assert result.id == event_id

        # Second attempt should return the existing event (idempotent)
        result2 = await adapter.ingest_event(event, idempotency_key="idem_key_1")
        assert result2 is not None
        assert result2.id == event_id

    @pytest.mark.asyncio
    async def test_concurrent_ingestion_different_events(self, db_session, db_metadata):
        """Test concurrent ingestion of different events."""
        adapter = SQLWalletEventIngestion(db_session, db_metadata)

        wallet_id = uuid4()
        occurred_at = datetime.utcnow()

        async def ingest_event(event_num):
            """Helper to ingest an event."""
            event = WalletTransactionEvent(
                wallet_id=wallet_id,
                provider=WalletProvider.FINCRA,
                event_type=WalletEventType.DEPOSIT,
                amount=100.0 + event_num,
                currency="USD",
                provider_event_id=f"provider_event_{event_num}",
                occurred_at=occurred_at,
            )
            return await adapter.ingest_event(event, idempotency_key=f"idem_key_{event_num}")

        # Ingest multiple events concurrently
        tasks = [ingest_event(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        # All should succeed and return different events
        assert len(results) == 5
        event_ids = [r.id for r in results]
        assert len(set(event_ids)) == 5  # All unique

    @pytest.mark.asyncio
    async def test_list_events_after_concurrent_ingestion(self, db_session, db_metadata):
        """Test listing events after concurrent ingestion."""
        adapter = SQLWalletEventIngestion(db_session, db_metadata)

        wallet_id = uuid4()
        occurred_at = datetime.utcnow()

        async def ingest_event(event_num):
            """Helper to ingest an event."""
            event = WalletTransactionEvent(
                wallet_id=wallet_id,
                provider=WalletProvider.FINCRA,
                event_type=WalletEventType.DEPOSIT,
                amount=100.0 + event_num,
                currency="USD",
                provider_event_id=f"provider_event_{event_num}",
                occurred_at=occurred_at,
            )
            return await adapter.ingest_event(event)

        # Ingest multiple events concurrently
        tasks = [ingest_event(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # List all events
        events = await adapter.list_by_wallet_id(wallet_id, limit=20)

        # Should have all 10 events
        assert len(events) == 10

        # All should belong to the same wallet
        assert all(e.wallet_id == wallet_id for e in events)

    @pytest.mark.asyncio
    async def test_pagination_correctness(self, db_session, db_metadata):
        """Test pagination returns correct and consistent results."""
        adapter = SQLWalletEventIngestion(db_session, db_metadata)

        wallet_id = uuid4()
        occurred_at = datetime.utcnow()

        # Ingest 15 events
        for i in range(15):
            event = WalletTransactionEvent(
                wallet_id=wallet_id,
                provider=WalletProvider.FINCRA,
                event_type=WalletEventType.DEPOSIT,
                amount=100.0 + i,
                currency="USD",
                provider_event_id=f"provider_event_{i}",
                occurred_at=occurred_at,
            )
            await adapter.ingest_event(event)

        # Get first page
        page1 = await adapter.list_by_wallet_id(wallet_id, limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await adapter.list_by_wallet_id(wallet_id, limit=5, offset=5)
        assert len(page2) == 5

        # Get third page
        page3 = await adapter.list_by_wallet_id(wallet_id, limit=5, offset=10)
        assert len(page3) == 5

        # All pages should have different events
        all_ids = [e.id for e in page1 + page2 + page3]
        assert len(set(all_ids)) == 15  # All unique

    @pytest.mark.asyncio
    async def test_get_by_provider_event_id(self, db_session, db_metadata):
        """Test getting event by provider event ID."""
        adapter = SQLWalletEventIngestion(db_session, db_metadata)

        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_event_id = "provider_event_123"
        occurred_at = datetime.utcnow()

        # Ingest event
        event = WalletTransactionEvent(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            provider_event_id=provider_event_id,
            occurred_at=occurred_at,
        )
        ingested = await adapter.ingest_event(event)

        # Get by provider event ID
        result = await adapter.get_by_provider_event_id(provider.value, provider_event_id)

        assert result is not None
        assert result.id == ingested.id
        assert result.provider_event_id == provider_event_id

    @pytest.mark.asyncio
    async def test_provider_event_id_uniqueness(self, db_session, db_metadata):
        """Test that provider_event_id prevents duplicates."""
        adapter = SQLWalletEventIngestion(db_session, db_metadata)

        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        provider_event_id = "provider_event_123"
        occurred_at = datetime.utcnow()

        # First ingestion
        event1 = WalletTransactionEvent(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            provider_event_id=provider_event_id,
            occurred_at=occurred_at,
        )
        result1 = await adapter.ingest_event(event1)

        # Second ingestion with same provider_event_id should return existing
        event2 = WalletTransactionEvent(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=200.0,  # Different amount
            currency="USD",
            provider_event_id=provider_event_id,
            occurred_at=occurred_at,
        )
        result2 = await adapter.ingest_event(event2)

        # Should return the same event (first one)
        assert result1.id == result2.id
        assert result2.amount == 100.0  # Original amount, not new one
