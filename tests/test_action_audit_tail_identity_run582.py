"""Append must reject corrupt persisted tail identity before producing more audit rows.

Only temporary local SQLite and synthetic ToolCall values are used. A digest
check is NOT caller attestation or a historical, authenticated hash chain.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _call(n: int) -> ToolCall:
    return ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": n})


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("outcome", "", "identity is malformed"),
        ("tool", sqlite3.Binary(b"not-text"), "identity is malformed"),
        ("request_id", "act_" + "e" * 64, "request identity is inconsistent"),
        ("arguments_sha256", "f" * 64, "request identity is inconsistent"),
        ("arguments_sha256", "A" * 64, "digest is malformed"),
    ],
)
def test_append_refuses_corrupt_tail_without_creating_new_evidence(
    tmp_path, column, value, message,
):
    path = tmp_path / "action.sqlite"
    initial = SQLiteActionAudit(path, clock_ms=lambda: 100)
    initial.append(_call(1), outcome="fixture")
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=1", (value,)
        )
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 101)
    with pytest.raises(ActionAuditSchemaError, match=message):
        restarted.append(_call(2), outcome="fixture")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone()[0] == 1


def test_append_after_restart_accepts_untampered_tail(tmp_path):
    path = tmp_path / "action.sqlite"
    first = SQLiteActionAudit(path, clock_ms=lambda: 100)
    saved = first.append(_call(1), outcome="fixture")
    restarted = SQLiteActionAudit(path, clock_ms=lambda: 100)
    new = restarted.append(_call(2), outcome="fixture")
    assert [row.event_id for row in restarted.events()] == [saved.event_id, new.event_id]
    assert new.occurred_at_ms == saved.occurred_at_ms


def test_append_bad_tail_does_not_rewrite_existing_rows(tmp_path):
    path = tmp_path / "action.sqlite"
    first = SQLiteActionAudit(path, clock_ms=lambda: 50)
    first.append(_call(1), outcome="fixture")
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE action_events SET scope=? WHERE event_id=1", ("tampered:scope",)
        )
        original = conn.execute("SELECT * FROM action_events").fetchall()
    with pytest.raises(ActionAuditSchemaError, match="request identity is inconsistent"):
        first.append(_call(2), outcome="fixture")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT * FROM action_events").fetchall() == original
