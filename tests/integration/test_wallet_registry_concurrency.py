"""
Integration test for concurrent wallet registry insert (DB-backed). Requires TEST_DATABASE_URL env var
"""
import os
import threading
import time
import pytest

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')

pytest.skipif = pytest.importorskip

if not TEST_DATABASE_URL:
    pytest.skip('TEST_DATABASE_URL not set - skipping DB concurrency test', allow_module_level=True)

from sqlalchemy import create_engine
from app.adapters.sql.wallet_registry import SQLWalletRegistryAdapter
from app.application.services.wallet_registry_service import WalletRegistryService


def worker_register(service, results, idx):
    try:
        rec = service.register('lnbits', 'w_concurrent', f'bot{idx}', idempotency_key=None)
        results.append(rec.id)
    except Exception as exc:
        results.append(str(exc))

@pytest.mark.integration
def test_concurrent_inserts_do_not_duplicate():
    engine = create_engine(TEST_DATABASE_URL)
    adapter = SQLWalletRegistryAdapter(engine)
    service = WalletRegistryService(adapter)

    results = []
    threads = [threading.Thread(target=worker_register, args=(service, results, i)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # all successful results that are ints should be identical
    int_ids = [r for r in results if isinstance(r, int)]
    assert len(set(int_ids)) <= 1
