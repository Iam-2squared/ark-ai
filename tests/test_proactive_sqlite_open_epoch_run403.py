"""Proactive preparation and count require stable SQLite-open source identity.

Offline, non-dispatching fixture checks only: no notification, credentials,
live observations, trusted clock or ToolBackend is involved.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.proactive_synthetic_review as proactive
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path: Path):
    path = tmp_path / "prepared.sqlite"
    return SyntheticProactiveLedger(path), path


def _execute(ledger: SyntheticProactiveLedger, operation: str):
    if operation == "count":
        return ledger.count()
    policy = SyntheticTriggerPolicy(
        "offline-owner", "private", "fixture", 1, "rev1", 1, 100, 3,
    )
    return ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=10, now_ms=10,
    )


@pytest.mark.parametrize("operation", ("prepare", "count"))
@pytest.mark.parametrize("boundary", ("resolve", "as_uri", "connect"))
def test_path_or_connection_callbacks_fail_before_sqlite_transaction(
    tmp_path: Path, monkeypatch, operation: str, boundary: str,
):
    ledger, path = _fixture(tmp_path)
    original_connect = sqlite3.connect
    opened = []
    invocations = []

    if boundary == "connect":
        def connecting(*args, **kwargs):
            conn = original_connect(*args, **kwargs)
            opened.append(conn)
            invocations.append(boundary)
            ledger.path = Path(str(path))
            return conn

        monkeypatch.setattr(proactive.sqlite3, "connect", connecting)
    else:
        original = getattr(Path, boundary)

        def changing(current, *args, **kwargs):
            result = original(current, *args, **kwargs)
            invocations.append(boundary)
            ledger.path = Path(str(path))
            return result

        monkeypatch.setattr(Path, boundary, changing)

    with pytest.raises(SyntheticTriggerRejected, match="path changed before opening"):
        _execute(ledger, operation)

    assert invocations == [boundary]
    for conn in opened:
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            conn.execute("SELECT 1")
    with original_connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers"
        ).fetchone() == (0,)


def test_unmodified_proactive_store_remains_inert_and_restart_safe(tmp_path: Path):
    ledger, path = _fixture(tmp_path)
    assert _execute(ledger, "count") == 0
    receipt = _execute(ledger, "prepare")
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    reopened = SyntheticProactiveLedger(path)
    assert _execute(reopened, "count") == 1
