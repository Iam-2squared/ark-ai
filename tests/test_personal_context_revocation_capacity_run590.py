"""Privacy veto markers must never strand a bounded local SQLite ledger.

All scopes/timestamps are synthetic. These tests grant no consent, authorize
no data disclosure and make no claim of secure physical erasure.
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

import ark.personal_context_revocation_review as module
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_continuity_review import review_revocation_continuity
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _revoke(store, name, at_ms):
    return store.revoke(MemoryScope("fixture-owner", name), at_ms=at_ms)


def test_capacity_refuses_new_veto_without_stranding_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(module, "_MAX_REVOCATION_ROWS", 2)
    path = tmp_path / "privacy-revocation.sqlite"
    store = SyntheticContextRevocationLedger(path)
    _revoke(store, "first", 100)
    _revoke(store, "second", 101)
    initial = review_revocation_continuity(store)
    assert len(initial.rows) == 2

    with pytest.raises(SyntheticContextRevocationRejected, match="capacity exhausted"):
        _revoke(store, "third", 102)

    restarted = SyntheticContextRevocationLedger(path)
    assert review_revocation_continuity(restarted, retained=initial) == initial
    with pytest.raises(SyntheticContextRevocationRejected, match="capacity exhausted"):
        _revoke(restarted, "fourth", 103)
    assert review_revocation_continuity(restarted) == initial


def test_zero_capacity_stores_no_veto_and_does_not_grant_consent(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(module, "_MAX_REVOCATION_ROWS", 0)
    store = SyntheticContextRevocationLedger(tmp_path / "zero.sqlite")
    with pytest.raises(SyntheticContextRevocationRejected, match="capacity exhausted"):
        _revoke(store, "first", 100)
    assert review_revocation_continuity(store).rows == ()


def test_competing_revocations_cannot_cross_last_capacity_slot(
    tmp_path: Path, monkeypatch,
):
    monkeypatch.setattr(module, "_MAX_REVOCATION_ROWS", 1)
    path = tmp_path / "contended.sqlite"
    stores = (
        SyntheticContextRevocationLedger(path),
        SyntheticContextRevocationLedger(path),
    )
    ready = Barrier(2)

    def attempt(args):
        ledger, namespace = args
        ready.wait(timeout=10)
        try:
            digest = _revoke(ledger, namespace, 100)
            assert isinstance(digest, str)
            return True
        except SyntheticContextRevocationRejected as exc:
            assert "capacity exhausted" in str(exc)
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(
            attempt, zip(stores, ("context-a", "context-b"), strict=True),
        ))
    assert sorted(outcomes) == [False, True]
    reopened = SyntheticContextRevocationLedger(path)
    assert len(review_revocation_continuity(reopened).rows) == 1
