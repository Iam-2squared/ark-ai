"""Disconnected Memory scope result custody under reentrant fixture callbacks."""

from dataclasses import FrozenInstanceError

import pytest

import ark.memory.synthetic_multiscope_integrity_review as reviewer
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


@pytest.fixture
def state(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "synthetic.sqlite", clock_ms=lambda: 100)
    scopes = (
        MemoryScope("synthetic-owner", "alpha"),
        MemoryScope("synthetic-owner", "beta"),
    )
    store.put(MemoryWrite(scopes[0], "synthetic-source", "synthetic bytes only"))
    return store, scopes


def test_normal_snapshot_and_cached_review_remain_inert(state):
    store, scopes = state
    prior = reviewer.review_synthetic_memory_scopes(store, scopes)
    result = reviewer.review_synthetic_memory_scopes(
        store, scopes, require_same_snapshot=prior,
    )
    assert result == prior
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert result.deletion_authorized is False
    with pytest.raises(FrozenInstanceError):
        result.snapshot_digest = "forged"


def test_result_constructor_cannot_forge_snapshot_digest(state, monkeypatch):
    store, scopes = state
    constructor = reviewer.SyntheticMemorySnapshotDigest

    def forge(owner_digest, rows, digest):
        result = constructor(owner_digest, rows, digest)
        object.__setattr__(result, "snapshot_digest", "memevt_" + "0" * 64)
        return result

    monkeypatch.setattr(reviewer, "SyntheticMemorySnapshotDigest", forge)
    with pytest.raises(
        reviewer.SyntheticMemorySnapshotRejected, match="constructed Memory snapshot",
    ):
        reviewer.review_synthetic_memory_scopes(store, scopes)


def test_equal_valued_snapshot_digest_carrier_swap_rejected(state, monkeypatch):
    store, scopes = state
    constructor = reviewer.SyntheticMemorySnapshotDigest

    def swap(owner_digest, rows, digest):
        result = constructor(owner_digest, rows, digest)
        clone = ("x" + digest)[1:]
        assert clone == digest and clone is not digest
        object.__setattr__(result, "snapshot_digest", clone)
        return result

    monkeypatch.setattr(reviewer, "SyntheticMemorySnapshotDigest", swap)
    with pytest.raises(
        reviewer.SyntheticMemorySnapshotRejected, match="constructed Memory snapshot",
    ):
        reviewer.review_synthetic_memory_scopes(store, scopes)


def test_reentrant_constructor_cannot_rebind_equal_event_carrier(state, monkeypatch):
    store, scopes = state
    constructor = reviewer.SyntheticMemorySnapshotDigest

    def swap(owner_digest, rows, digest):
        old = rows[0].events.tail_hash
        clone = ("x" + old)[1:]
        assert clone == old and clone is not old
        object.__setattr__(rows[0].events, "tail_hash", clone)
        return constructor(owner_digest, rows, digest)

    monkeypatch.setattr(reviewer, "SyntheticMemorySnapshotDigest", swap)
    with pytest.raises(
        reviewer.SyntheticMemorySnapshotRejected, match="constructed Memory scope",
    ):
        reviewer.review_synthetic_memory_scopes(store, scopes)


def test_digest_callback_cannot_rebind_equal_scope_receipt(state, monkeypatch):
    store, scopes = state
    original_scope = reviewer.SyntheticMemoryScopeDigest
    original_hash = reviewer._hash
    captured = []

    def capture_scope(*args):
        scope = original_scope(*args)
        captured.append(scope)
        return scope

    def swap_on_digest(label, value):
        digest = original_hash(label, value)
        if label == "ARK-synthetic-memory-multiscope-v1":
            assert captured
            old = captured[0].live_rows_digest
            clone = ("x" + old)[1:]
            assert clone == old and clone is not old
            object.__setattr__(captured[0], "live_rows_digest", clone)
        return digest

    monkeypatch.setattr(reviewer, "SyntheticMemoryScopeDigest", capture_scope)
    monkeypatch.setattr(reviewer, "_hash", swap_on_digest)
    with pytest.raises(
        reviewer.SyntheticMemorySnapshotRejected, match="constructed Memory scope",
    ):
        reviewer.review_synthetic_memory_scopes(store, scopes)
