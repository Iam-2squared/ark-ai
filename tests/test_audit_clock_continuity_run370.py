"""Optional read-only audit clock ordering; no clock trust or tool dispatch."""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path):
    stamps = iter((100, 101, 102))
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: next(stamps))
    for n in range(3):
        audit.append(
            ToolCall("fixture", "read", "test", {"n": n}),
            outcome="synthetic",
        )
    return audit


def test_monotonic_review_accepts_equal_or_increasing_times(tmp_path):
    audit = _audit(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("UPDATE action_events SET occurred_at_ms=101 WHERE event_id=3")
    witness = review_audit_continuity(audit, require_monotonic_time=True)
    assert witness.event_count == 3


def test_monotonic_review_refuses_rollback_but_legacy_review_remains_available(tmp_path):
    audit = _audit(tmp_path)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("UPDATE action_events SET occurred_at_ms=0 WHERE event_id=2")
    assert review_audit_continuity(audit).event_count == 3
    with pytest.raises(ActionAuditSchemaError, match="clock regressed"):
        review_audit_continuity(audit, require_monotonic_time=True)


def test_monotonic_review_preserves_retained_prefix_detection(tmp_path):
    audit = _audit(tmp_path)
    retained = review_audit_continuity(audit, require_monotonic_time=True)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("UPDATE action_events SET outcome='tampered' WHERE event_id=1")
    with pytest.raises(ActionAuditSchemaError, match="prefix differs"):
        review_audit_continuity(
            audit, retained=retained, require_monotonic_time=True,
        )


@pytest.mark.parametrize("invalid", [1, "yes", None])
def test_clock_review_flag_must_be_exact_bool(tmp_path, invalid):
    audit = _audit(tmp_path)
    with pytest.raises(TypeError, match="exact boolean"):
        review_audit_continuity(audit, require_monotonic_time=invalid)
