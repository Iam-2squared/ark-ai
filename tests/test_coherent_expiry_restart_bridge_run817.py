"""Coherent expiry restart comparison reopens one SQLite WAL snapshot, never purges."""

from __future__ import annotations

import pytest

import ark.memory.coherent_expiry_restart_bridge as restart
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_expiry_snapshot_review import review_coherent_expiry_snapshot


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    a = MemoryScope("owner", "notes")
    b = MemoryScope("owner", "tasks")
    store.put(MemoryWrite(a, "one", "private-one", expires_at_ms=1200))
    store.put(MemoryWrite(b, "two", "private-two", expires_at_ms=1300))
    return store, (a, b)


def _baseline(store, scopes, *, now_ms=1500, limit=100):
    return review_coherent_expiry_snapshot(store, scopes, now_ms=now_ms, limit=limit)


def _restart(store, scopes, retained, *, now_ms=1500, limit=100):
    return restart.review_coherent_expiry_restart(
        store, scopes, retained, now_ms=now_ms, limit=limit,
    )


def _no_authority(result):
    assert result.automatic_purge_authorized is False
    assert result.trusted_clock_verified is False
    assert result.independent_custody_verified is False
    assert result.historical_completeness_proven is False
    assert result.cross_epoch_atomicity_proven is False
    assert "private" not in repr(result)


def test_retained_quiescent_epoch_remains_local_claim(tmp_path):
    store, scopes = _store(tmp_path)
    prior = _baseline(store, scopes)
    reviewed = _restart(store, scopes, prior)
    assert reviewed == _restart(store, scopes, prior)
    assert reviewed.transition == "UNCHANGED_LOCAL_CLAIM"
    assert reviewed.previous_candidates == reviewed.observed_candidates == 2
    assert reviewed.previous_snapshot_sha256 == reviewed.observed_snapshot_sha256
    assert len(reviewed.receipt_sha256) == 64
    _no_authority(reviewed)


def test_new_due_memory_changes_local_digest_but_never_purges(tmp_path):
    store, scopes = _store(tmp_path)
    prior = _baseline(store, scopes)
    store.put(MemoryWrite(scopes[1], "three", "private-three", expires_at_ms=1400))
    reviewed = _restart(store, scopes, prior)
    assert reviewed.transition == "CHANGED_UNVERIFIED"
    assert reviewed.previous_candidates == 2
    assert reviewed.observed_candidates == 3
    assert reviewed.previous_snapshot_sha256 != reviewed.observed_snapshot_sha256
    _no_authority(reviewed)
    assert _baseline(store, scopes).cohort.candidate_count == 3  # No automatic purge.


def test_later_caller_clock_is_not_trusted_time(tmp_path):
    store, scopes = _store(tmp_path)
    prior = _baseline(store, scopes)
    reviewed = _restart(store, scopes, prior, now_ms=1600)
    assert reviewed.transition == "CLOCK_ADVANCED_UNVERIFIED"
    _no_authority(reviewed)


@pytest.mark.parametrize("problem", (
    "rollback", "wrong-limit", "mutated-snapshot-digest",
    "mutated-cohort", "truncated", "mixed-scopes", "bool-clock",
))
def test_ambiguous_retained_state_cannot_be_reused(tmp_path, problem):
    store, scopes = _store(tmp_path)
    prior = _baseline(store, scopes)
    now_ms, limit = 1500, 100
    if problem == "rollback":
        now_ms = 1499
    elif problem == "wrong-limit":
        limit = 99
    elif problem == "mutated-snapshot-digest":
        object.__setattr__(prior, "snapshot_sha256", "f" * 64)
    elif problem == "mutated-cohort":
        object.__setattr__(prior.cohort, "candidate_count", 777)
    elif problem == "truncated":
        prior = _baseline(store, scopes, limit=1)
        store.put(MemoryWrite(scopes[1], "overflow", "private", expires_at_ms=1400))
        prior = _baseline(store, scopes, limit=1)
        limit = 1
    elif problem == "mixed-scopes":
        scopes = (scopes[0], MemoryScope("another", "tasks"))
    else:
        now_ms = True
    with pytest.raises(restart.CoherentExpiryRestartRejected):
        _restart(store, scopes, prior, now_ms=now_ms, limit=limit)


@pytest.mark.parametrize("target", ("coherent-read", "restart-review", "result-denial", "hash"))
def test_rebound_review_components_refuse_before_database_use(
    tmp_path, monkeypatch, target,
):
    store, scopes = _store(tmp_path)
    prior = _baseline(store, scopes)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append(target)
        raise AssertionError("forged code must not run")

    with monkeypatch.context() as patch:
        if target == "coherent-read":
            patch.setattr(restart.coherent, "review_coherent_expiry_snapshot", forbidden)
        elif target == "restart-review":
            patch.setattr(
                restart.restart, "review_memory_expiry_restart_receipt", forbidden,
            )
        elif target == "result-denial":
            patch.setattr(
                restart.CoherentExpiryRestartReview,
                "automatic_purge_authorized", property(forbidden),
            )
        else:
            patch.setattr(restart.hashlib, "sha256", forbidden)
        with pytest.raises(
            restart.CoherentExpiryRestartRejected, match="protocol changed",
        ):
            _restart(store, scopes, prior)
    assert invoked == []
