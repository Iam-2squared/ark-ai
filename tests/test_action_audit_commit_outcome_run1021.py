"""Run1021: ActionAudit COMMIT rollback and lost acknowledgement are distinct.

Synthetic ToolCall identities and disposable SQLite only. Audit rows do not
prove that a tool ran, authorize replay, or authenticate an approval.
"""

import sqlite3

import pytest

_PRIVATE = "audit-payload-must-never-be-persisted"


def _call(number: int):
    from ark.agency.contracts import ToolCall

    return ToolCall(
        "fixture.audit",
        "mock.write",
        "synthetic:run1021",
        {"private_marker": _PRIVATE, "number": number},
    )


class _CommitBoundary:
    """Inject rollback-before-COMMIT or native-COMMIT/lost-acknowledgement."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable
        self.commit_attempts = 0
        self.native_commits = 0
        self.rollbacks = 0

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            return self.connection.__exit__(exc_type, exc, traceback)
        self.commit_attempts += 1
        if self.durable:
            self.connection.__exit__(None, None, None)
            self.native_commits += 1
        else:
            self.connection.rollback()
            self.rollbacks += 1
        raise sqlite3.OperationalError(
            "synthetic action-audit COMMIT acknowledgement lost"
        )

    def close(self) -> None:
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize(
    "durable",
    (False, True),
    ids=("rollback-before-native-commit", "native-commit-ack-lost"),
)
def test_action_audit_commit_outcome_requires_cold_readback_not_duplicate_append(
    tmp_path, monkeypatch, durable: bool,
) -> None:
    path = tmp_path / "action-audit-commit-outcome.sqlite3"
    clock_values = iter((200, 201))
    from ark.agency.audit import SQLiteActionAudit

    audit = SQLiteActionAudit(path, clock_ms=lambda: next(clock_values))
    first = audit.append(_call(1), outcome="synthetic_before_mock")
    second_call = _call(2)
    original_connect = audit._connect
    boundaries: list[_CommitBoundary] = []

    def uncertain_connect():
        boundary = _CommitBoundary(original_connect(), durable=durable)
        boundaries.append(boundary)
        return boundary

    with monkeypatch.context() as patch:
        patch.setattr(audit, "_connect", uncertain_connect)
        with pytest.raises(
            sqlite3.OperationalError,
            match="action-audit COMMIT acknowledgement lost",
        ):
            audit.append(second_call, outcome="synthetic_before_mock")

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1
    assert boundaries[0].native_commits == (1 if durable else 0)
    assert boundaries[0].rollbacks == (0 if durable else 1)

    cold = SQLiteActionAudit(path, clock_ms=lambda: 202)
    events = cold.events()
    assert events[0] == first
    assert [event.event_id for event in events] == ([1, 2] if durable else [1])
    assert sum(event.request_id == second_call.request_id for event in events) == (
        1 if durable else 0
    )

    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT event_id,request_id,tool,capability,scope,arguments_sha256,"
            "outcome,occurred_at_ms FROM action_events ORDER BY event_id"
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    assert len(rows) == (2 if durable else 1)
    assert rows[0][0] == 1
    assert rows[0][1] == first.request_id
    assert rows[0][5] == first.arguments_sha256
    assert rows[0][7] == 200
    if durable:
        assert rows[1][0] == 2
        assert rows[1][1] == second_call.request_id
        assert rows[1][5] == second_call.arguments_sha256
        assert rows[1][7] == 201
    assert _PRIVATE.encode("utf-8") not in path.read_bytes()
    assert not hasattr(cold, "execute")
