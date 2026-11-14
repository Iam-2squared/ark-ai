"""The bounded synthetic reservation ledger must stay readable at capacity.

All tokens, times and identities are synthetic; no backend is dispatched.
"""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

import ark.agency.durable_occurrence_review as occurrence_module
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic reservation cannot dispatch")


def _fixture():
    registry = ToolRegistry(
        (ToolRegistration("mock", "fixture", Effect.WRITE, "offline", NeverDispatch()),)
    )
    call = ToolCall("mock", "fixture", "synthetic", {"case": "capacity"})
    return registry, call


def _reserve(store, registry, call, name, now_ms=30):
    return store.reserve_synthetic(
        registry,
        call,
        OneShotAuthorization(f"synthetic-{name}", call.request_id, 1000),
        occurrence_id="occ_" + hashlib.sha256(name.encode()).hexdigest(),
        now_ms=now_ms,
    )


def test_full_ledger_refuses_next_insert_without_stranding_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(occurrence_module, "_MAX_FIXTURE_ROWS", 1)
    path = tmp_path / "synthetic.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call = _fixture()
    first = _reserve(store, registry, call, "first")
    assert first.dispatch_authorized is False
    assert store.count_synthetic() == 1

    with pytest.raises(SyntheticReplayRejected, match="capacity exhausted"):
        _reserve(store, registry, call, "second", now_ms=31)

    restarted = SyntheticOccurrenceStore(path)
    assert restarted.count_synthetic() == 1
    with pytest.raises(SyntheticReplayRejected, match="capacity exhausted"):
        _reserve(restarted, registry, call, "third", now_ms=32)
    assert restarted.count_synthetic() == 1

    # The failed INSERT did not spend the second fixture token. Raising the
    # synthetic test bound permits it without any journal repair.
    monkeypatch.setattr(occurrence_module, "_MAX_FIXTURE_ROWS", 2)
    again = _reserve(restarted, registry, call, "second", now_ms=33)
    assert again.automatic_replay_authorized is False
    assert restarted.count_synthetic() == 2


def test_zero_capacity_rejects_first_reservation_without_inserting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    store = SyntheticOccurrenceStore(tmp_path / "synthetic.sqlite")
    registry, call = _fixture()
    monkeypatch.setattr(occurrence_module, "_MAX_FIXTURE_ROWS", 0)
    with pytest.raises(SyntheticReplayRejected, match="capacity exhausted"):
        _reserve(store, registry, call, "first")
    assert store.count_synthetic() == 0


def test_competing_writers_cannot_cross_same_capacity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(occurrence_module, "_MAX_FIXTURE_ROWS", 1)
    path = tmp_path / "synthetic.sqlite"
    stores = (SyntheticOccurrenceStore(path), SyntheticOccurrenceStore(path))
    registry, call = _fixture()
    barrier = Barrier(2)

    def attempt(pair):
        store, name = pair
        barrier.wait(timeout=10)
        try:
            receipt = _reserve(store, registry, call, name)
            assert receipt.outcome_known is False
            return True
        except SyntheticReplayRejected as exc:
            assert "capacity exhausted" in str(exc)
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, zip(stores, ("A", "B"), strict=True)))

    assert sorted(outcomes) == [False, True]
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
