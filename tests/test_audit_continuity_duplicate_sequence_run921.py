"""Read-only audit continuity cannot hide extra AUTOINCREMENT markers.

The local sequence is a consistency signal, not trusted provenance or
permission to execute a tool.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path) -> SQLiteActionAudit:
    audit = SQLiteActionAudit(tmp_path / "audit-continuity-sequence.sqlite")
    audit.append(
        ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": 1}),
        outcome="synthetic-only",
    )
    return audit


@pytest.mark.parametrize("forged_seq", (1, 2, 777))
def test_matching_first_marker_does_not_hide_duplicate(tmp_path, forged_seq: int) -> None:
    audit = _audit(tmp_path)
    with closing(sqlite3.connect(audit.path)) as conn, conn:
        conn.execute(
            "INSERT INTO sqlite_sequence (name, seq) VALUES ('action_events', ?)",
            (forged_seq,),
        )
        markers = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
        ).fetchall()
        assert markers == [(1,), (forged_seq,)]
    with pytest.raises(ActionAuditSchemaError, match="high-water mismatch"):
        review_audit_continuity(audit)


def test_three_markers_rejected_without_a_retained_witness(tmp_path) -> None:
    audit = _audit(tmp_path)
    with closing(sqlite3.connect(audit.path)) as conn, conn:
        conn.executemany(
            "INSERT INTO sqlite_sequence (name, seq) VALUES ('action_events', ?)",
            ((1,), (1,)),
        )
    with pytest.raises(ActionAuditSchemaError, match="high-water mismatch"):
        review_audit_continuity(audit)


def test_valid_append_after_restart_preserves_continuity(tmp_path) -> None:
    audit = _audit(tmp_path)
    retained = review_audit_continuity(audit)
    reopened = SQLiteActionAudit(audit.path)
    reopened.append(
        ToolCall("fixture.read", "fixture.read", "synthetic:scope", {"n": 2}),
        outcome="synthetic-only",
    )
    witness = review_audit_continuity(reopened, retained=retained)
    assert witness.event_count == 2
    assert witness.tail_event_id == 2
    assert witness.chain_sha256 != retained.chain_sha256
