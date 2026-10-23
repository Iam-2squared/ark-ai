"""Stored proactive fixture digests must bind the trigger primary key."""

import sqlite3
from pathlib import Path

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _prepare(store):
    return store.prepare(
        SyntheticTriggerPolicy("owner", "notes", "observe", 1, "v1", 1, 100, 2),
        source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=9,
        now_ms=10,
    )


@pytest.mark.parametrize(("field", "replacement"), [
    ("source_digest", "c" * 64),
    ("observation_digest", "d" * 64),
    ("scope_digest", "e" * 64),
    ("policy_digest", "f" * 64),
    ("trigger_id", "trigger_" + "0" * 64),
])
def test_well_formed_persisted_binding_mutation_fails_closed(
    tmp_path: Path, field: str, replacement: str,
):
    path = tmp_path / "synthetic.sqlite"
    store = SyntheticProactiveLedger(path)
    _prepare(store)
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_prepared_triggers SET {field}=?", (replacement,),
        )
    with pytest.raises(SyntheticTriggerRejected, match="identity"):
        store.count()
    with pytest.raises(SyntheticTriggerRejected, match="identity"):
        _prepare(store)
    with pytest.raises(SyntheticTriggerRejected, match="identity"):
        SyntheticProactiveLedger(path)


def test_valid_persisted_binding_remains_usable_across_restarts(tmp_path: Path):
    path = tmp_path / "synthetic.sqlite"
    first = SyntheticProactiveLedger(path)
    receipt = _prepare(first)
    reopened = SyntheticProactiveLedger(path)
    assert reopened.count() == 1
    assert receipt.trigger_id.startswith("trigger_")
    with pytest.raises(SyntheticTriggerRejected, match="duplicate"):
        _prepare(reopened)
    assert reopened.count() == 1
