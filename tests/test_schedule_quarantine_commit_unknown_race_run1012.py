"""Run1012: proactive quarantine COMMIT-UNKNOWN and competing-process custody.

Synthetic schedule timestamps and disposable local SQLite only. A quarantine
record is an overdue classification, never a trusted clock, notification,
consent, execution, or automatic-replay capability.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ark import disconnected_schedule_quarantine_ledger as quarantine


def _policy() -> quarantine.QuarantinePolicy:
    return quarantine.QuarantinePolicy("a" * 64, 10_000, 5_000, 2, 500)


def _expired_claim(policy: quarantine.QuarantinePolicy):
    return (
        0,
        quarantine.derive_quarantined_occurrence(policy, 0),
        10_501,
    )


def test_lost_commit_acknowledgement_is_unknown_and_original_witness_cannot_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "commit-unknown-quarantine.sqlite3"
    policy = _policy()
    ledger = quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    retained = quarantine.genesis_quarantine_witness(policy)
    index, occurrence_id, observed_ms = _expired_claim(policy)
    native_connect = quarantine.sqlite3.connect
    target = path.as_uri() + "?mode=rw"

    class CommitAcknowledgementLost:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def commit(self) -> None:
            # The underlying durable COMMIT succeeds, but its acknowledgement
            # is lost before the caller can receive a quarantine receipt.
            self.connection.commit()
            raise sqlite3.OperationalError("synthetic COMMIT acknowledgement lost")

        def rollback(self) -> None:
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def execute(self, *args, **kwargs):
            return self.connection.execute(*args, **kwargs)

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect(database, *args, **kwargs):
        connection = native_connect(database, *args, **kwargs)
        if database == target:
            return CommitAcknowledgementLost(connection)
        return connection

    with monkeypatch.context() as patch:
        patch.setattr(quarantine.sqlite3, "connect", connect)
        with pytest.raises(
            sqlite3.OperationalError, match="COMMIT acknowledgement lost",
        ):
            ledger.quarantine_expired(
                index=index,
                occurrence_id=occurrence_id,
                observed_ms=observed_ms,
                retained=retained,
            )

    # The method raised and returned no receipt. Cold inspection may establish
    # only what this same local ledger currently contains, not independent
    # custody or permission to retry an external effect.
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT seq,occurrence_id,due_ms,observed_ms,chain_sha256 "
            "FROM quarantines ORDER BY seq"
        ).fetchall()
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert len(rows) == 1
    assert rows[0][:4] == (1, occurrence_id, 10_000, observed_ms)
    assert len(rows[0][4]) == 64

    local_only = quarantine.QuarantineWitness(1, rows[0][4])
    assert local_only.independently_authenticated is False
    cold = quarantine.DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert cold.inspect(retained=local_only) == local_only
    with pytest.raises(quarantine.ScheduleQuarantineRejected, match="stale"):
        cold.inspect(retained=retained)
    with pytest.raises(quarantine.ScheduleQuarantineRejected, match="stale"):
        cold.quarantine_expired(
            index=index,
            occurrence_id=occurrence_id,
            observed_ms=observed_ms + 1,
            retained=retained,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)


_RACE_CHILD = """
import sys
import time
from pathlib import Path
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger, QuarantinePolicy,
    ScheduleQuarantineRejected, derive_quarantined_occurrence,
    genesis_quarantine_witness,
)
database, ready_name, release_name, observed_text = sys.argv[1:]
policy = QuarantinePolicy("a" * 64, 10_000, 5_000, 2, 500)
ledger = DisconnectedScheduleQuarantineLedger(Path(database), policy=policy)
retained = genesis_quarantine_witness(policy)
ready = Path(ready_name)
release = Path(release_name)
ready.touch()
deadline = time.monotonic() + 25
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit(8)
    time.sleep(0.01)
try:
    receipt = ledger.quarantine_expired(
        index=0,
        occurrence_id=derive_quarantined_occurrence(policy, 0),
        observed_ms=int(observed_text),
        retained=retained,
    )
except ScheduleQuarantineRejected:
    sys.exit(4)
assert receipt.quarantined_index == 0
assert receipt.execution_authorized is False
assert receipt.notification_authorized is False
assert receipt.automatic_replay_authorized is False
assert receipt.trusted_clock_verified is False
assert receipt.consent_verified is False
sys.exit(0)
"""


def test_two_processes_cannot_commit_the_same_expired_occurrence_from_one_witness(
    tmp_path: Path,
) -> None:
    path = tmp_path / "competing-quarantine.sqlite3"
    policy = _policy()
    quarantine.DisconnectedScheduleQuarantineLedger(
        path, policy=policy, create=True,
    )
    release = tmp_path / "release"
    ready = (tmp_path / "ready-a", tmp_path / "ready-b")
    observed = (10_501, 10_502)
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _RACE_CHILD, str(path), str(ready[i]),
                str(release), str(observed[i]),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all(marker.exists() for marker in ready):
            if any(process.poll() is not None for process in processes):
                outputs = [process.communicate(timeout=5) for process in processes]
                raise AssertionError(f"quarantine race worker exited before barrier: {outputs}")
            if time.monotonic() >= deadline:
                raise AssertionError("quarantine race workers did not reach barrier")
            time.sleep(0.01)
        release.touch()
        outputs = [process.communicate(timeout=35) for process in processes]
        assert sorted(process.returncode for process in processes) == [0, 4], outputs
    finally:
        release.touch()
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT seq,occurrence_id,due_ms,observed_ms,chain_sha256 "
            "FROM quarantines ORDER BY seq"
        ).fetchall()
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert len(rows) == 1
    assert rows[0][0] == 1
    assert rows[0][1] == quarantine.derive_quarantined_occurrence(policy, 0)
    assert rows[0][2] == 10_000
    assert rows[0][3] in observed
    assert len(rows[0][4]) == 64

    local_only = quarantine.QuarantineWitness(1, rows[0][4])
    cold = quarantine.DisconnectedScheduleQuarantineLedger(path, policy=policy)
    assert cold.inspect(retained=local_only) == local_only
    assert local_only.independently_authenticated is False
    with pytest.raises(quarantine.ScheduleQuarantineRejected, match="stale"):
        cold.inspect(retained=quarantine.genesis_quarantine_witness(policy))
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM quarantines").fetchone() == (1,)
