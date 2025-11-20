"""
Unit tests for WalletRegistryService using InMemory adapter
"""
import pytest

from app.adapters.inmemory.wallet_registry import InMemoryWalletRegistryAdapter
from app.application.services.wallet_registry_service import WalletRegistryService


def test_idempotency_by_key():
    adapter = InMemoryWalletRegistryAdapter()
    service = WalletRegistryService(adapter)

    rec1 = service.register('lnbits', 'w_abc', 'botuser1', metadata={'x':1}, idempotency_key='key-1')
    rec2 = service.register('lnbits', 'w_abc', 'botuser1', metadata={'x':1}, idempotency_key='key-1')

    assert rec1.id == rec2.id


def test_idempotency_by_provider():
    adapter = InMemoryWalletRegistryAdapter()
    service = WalletRegistryService(adapter)

    rec1 = service.register('lnbits', 'w_abc', 'botuser1', metadata={'x':1}, idempotency_key=None)
    rec2 = service.register('lnbits', 'w_abc', 'botuser2', metadata={'x':2}, idempotency_key=None)

    assert rec1.id == rec2.id
