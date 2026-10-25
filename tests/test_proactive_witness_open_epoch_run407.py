"""Offline proactive witness snapshots pin source/history across SQLite open.

Only disposable local fixture hashes are involved; no notification, external
ToolBackend, clock attestation or consent is provided by these tests.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.proactive_synthetic_continuity_review as review
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _state(tmp_path):
    path = tmp_path / "triggers.sqlite"
    ledger = SyntheticProactiveLedger(path)
    policy = SyntheticTriggerPolicy(
        "owner", "private", "offline-fixture", 1, "rev1", 5, 100, 3,
    )
    ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=10, now_ms=10,
    )
    witness = review.read_proactive_witness(ledger)
    assert len(witness.row_hashes) == 1
    return ledger, witness, path


@pytest.mark.parametrize("boundary", ("resolve", "as_uri", "connect"))
@pytest.mark.parametrize("target", ("ledger_path", "retained_rows"))
def test_source_or_retained_witness_drift_at_sqlite_open_is_vetoed(
    tmp_path, monkeypatch, boundary, target,
):
    ledger, retained, path = _state(tmp_path)
    original_connect = sqlite3.connect
    opened = []
    observed = []

    def mutate():
        observed.append((boundary, target))
        if target == "ledger_path":
            replacement = Path(str(path))
            assert replacement == ledger.path and replacement is not ledger.path
            ledger.path = replacement
        else:
            replacement = tuple(list(retained.row_hashes))
            assert replacement == retained.row_hashes
            assert replacement is not retained.row_hashes
            object.__setattr__(retained, "row_hashes", replacement)

    if boundary == "connect":
        def injected(*args, **kwargs):
            conn = original_connect(*args, **kwargs)
            opened.append(conn)
            mutate()
            return conn

        monkeypatch.setattr(review.sqlite3, "connect", injected)
    else:
        original = getattr(Path, boundary)

        def injected(self, *args, **kwargs):
            result = original(self, *args, **kwargs)
            mutate()
            return result

        monkeypatch.setattr(Path, boundary, injected)

    with pytest.raises(
        SyntheticTriggerRejected, match="source or retained history changed",
    ):
        review.read_proactive_witness(ledger, retained=retained)
    assert observed == [(boundary, target)]
    for conn in opened:
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            conn.execute("SELECT 1")
    with original_connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers"
        ).fetchone()[0] == 1


def test_unmodified_readonly_trigger_witness_survives_restart(tmp_path):
    ledger, retained, path = _state(tmp_path)
    assert review.read_proactive_witness(ledger, retained=retained) == retained
    reopened = SyntheticProactiveLedger(path)
    current = review.read_proactive_witness(reopened, retained=retained)
    assert current == retained
    assert reopened.count() == 1
    assert not hasattr(current, "dispatch_authorized")
