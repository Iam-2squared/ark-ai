"""A separately retained trigger history fences new synthetic preparations."""

import sqlite3
from pathlib import Path

import pytest

from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)

A, B, C, D = ("a" * 64, "b" * 64, "c" * 64, "d" * 64)


def _setup(tmp_path: Path):
    path = tmp_path / "prepared.sqlite"
    store = SyntheticProactiveLedger(path)
    policy = SyntheticTriggerPolicy(
        "synthetic-owner", "local", "fixture", 1, "p1", 1, 20, 3,
    )
    return store, policy, path


def _prepare(store, policy, *, observation=A, now=100, retained=None):
    return store.prepare(
        policy, source_digest=B, observation_digest=observation,
        observed_at_ms=now, now_ms=now, retained=retained,
    )


def test_retained_empty_and_nonempty_histories_permit_append(tmp_path: Path):
    store, policy, _path = _setup(tmp_path)
    empty = read_proactive_witness(store)
    one = _prepare(store, policy, retained=empty)
    earlier = read_proactive_witness(store)
    second = _prepare(store, policy, observation=C, now=101, retained=earlier)
    assert one.trigger_id != second.trigger_id
    assert len(read_proactive_witness(store, retained=earlier).row_hashes) == 2


def test_deleted_history_denies_new_preparation_inside_writer(tmp_path: Path):
    store, policy, path = _setup(tmp_path)
    _prepare(store, policy)
    retained = read_proactive_witness(store)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_prepared_triggers")
    with pytest.raises(SyntheticTriggerRejected, match="retained proactive trigger history"):
        _prepare(store, policy, observation=C, now=101, retained=retained)
    assert store.count() == 0


def test_rewritten_prior_timestamp_denies_new_preparation(tmp_path: Path):
    store, policy, path = _setup(tmp_path)
    _prepare(store, policy)
    retained = read_proactive_witness(store)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_prepared_triggers SET prepared_at_ms=101"
        )
    with pytest.raises(SyntheticTriggerRejected, match="retained proactive trigger history"):
        _prepare(store, policy, observation=C, now=102, retained=retained)
    assert store.count() == 1


@pytest.mark.parametrize("bad", ["history", 42, True, object()])
def test_wrong_retained_types_fail_before_reservation(tmp_path: Path, bad):
    store, policy, _path = _setup(tmp_path)
    with pytest.raises(SyntheticTriggerRejected, match="exact retained"):
        _prepare(store, policy, retained=bad)
    assert store.count() == 0


def test_reflectively_mutated_witness_fails_without_a_write(tmp_path: Path):
    store, policy, _path = _setup(tmp_path)
    _prepare(store, policy)
    witness = read_proactive_witness(store)
    object.__setattr__(witness, "digest", "synthetic_triggers_" + "f" * 64)
    with pytest.raises(SyntheticTriggerRejected, match="witness integrity"):
        _prepare(store, policy, observation=C, now=101, retained=witness)
    assert store.count() == 1


def test_missing_database_is_never_recreated_by_fenced_preparation(tmp_path: Path):
    store, policy, path = _setup(tmp_path)
    witness = read_proactive_witness(store)
    path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        _prepare(store, policy, retained=witness)
    assert not path.exists()


def test_retained_fence_does_not_bypass_cooldown(tmp_path: Path):
    store, policy, _path = _setup(tmp_path)
    _prepare(store, policy)
    witness = read_proactive_witness(store)
    with pytest.raises(SyntheticTriggerRejected, match="minimum preparation interval"):
        _prepare(store, policy, observation=C, now=100, retained=witness)
    assert store.count() == 1


def test_retained_fence_does_not_bypass_rolling_budget(tmp_path: Path):
    store, policy, _path = _setup(tmp_path)
    _prepare(store, policy, now=100, observation=A)
    _prepare(store, policy, now=101, observation=C)
    _prepare(store, policy, now=102, observation=D)
    witness = read_proactive_witness(store)
    with pytest.raises(SyntheticTriggerRejected, match="rolling preparation budget"):
        _prepare(store, policy, now=103, observation="e" * 64, retained=witness)
    assert store.count() == 3
