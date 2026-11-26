"""Run1452: a Personal Context revocation survives native-COMMIT hard exit.

Only synthetic Memory rows and a disposable local revocation ledger are used.
The durable marker is a negative-use veto, not consent or erasure authority.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from pathlib import Path

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)

_OWNER = "offline-owner"
_NAMESPACE = "private"


def _hard_exit_after_revoke_commit(database: str) -> None:
    ledger = SyntheticContextRevocationLedger(
        Path(database),
        require_existing=True,
    )
    native_connect = ledger._connect

    class CommitThenExit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def commit(self) -> None:
            self.connection.commit()
            # The veto row is committed; exit before source recheck or return.
            os._exit(81)

        def rollback(self) -> None:
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    ledger._connect = lambda *, readonly: CommitThenExit(
        native_connect(readonly=readonly),
    )
    ledger.revoke(MemoryScope(_OWNER, _NAMESPACE), at_ms=101)
    os._exit(82)


def test_revocation_veto_survives_native_commit_process_exit_and_blocks_context(
    tmp_path: Path,
) -> None:
    memory_path = tmp_path / "synthetic-memory.sqlite3"
    veto_path = tmp_path / "synthetic-context-veto.sqlite3"
    scope = MemoryScope(_OWNER, _NAMESPACE)
    memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 100)
    memory.put(MemoryWrite(scope, "profile", "synthetic-private-context"))
    ledger = SyntheticContextRevocationLedger(veto_path)
    retained = review_revocation_continuity(ledger)
    assert retained.rows == ()

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_revoke_commit,
        args=(str(veto_path),),
    )
    process.start()
    process.join(timeout=35)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("Personal Context revocation hard-exit fixture did not terminate")
    assert process.exitcode == 81

    cold = SyntheticContextRevocationLedger(
        veto_path,
        require_existing=True,
    )
    current = review_revocation_continuity(cold, retained=retained)
    assert len(current.rows) == 1
    scope_digest, revoked_at_ms = current.rows[0]
    assert type(scope_digest) is str and len(scope_digest) == 64
    assert revoked_at_ms == 101

    with sqlite3.connect(veto_path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        rows = connection.execute(
            "SELECT scope_digest,revoked_at_ms "
            "FROM synthetic_context_revocations"
        ).fetchall()
    assert rows == [current.rows[0]]

    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked((scope,))

    # The higher-level local projection must observe the durable veto before
    # reading Memory content; it returns no context bundle after the crash.
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(
            memory,
            CoherentSnapshotRequest(_OWNER, (_NAMESPACE,)),
            ContextSelectionPolicy(3, 3),
            cold,
            retained_revocations=retained,
        )

    veto_files = tuple(tmp_path.glob(veto_path.name + "*"))
    persisted_veto = b"".join(path.read_bytes() for path in veto_files if path.is_file())
    assert _OWNER.encode("utf-8") not in persisted_veto
    assert _NAMESPACE.encode("utf-8") not in persisted_veto
    assert b"synthetic-private-context" not in persisted_veto
