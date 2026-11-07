"""Offline proactive admission is restart-safe, bounded and never an action."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)

A = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64


def _policy(**overrides):
    fields = dict(
        owner="synthetic-owner", namespace="fixture",
        definition_id="observe", revision=1, policy_revision="v1",
        minimum_interval_ms=1, rolling_window_ms=10,
        max_preparations_per_window=2,
    )
    fields.update(overrides)
    return SyntheticTriggerPolicy(**fields)


def _prepare(store, policy=None, observation=A, now=100, source=B):
    return store.prepare(
        _policy() if policy is None else policy,
        source_digest=source, observation_digest=observation,
        observed_at_ms=now, now_ms=now,
    )


def test_preparation_is_inert_and_content_minimized(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    store = SyntheticProactiveLedger(path)
    receipt = _prepare(store)
    assert receipt.trigger_id.startswith("trigger_")
    assert len(receipt.trigger_id) == 72
    assert receipt.prepared_at_ms == 100
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert store.count() == 1
    with sqlite3.connect(path) as conn:
        columns = conn.execute(
            "SELECT * FROM synthetic_prepared_triggers"
        ).fetchone()
    assert "synthetic-owner" not in repr(columns)
    assert "fixture" not in repr(columns)


def test_reopen_preserves_deduplication_even_after_window(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    store = SyntheticProactiveLedger(path)
    first = _prepare(store)
    reopened = SyntheticProactiveLedger(path)
    with pytest.raises(SyntheticTriggerRejected, match="duplicate"):
        _prepare(reopened, observation=A, now=200)
    assert reopened.count() == 1
    assert first.notification_authorized is False


def test_minimum_interval_denies_distinct_observation(tmp_path: Path):
    store = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    policy = _policy(minimum_interval_ms=10)
    _prepare(store, policy=policy, observation=A, now=100)
    with pytest.raises(SyntheticTriggerRejected, match="minimum preparation"):
        _prepare(store, policy=policy, observation=C, now=109)
    assert store.count() == 1
    _prepare(store, policy=policy, observation=C, now=110)
    assert store.count() == 2


def test_rolling_window_boundary_frees_slot(tmp_path: Path):
    store = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    _prepare(store, observation=A, now=100)
    _prepare(store, observation=C, now=101)
    with pytest.raises(SyntheticTriggerRejected, match="rolling preparation"):
        _prepare(store, observation=D, now=102)
    _prepare(store, observation=D, now=110)
    assert store.count() == 3


def test_distinct_scope_and_policy_revision_are_isolated(tmp_path: Path):
    store = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    one = _prepare(store, policy=_policy(), now=100)
    two = _prepare(store, policy=_policy(owner="another"), now=100)
    three = _prepare(store, policy=_policy(namespace="other"), now=100)
    four = _prepare(store, policy=_policy(policy_revision="v2"), now=100)
    assert len({one.trigger_id, two.trigger_id, three.trigger_id,
                four.trigger_id}) == 4
    assert store.count() == 4


def test_clock_regression_and_future_observation_fail_closed(tmp_path: Path):
    store = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    _prepare(store, now=100)
    with pytest.raises(SyntheticTriggerRejected, match="clock regressed"):
        _prepare(store, observation=C, now=99)
    with pytest.raises(SyntheticTriggerRejected, match="future observation"):
        store.prepare(
            _policy(), source_digest=B, observation_digest=C,
            observed_at_ms=102, now_ms=101,
        )
    assert store.count() == 1


@pytest.mark.parametrize("field,bad", [
    ("revision", False),
    ("minimum_interval_ms", 0),
    ("rolling_window_ms", -1),
    ("max_preparations_per_window", True),
    ("revision", 2**63),
    ("owner", ""),
    ("namespace", " whitespace "),
])
def test_invalid_policy_fields_fail_closed(field, bad):
    with pytest.raises(ValueError):
        _policy(**{field: bad})


@pytest.mark.parametrize("bad", ["not-a-hash", "A" * 64, None, 123])
def test_invalid_observation_digest_never_writes(tmp_path: Path, bad):
    store = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    with pytest.raises(SyntheticTriggerRejected, match="canonical"):
        _prepare(store, observation=bad)
    assert store.count() == 0


@pytest.mark.parametrize("bad", [True, -1, 2**63, "100"])
def test_invalid_clock_never_writes(tmp_path: Path, bad):
    store = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    with pytest.raises(ValueError, match="bounded integer"):
        _prepare(store, now=bad)
    assert store.count() == 0


def test_cross_instance_race_admits_only_one(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    SyntheticProactiveLedger(path)
    barrier = Barrier(2)

    def attempt():
        store = SyntheticProactiveLedger(path)
        barrier.wait(timeout=10)
        try:
            return _prepare(store).trigger_id
        except SyntheticTriggerRejected:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = tuple(pool.map(lambda _ignored: attempt(), range(2)))
    assert sum(value is not None for value in result) == 1
    assert SyntheticProactiveLedger(path).count() == 1


def test_missing_database_read_does_not_create_new_file(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    store = SyntheticProactiveLedger(path)
    path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        store.count()
    assert not path.exists()


def test_missing_database_preparation_does_not_recreate(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    store = SyntheticProactiveLedger(path)
    path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        _prepare(store)
    assert not path.exists()


def test_schema_drift_is_refused_without_repair(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    store = SyntheticProactiveLedger(path)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(SyntheticTriggerRejected, match="schema version"):
        store.count()
    with pytest.raises(SyntheticTriggerRejected, match="schema version"):
        _prepare(store)


def test_same_version_persisted_row_corruption_is_refused(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    store = SyntheticProactiveLedger(path)
    _prepare(store)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_prepared_triggers SET source_digest='bad'"
        )
    with pytest.raises(SyntheticTriggerRejected, match="row integrity"):
        store.count()
    with pytest.raises(SyntheticTriggerRejected, match="row integrity"):
        _prepare(store, observation=C, now=200)


def test_uri_reserved_path_and_no_actions(tmp_path: Path):
    store = SyntheticProactiveLedger(tmp_path / "synthetic #100 %.sqlite")
    assert _prepare(store).notification_authorized is False
    assert store.count() == 1
