"""Run1008: a hard crash after durable occurrence commit cannot replay a mock WRITE.

The child exits inside the SQLite commit acknowledgement boundary, after the
occurrence row is durable but before the executor can append its pre-action
audit or call the mock backend. All storage is disposable local SQLite.
"""

from __future__ import annotations

import hashlib
import multiprocessing
import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionGate,
    SQLiteActionAudit,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.disconnected_mock_executor import (
    DisconnectedMockExecutionRejected,
    DisconnectedMockExecutor,
    MockToolBackend,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore

_TOKEN_ID = "synthetic-occurrence-crash-token"
_OCCURRENCE_ID = "occ_" + "f" * 64


def _stack(audit_path: Path, occurrence_path: Path):
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.mock",
            "fixture.mock",
            Effect.WRITE,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    gate = PermissionGate()
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 100)
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    return backend, executor, call, grant, audit, occurrences


class _ExitAfterOccurrenceCommit:
    """Commit the exact occurrence INSERT, then terminate before returning."""

    def __init__(self, connection, marker: str):
        self._connection = connection
        self._marker = marker
        self._inserted = False

    def execute(self, statement, *args):
        cursor = self._connection.execute(statement, *args)
        if (
            type(statement) is str
            and statement.lstrip().startswith(
                "INSERT INTO synthetic_occurrence_reservations"
            )
        ):
            self._inserted = True
        return cursor

    def commit(self):
        self._connection.commit()
        if self._inserted:
            Path(self._marker).write_text("committed", encoding="ascii")
            os._exit(0)

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _crash_after_occurrence_commit(
    audit_path: str, occurrence_path: str, marker: str,
) -> None:
    audit = Path(audit_path)
    occurrences = Path(occurrence_path)
    backend, executor, call, grant, _, _ = _stack(audit, occurrences)
    token = OneShotAuthorization(_TOKEN_ID, call.request_id, 500)

    original_connect = sqlite3.connect
    occurrence_uri = occurrences.resolve().as_uri() + "?mode=rw"

    def connect(*args, **kwargs):
        database = args[0] if args else kwargs.get("database")
        connection = original_connect(*args, **kwargs)
        if type(database) is str and database == occurrence_uri:
            return _ExitAfterOccurrenceCommit(connection, marker)
        return connection

    # Patch only this child process and only the already-initialized occurrence
    # store. The wrapper exits after native COMMIT, before reserve_synthetic
    # returns and before DisconnectedMockExecutor can append its audit event.
    sqlite3.connect = connect
    executor.execute(
        call,
        (grant,),
        now_ms=100,
        one_shot=token,
        occurrence_id=_OCCURRENCE_ID,
    )
    # Reaching this line would mean the intended hard-crash boundary was missed.
    os._exit(9)


@pytest.mark.parametrize(
    "retry_occurrence_id",
    (_OCCURRENCE_ID, "occ_" + "a" * 64),
    ids=("same-occurrence", "same-token-new-occurrence"),
)
def test_committed_occurrence_survives_process_crash_before_audit_and_blocks_replay(
    tmp_path: Path, retry_occurrence_id: str,
) -> None:
    audit_path = tmp_path / "audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    marker = tmp_path / "occurrence-committed"
    _, _, _, _, audit, occurrences = _stack(audit_path, occurrence_path)

    process = multiprocessing.get_context("spawn").Process(
        target=_crash_after_occurrence_commit,
        args=(str(audit_path), str(occurrence_path), str(marker)),
    )
    process.start()
    process.join(timeout=35)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)

    assert process.exitcode == 0
    assert marker.read_text(encoding="ascii") == "committed"

    # The durable token digest and occurrence reservation survive process exit.
    assert occurrences.count_synthetic() == 1
    expected_token_digest = hashlib.sha256(
        ("ARK-synthetic-v1\0" + _TOKEN_ID).encode("utf-8")
    ).hexdigest()
    with sqlite3.connect(occurrence_path) as connection:
        row = connection.execute(
            "SELECT token_digest, occurrence_id "
            "FROM synthetic_occurrence_reservations"
        ).fetchone()
    assert row == (expected_token_digest, _OCCURRENCE_ID)
    assert _TOKEN_ID not in repr(row)

    # There is intentionally no audit row: the process died before that
    # separate store was reached. Absence is not permission to retry.
    assert audit.events() == []

    # A fresh gate has no process-local consumed-token history. The durable
    # occurrence ledger alone must deny both same-occurrence and changed-
    # occurrence reuse of the same one-shot token before audit or mock dispatch.
    backend, restarted, call, grant, reopened_audit, reopened_occurrences = _stack(
        audit_path, occurrence_path,
    )
    token = OneShotAuthorization(_TOKEN_ID, call.request_id, 500)
    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        restarted.execute(
            call,
            (grant,),
            now_ms=101,
            one_shot=token,
            occurrence_id=retry_occurrence_id,
        )

    assert backend.calls == 0
    assert reopened_occurrences.count_synthetic() == 1
    assert reopened_audit.events() == []
