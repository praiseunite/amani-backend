"""Unit tests for wallet event ingestion."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.adapters.inmemory.audit import InMemoryAudit
from app.adapters.inmemory.wallet_event_ingestion import InMemoryWalletEventIngestion
from app.application.services.wallet_event_ingestion_service import WalletEventIngestionService
from app.domain.entities import WalletEventType, WalletProvider


class TestWalletEventIngestion:
    """Test suite for wallet event ingestion."""

    @pytest.fixture
    def event_ingestion_port(self):
        """Create in-memory event ingestion port."""
        return InMemoryWalletEventIngestion()

    @pytest.fixture
    def audit_port(self):
        """Create in-memory audit port."""
        return InMemoryAudit()

    @pytest.fixture
    def service(self, event_ingestion_port, audit_port):
        """Create wallet event ingestion service."""
        return WalletEventIngestionService(
            event_ingestion_port=event_ingestion_port,
            audit_port=audit_port,
        )

    @pytest.mark.asyncio
    async def test_ingest_new_event(self, service):
        """Test ingesting a new wallet event."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        event_type = WalletEventType.DEPOSIT
        amount = 100.50
        currency = "USD"
        occurred_at = datetime.utcnow()
        provider_event_id = "provider_event_123"

        result = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            provider_event_id=provider_event_id,
        )

        assert result is not None
        assert result.wallet_id == wallet_id
        assert result.provider == provider
        assert result.event_type == event_type
        assert result.amount == amount
        assert result.currency == currency
        assert result.provider_event_id == provider_event_id

    @pytest.mark.asyncio
    async def test_ingest_duplicate_provider_event_id(self, service):
        """Test that duplicate provider_event_id returns existing event."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        event_type = WalletEventType.DEPOSIT
        amount = 100.50
        currency = "USD"
        occurred_at = datetime.utcnow()
        provider_event_id = "provider_event_123"

        # First ingestion
        result1 = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            provider_event_id=provider_event_id,
        )

        # Second ingestion with same provider_event_id
        result2 = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            provider_event_id=provider_event_id,
        )

        # Should return the same event
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_ingest_duplicate_idempotency_key(self, service):
        """Test that duplicate idempotency_key returns existing event."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        event_type = WalletEventType.DEPOSIT
        amount = 100.50
        currency = "USD"
        occurred_at = datetime.utcnow()
        idempotency_key = "idem_key_1"

        # First ingestion
        result1 = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            idempotency_key=idempotency_key,
        )

        # Second ingestion with same idempotency_key
        result2 = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=event_type,
            amount=amount,
            currency=currency,
            occurred_at=occurred_at,
            idempotency_key=idempotency_key,
        )

        # Should return the same event
        assert result1.id == result2.id

    @pytest.mark.asyncio
    async def test_list_events_by_wallet(self, service):
        """Test listing events for a wallet."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at_base = datetime.utcnow()

        # Ingest multiple events
        events = []
        for i in range(5):
            event = await service.ingest_event(
                wallet_id=wallet_id,
                provider=provider,
                event_type=WalletEventType.DEPOSIT,
                amount=100.0 + i,
                currency="USD",
                occurred_at=occurred_at_base + timedelta(seconds=i),
                provider_event_id=f"provider_event_{i}",
            )
            events.append(event)

        # List events
        result = await service.list_events(wallet_id=wallet_id, limit=10)

        assert len(result) == 5
        # Should be ordered by occurred_at descending
        assert result[0].occurred_at >= result[1].occurred_at
        assert result[1].occurred_at >= result[2].occurred_at

    @pytest.mark.asyncio
    async def test_list_events_with_pagination(self, service):
        """Test pagination when listing events."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at_base = datetime.utcnow()

        # Ingest 10 events
        for i in range(10):
            await service.ingest_event(
                wallet_id=wallet_id,
                provider=provider,
                event_type=WalletEventType.DEPOSIT,
                amount=100.0 + i,
                currency="USD",
                occurred_at=occurred_at_base + timedelta(seconds=i),
                provider_event_id=f"provider_event_{i}",
            )

        # Get first page
        page1 = await service.list_events(wallet_id=wallet_id, limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = await service.list_events(wallet_id=wallet_id, limit=5, offset=5)
        assert len(page2) == 5

        # Pages should have different events
        assert page1[0].id != page2[0].id

    @pytest.mark.asyncio
    async def test_list_events_filters_by_wallet(self, service):
        """Test that list_events filters by wallet_id."""
        wallet_id1 = uuid4()
        wallet_id2 = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()

        # Ingest events for wallet 1
        await service.ingest_event(
            wallet_id=wallet_id1,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            occurred_at=occurred_at,
            provider_event_id="provider_event_1",
        )

        # Ingest events for wallet 2
        await service.ingest_event(
            wallet_id=wallet_id2,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=200.0,
            currency="USD",
            occurred_at=occurred_at,
            provider_event_id="provider_event_2",
        )

        # List events for wallet 1
        result1 = await service.list_events(wallet_id=wallet_id1)
        assert len(result1) == 1
        assert result1[0].wallet_id == wallet_id1

        # List events for wallet 2
        result2 = await service.list_events(wallet_id=wallet_id2)
        assert len(result2) == 1
        assert result2[0].wallet_id == wallet_id2

    @pytest.mark.asyncio
    async def test_get_event_by_id(self, service):
        """Test getting an event by ID."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()

        # Ingest event
        ingested = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            occurred_at=occurred_at,
            provider_event_id="provider_event_1",
        )

        # Get event by ID
        result = await service.get_event(ingested.id)

        assert result is not None
        assert result.id == ingested.id
        assert result.wallet_id == wallet_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_event(self, service):
        """Test getting a nonexistent event returns None."""
        nonexistent_id = uuid4()
        result = await service.get_event(nonexistent_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_ingest_with_metadata(self, service):
        """Test ingesting event with metadata."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()
        metadata = {"transaction_id": "tx_123", "note": "Test deposit"}

        result = await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            occurred_at=occurred_at,
            metadata=metadata,
        )

        assert result.metadata == metadata

    @pytest.mark.asyncio
    async def test_audit_events_recorded(self, service, audit_port):
        """Test that audit events are recorded for new ingestions."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()

        # Ingest event
        await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            occurred_at=occurred_at,
            provider_event_id="provider_event_1",
        )

        # Check audit events
        events = audit_port.get_events()
        assert len(events) == 1
        assert events[0]["action"] == "ingest_wallet_event"
        assert events[0]["resource_type"] == "wallet_transaction_event"

    @pytest.mark.asyncio
    async def test_no_duplicate_audit_for_duplicate_event(self, service, audit_port):
        """Test that no duplicate audit events for duplicate ingestions."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()
        provider_event_id = "provider_event_1"

        # First ingestion
        await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            occurred_at=occurred_at,
            provider_event_id=provider_event_id,
        )

        # Second ingestion (duplicate)
        await service.ingest_event(
            wallet_id=wallet_id,
            provider=provider,
            event_type=WalletEventType.DEPOSIT,
            amount=100.0,
            currency="USD",
            occurred_at=occurred_at,
            provider_event_id=provider_event_id,
        )

        # Should only have one audit event
        events = audit_port.get_events()
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_different_event_types(self, service):
        """Test ingesting different event types."""
        wallet_id = uuid4()
        provider = WalletProvider.FINCRA
        occurred_at = datetime.utcnow()

        event_types = [
            WalletEventType.DEPOSIT,
            WalletEventType.WITHDRAWAL,
            WalletEventType.TRANSFER_IN,
            WalletEventType.TRANSFER_OUT,
            WalletEventType.FEE,
            WalletEventType.REFUND,
        ]

        for i, event_type in enumerate(event_types):
            result = await service.ingest_event(
                wallet_id=wallet_id,
                provider=provider,
                event_type=event_type,
                amount=100.0,
                currency="USD",
                occurred_at=occurred_at,
                provider_event_id=f"provider_event_{i}",
            )
            assert result.event_type == event_type

    @pytest.mark.asyncio
    async def test_different_providers(self, service):
        """Test ingesting events from different providers."""
        wallet_id = uuid4()
        occurred_at = datetime.utcnow()

        providers = [
            WalletProvider.FINCRA,
            WalletProvider.PAYSTACK,
            WalletProvider.FLUTTERWAVE,
        ]

        for i, provider in enumerate(providers):
            result = await service.ingest_event(
                wallet_id=wallet_id,
                provider=provider,
                event_type=WalletEventType.DEPOSIT,
                amount=100.0,
                currency="USD",
                occurred_at=occurred_at,
                provider_event_id=f"provider_event_{i}",
            )
            assert result.provider == provider
