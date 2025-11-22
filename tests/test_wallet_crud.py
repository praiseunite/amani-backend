"""
Unit tests for wallet CRUD operations.
"""

import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime


class TestWalletCRUDImports:
    """Test wallet CRUD function imports."""

    def test_wallet_registry_crud_imports(self):
        """Test that wallet registry CRUD functions can be imported."""
        from app.crud.wallet import (
            create_wallet_registry,
            get_wallet_registry_by_id,
            get_wallet_registry_by_external_id,
            get_wallet_registry_by_user_and_provider,
            get_wallet_registries_by_user,
            update_wallet_registry,
            deactivate_wallet_registry,
            delete_wallet_registry,
        )

        assert create_wallet_registry is not None
        assert get_wallet_registry_by_id is not None
        assert get_wallet_registry_by_external_id is not None
        assert get_wallet_registry_by_user_and_provider is not None
        assert get_wallet_registries_by_user is not None
        assert update_wallet_registry is not None
        assert deactivate_wallet_registry is not None
        assert delete_wallet_registry is not None

    def test_wallet_balance_crud_imports(self):
        """Test that wallet balance CRUD functions can be imported."""
        from app.crud.wallet_balance import (
            create_wallet_balance_snapshot,
            get_wallet_balance_snapshot_by_id,
            get_wallet_balance_snapshot_by_idempotency_key,
            get_latest_wallet_balance_snapshot,
            get_wallet_balance_snapshots_by_wallet,
            get_wallet_balance_snapshot_by_external_id,
            delete_wallet_balance_snapshot,
        )

        assert create_wallet_balance_snapshot is not None
        assert get_wallet_balance_snapshot_by_id is not None
        assert get_wallet_balance_snapshot_by_idempotency_key is not None
        assert get_latest_wallet_balance_snapshot is not None
        assert get_wallet_balance_snapshots_by_wallet is not None
        assert get_wallet_balance_snapshot_by_external_id is not None
        assert delete_wallet_balance_snapshot is not None

    def test_wallet_event_crud_imports(self):
        """Test that wallet event CRUD functions can be imported."""
        from app.crud.wallet_event import (
            create_wallet_event,
            get_wallet_event_by_id,
            get_wallet_event_by_external_id,
            get_wallet_event_by_idempotency_key,
            get_wallet_events_by_wallet,
            get_wallet_events_by_provider_event_id,
            get_wallet_events_by_type,
            delete_wallet_event,
        )

        assert create_wallet_event is not None
        assert get_wallet_event_by_id is not None
        assert get_wallet_event_by_external_id is not None
        assert get_wallet_event_by_idempotency_key is not None
        assert get_wallet_events_by_wallet is not None
        assert get_wallet_events_by_provider_event_id is not None
        assert get_wallet_events_by_type is not None
        assert delete_wallet_event is not None


class TestWalletCRUDFunctionSignatures:
    """Test wallet CRUD function signatures."""

    def test_create_wallet_registry_signature(self):
        """Test create_wallet_registry function signature."""
        from app.crud.wallet import create_wallet_registry
        import inspect

        sig = inspect.signature(create_wallet_registry)
        assert "db" in sig.parameters
        assert "user_id" in sig.parameters
        assert "provider" in sig.parameters
        assert "provider_account_id" in sig.parameters
        assert "provider_customer_id" in sig.parameters
        assert "metadata" in sig.parameters

    def test_create_wallet_balance_snapshot_signature(self):
        """Test create_wallet_balance_snapshot function signature."""
        from app.crud.wallet_balance import create_wallet_balance_snapshot
        import inspect

        sig = inspect.signature(create_wallet_balance_snapshot)
        assert "db" in sig.parameters
        assert "wallet_id" in sig.parameters
        assert "provider" in sig.parameters
        assert "balance" in sig.parameters
        assert "currency" in sig.parameters
        assert "idempotency_key" in sig.parameters

    def test_create_wallet_event_signature(self):
        """Test create_wallet_event function signature."""
        from app.crud.wallet_event import create_wallet_event
        import inspect

        sig = inspect.signature(create_wallet_event)
        assert "db" in sig.parameters
        assert "wallet_id" in sig.parameters
        assert "provider" in sig.parameters
        assert "event_type" in sig.parameters
        assert "amount" in sig.parameters
        assert "currency" in sig.parameters
        assert "idempotency_key" in sig.parameters


class TestWalletModels:
    """Test wallet model imports and structure."""

    def test_wallet_registry_model_import(self):
        """Test wallet registry model import."""
        from app.models.wallet_registry import WalletRegistry

        assert WalletRegistry is not None
        assert hasattr(WalletRegistry, "__tablename__")
        assert WalletRegistry.__tablename__ == "wallet_registry"

    def test_wallet_balance_snapshot_model_import(self):
        """Test wallet balance snapshot model import."""
        from app.models.wallet_balance_snapshot import WalletBalanceSnapshot

        assert WalletBalanceSnapshot is not None
        assert hasattr(WalletBalanceSnapshot, "__tablename__")
        assert WalletBalanceSnapshot.__tablename__ == "wallet_balance_snapshot"

    def test_wallet_event_model_import(self):
        """Test wallet transaction event model import."""
        from app.models.wallet_event import WalletTransactionEvent

        assert WalletTransactionEvent is not None
        assert hasattr(WalletTransactionEvent, "__tablename__")
        assert WalletTransactionEvent.__tablename__ == "wallet_transaction_event"

    def test_wallet_registry_model_columns(self):
        """Test wallet registry model has required columns."""
        from app.models.wallet_registry import WalletRegistry

        # Check that the model has expected attributes
        assert hasattr(WalletRegistry, "id")
        assert hasattr(WalletRegistry, "external_id")
        assert hasattr(WalletRegistry, "user_id")
        assert hasattr(WalletRegistry, "provider")
        assert hasattr(WalletRegistry, "provider_account_id")
        assert hasattr(WalletRegistry, "is_active")
        assert hasattr(WalletRegistry, "created_at")
        assert hasattr(WalletRegistry, "updated_at")

    def test_wallet_balance_snapshot_model_columns(self):
        """Test wallet balance snapshot model has required columns."""
        from app.models.wallet_balance_snapshot import WalletBalanceSnapshot

        assert hasattr(WalletBalanceSnapshot, "id")
        assert hasattr(WalletBalanceSnapshot, "wallet_id")
        assert hasattr(WalletBalanceSnapshot, "provider")
        assert hasattr(WalletBalanceSnapshot, "balance")
        assert hasattr(WalletBalanceSnapshot, "currency")
        assert hasattr(WalletBalanceSnapshot, "as_of")
        assert hasattr(WalletBalanceSnapshot, "created_at")

    def test_wallet_event_model_columns(self):
        """Test wallet transaction event model has required columns."""
        from app.models.wallet_event import WalletTransactionEvent

        assert hasattr(WalletTransactionEvent, "id")
        assert hasattr(WalletTransactionEvent, "external_id")
        assert hasattr(WalletTransactionEvent, "wallet_id")
        assert hasattr(WalletTransactionEvent, "provider")
        assert hasattr(WalletTransactionEvent, "event_type")
        assert hasattr(WalletTransactionEvent, "amount")
        assert hasattr(WalletTransactionEvent, "currency")
        assert hasattr(WalletTransactionEvent, "occurred_at")
        assert hasattr(WalletTransactionEvent, "created_at")
