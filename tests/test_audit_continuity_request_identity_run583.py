"""Read-only audit continuity must reject internally contradictory event identities.

All data is synthetic local SQLite. SHA-256 checks cannot authenticate a
writer or prove any backend effect, consent, or independent witness custody.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _make_audit(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "synthetic-audit.sqlite", clock_ms=lambda: 100)
    audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 1}),
        outcome="fixture-only",
    )
    audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 2}),
        outcome="fixture-only",
    )
    return audit


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("request_id", "act_" + "f" * 64),
        ("arguments_sha256", "f" * 64),
        ("tool", "swapped.read"),
        ("capability", "swapped.read"),
        ("scope", "swapped:scope"),
    ],
)
def test_middle_row_identity_rewrite_is_rejected_without_retained_witness(
    tmp_path, column, replacement,
):
    audit = _make_audit(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        saved = conn.execute("SELECT * FROM action_events ORDER BY event_id").fetchall()
        conn.execute(
            f"UPDATE action_events SET {column}=? WHERE event_id=1",
            (replacement,),
        )
        altered = conn.execute("SELECT * FROM action_events ORDER BY event_id").fetchall()
    assert altered != saved
    # The last row stays syntactically and semantically correct. Continuity
    # must inspect every row, not only the persisted tail or a supplied tip.
    with pytest.raises(ActionAuditSchemaError, match="request identity is inconsistent"):
        review_audit_continuity(audit)
    with sqlite3.connect(audit.path) as conn:
        assert conn.execute("SELECT * FROM action_events ORDER BY event_id").fetchall() == altered


def test_valid_history_preserves_independently_retained_prefix(tmp_path):
    audit = _make_audit(tmp_path)
    first = review_audit_continuity(audit, require_monotonic_time=True)
    assert first.event_count == 2
    audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:scope", {"n": 3}),
        outcome="fixture-only",
    )
    later = review_audit_continuity(
        audit, retained=first, require_monotonic_time=True,
    )
    assert later.event_count == 3
    assert later.tail_event_id > first.tail_event_id
    assert later.chain_sha256 != first.chain_sha256


def test_retained_witness_does_not_make_inconsistent_history_acceptable(tmp_path):
    audit = _make_audit(tmp_path)
    retained = review_audit_continuity(audit)
    with sqlite3.connect(audit.path) as conn:
        conn.execute(
            "UPDATE action_events SET capability=? WHERE event_id=1",
            ("different.capability",),
        )
    with pytest.raises(ActionAuditSchemaError, match="request identity is inconsistent"):
        review_audit_continuity(audit, retained=retained)
