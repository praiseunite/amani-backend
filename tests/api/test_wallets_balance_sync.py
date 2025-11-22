"""API tests for wallet balance sync endpoints."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.adapters.inmemory.audit import InMemoryAudit
from app.adapters.inmemory.wallet_balance_sync import InMemoryWalletBalanceSync
from app.adapters.inmemory.wallet_provider import InMemoryWalletProvider
from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistry
from app.api.controllers.wallets import create_wallets_router
from app.application.services.wallet_balance_sync_service import WalletBalanceSyncService
from app.application.services.wallet_registry_service import WalletRegistryService
from app.application.use_cases.register_wallet import RegisterWalletUseCase
from app.application.use_cases.sync_wallet_balance import SyncWalletBalanceUseCase


class TestWalletBalanceSyncAPI:
    """Test suite for wallet balance sync API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with wallet routes."""
        # Create ports
        wallet_registry_port = InMemoryWalletRegistry()
        wallet_balance_sync_port = InMemoryWalletBalanceSync()
        wallet_provider_port = InMemoryWalletProvider()
        audit_port = InMemoryAudit()

        # Create services
        wallet_registry_service = WalletRegistryService(
            wallet_registry_port=wallet_registry_port,
            audit_port=audit_port,
        )
        wallet_balance_sync_service = WalletBalanceSyncService(
            wallet_balance_sync_port=wallet_balance_sync_port,
            wallet_provider_port=wallet_provider_port,
            wallet_registry_port=wallet_registry_port,
            audit_port=audit_port,
        )

        # Create use cases
        register_wallet_use_case = RegisterWalletUseCase(wallet_registry_service)
        sync_wallet_balance_use_case = SyncWalletBalanceUseCase(wallet_balance_sync_service)

        # Create a mock HMAC auth dependency for testing
        async def mock_hmac_auth():
            """Mock HMAC auth that always succeeds for testing."""
            return "test-key-id"

        # Create app and router
        app = FastAPI()
        router = create_wallets_router(
            register_wallet_use_case=register_wallet_use_case,
            hmac_auth_dependency=mock_hmac_auth,
            sync_wallet_balance_use_case=sync_wallet_balance_use_case,
        )
        app.include_router(router)

        # Store provider for test setup
        app.state.wallet_provider_port = wallet_provider_port

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_sync_balance_endpoint(self, client, app):
        """Test syncing wallet balance via API."""
        wallet_id = uuid4()
        balance = 100.50
        currency = "USD"

        # Set up mock provider
        app.state.wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            currency=currency,
            external_balance_id="ext_bal_123",
        )

        # Call sync endpoint
        response = client.post(f"/wallets/{wallet_id}/sync-balance")

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_id"] == str(wallet_id)
        assert data["balance"] == balance
        assert data["currency"] == currency
        assert data["external_balance_id"] == "ext_bal_123"

    def test_sync_balance_with_idempotency_key(self, client, app):
        """Test syncing with idempotency key."""
        wallet_id = uuid4()
        idempotency_key = "idem_key_1"
        balance = 100.50

        app.state.wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id="ext_bal_123",
        )

        # First request
        response1 = client.post(
            f"/wallets/{wallet_id}/sync-balance",
            params={"idempotency_key": idempotency_key},
        )

        # Second request with same key
        response2 = client.post(
            f"/wallets/{wallet_id}/sync-balance",
            params={"idempotency_key": idempotency_key},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Should return same snapshot
        data1 = response1.json()
        data2 = response2.json()
        assert data1["snapshot_id"] == data2["snapshot_id"]

    def test_get_balance_endpoint(self, client, app):
        """Test getting latest balance via API."""
        wallet_id = uuid4()
        balance = 100.50

        app.state.wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=balance,
            external_balance_id="ext_bal_123",
        )

        # First sync to create snapshot
        client.post(f"/wallets/{wallet_id}/sync-balance")

        # Get balance
        response = client.get(f"/wallets/{wallet_id}/balance")

        assert response.status_code == 200
        data = response.json()
        assert data["wallet_id"] == str(wallet_id)
        assert data["balance"] == balance

    def test_get_balance_not_found(self, client):
        """Test getting balance when no snapshot exists."""
        wallet_id = uuid4()

        response = client.get(f"/wallets/{wallet_id}/balance")

        assert response.status_code == 404
        assert "No balance snapshot found" in response.json()["detail"]

    def test_sync_multiple_times_creates_snapshots_on_balance_change(self, client, app):
        """Test that multiple syncs with different balances create separate snapshots."""
        wallet_id = uuid4()

        # First sync with balance 100
        app.state.wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=100.0,
            external_balance_id="ext_bal_1",
        )
        response1 = client.post(f"/wallets/{wallet_id}/sync-balance")

        # Second sync with balance 200
        app.state.wallet_provider_port.set_balance(
            wallet_id=wallet_id,
            balance=200.0,
            external_balance_id="ext_bal_2",
        )
        response2 = client.post(f"/wallets/{wallet_id}/sync-balance")

        assert response1.status_code == 200
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        # Should be different snapshots
        assert data1["snapshot_id"] != data2["snapshot_id"]
        assert data1["balance"] == 100.0
        assert data2["balance"] == 200.0

        # Get balance should return latest
        response3 = client.get(f"/wallets/{wallet_id}/balance")
        data3 = response3.json()
        assert data3["snapshot_id"] == data2["snapshot_id"]
        assert data3["balance"] == 200.0
