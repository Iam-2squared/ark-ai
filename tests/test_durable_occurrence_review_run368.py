"""Synthetic-only reservation replay and crash/restart fixture checks."""

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecutedBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("disconnected fixture must never invoke backend")


def _identity(effect=Effect.WRITE):
    registry = ToolRegistry(
        (ToolRegistration("mock_tool", "fixture", effect, "offline", NeverExecutedBackend()),)
    )
    call = ToolCall("mock_tool", "fixture", "synthetic", {"n": 1})
    return registry, call


def _token(call, name="token-A"):
    return OneShotAuthorization(name, call.request_id, 1000)


def _occurrence(name):
    return "occ_" + hashlib.sha256(name.encode("utf-8")).hexdigest()


def test_restart_does_not_reopen_consumed_synthetic_token(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    registry, call = _identity()
    store = SyntheticOccurrenceStore(path)
    receipt = store.reserve_synthetic(
        registry, call, _token(call),
        occurrence_id=_occurrence("first"), now_ms=42,
    )
    assert receipt.bound_action_id == registry.bind(call).bound_action_id
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    reopened = SyntheticOccurrenceStore(path)
    assert reopened.count_synthetic() == 1
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        reopened.reserve_synthetic(
            registry, call, _token(call),
            occurrence_id=_occurrence("second"), now_ms=43,
        )
    assert store.count_synthetic() == 1


def test_same_occurrence_cannot_be_reused_with_different_token(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "fixture.sqlite")
    registry, call = _identity()
    store.reserve_synthetic(
        registry, call, _token(call, "token-A"),
        occurrence_id=_occurrence("same"), now_ms=10,
    )
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        store.reserve_synthetic(
            registry, call, _token(call, "token-B"),
            occurrence_id=_occurrence("same"), now_ms=11,
        )
    assert store.count_synthetic() == 1


def test_distinct_occurrences_and_tokens_are_independent(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "fixture.sqlite")
    registry, call = _identity()
    for name in ("A", "B"):
        store.reserve_synthetic(
            registry, call, _token(call, "token-" + name),
            occurrence_id=_occurrence(name), now_ms=25,
        )
    assert store.count_synthetic() == 2


def test_two_store_instances_cannot_both_reserve_the_same_token(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    registry, call = _identity()
    stores = (SyntheticOccurrenceStore(path), SyntheticOccurrenceStore(path))
    barrier = Barrier(2)

    def attempt(store):
        barrier.wait(timeout=5)
        try:
            store.reserve_synthetic(
                registry, call, _token(call),
                occurrence_id=_occurrence("one"), now_ms=30,
            )
            return True
        except SyntheticReplayRejected:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, stores))
    assert sorted(results) == [False, True]
    assert stores[0].count_synthetic() == 1


@pytest.mark.parametrize("bad_time", [-1, True, 2**63, "10"])
def test_invalid_synthetic_clock_does_not_spend_token(tmp_path: Path, bad_time):
    store = SyntheticOccurrenceStore(tmp_path / "fixture.sqlite")
    registry, call = _identity()
    with pytest.raises(SyntheticReplayRejected, match="timestamp"):
        store.reserve_synthetic(
            registry, call, _token(call),
            occurrence_id=_occurrence("time"), now_ms=bad_time,
        )
    assert store.count_synthetic() == 0


def test_expired_token_never_reserves(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "fixture.sqlite")
    registry, call = _identity()
    with pytest.raises(SyntheticReplayRejected, match="expired"):
        store.reserve_synthetic(
            registry, call, _token(call),
            occurrence_id=_occurrence("late"), now_ms=1000,
        )
    assert store.count_synthetic() == 0


def test_read_effect_does_not_reserve_a_write_occurrence(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "fixture.sqlite")
    registry, call = _identity(Effect.READ)
    with pytest.raises(SyntheticReplayRejected, match="WRITE"):
        store.reserve_synthetic(
            registry, call, _token(call),
            occurrence_id=_occurrence("read"), now_ms=0,
        )
    assert store.count_synthetic() == 0


def test_schema_drift_is_rejected_without_repair(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    with sqlite3.connect(path) as conn:
        conn.execute("ALTER TABLE synthetic_occurrence_reservations ADD COLUMN drift TEXT")
    with pytest.raises(SyntheticReplayRejected, match="schema changed"):
        SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected, match="schema changed"):
        store.count_synthetic()


def test_missing_db_read_does_not_create_new_database(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        store.count_synthetic()
    assert not path.exists()


@pytest.mark.parametrize("name", ["invalid", "occ_" + "z" * 64, True, ""])
def test_invalid_occurrence_rejected_without_reservation(tmp_path: Path, name):
    store = SyntheticOccurrenceStore(tmp_path / "fixture.sqlite")
    registry, call = _identity()
    with pytest.raises(SyntheticReplayRejected, match="occurrence identity"):
        store.reserve_synthetic(
            registry, call, _token(call), occurrence_id=name, now_ms=0,
        )
    assert store.count_synthetic() == 0


def test_existing_unversioned_database_is_not_repaired(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unrelated(x TEXT)")
    with pytest.raises(SyntheticReplayRejected, match="nonempty"):
        SyntheticOccurrenceStore(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='unrelated'").fetchone()
