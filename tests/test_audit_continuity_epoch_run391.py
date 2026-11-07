"""Read-only audit continuity rejects changed source and retained epochs."""

from pathlib import Path

import pytest

import ark.agency.audit_continuity_review as continuity
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path: Path) -> SQLiteActionAudit:
    audit = SQLiteActionAudit(tmp_path / "Audit # %.sqlite", clock_ms=lambda: 100)
    audit.append(ToolCall("fixture", "read", "synthetic", {"n": 1}), outcome="mock")
    audit.append(ToolCall("fixture", "read", "synthetic", {"n": 2}), outcome="mock")
    return audit


@pytest.mark.parametrize("stage", ["schema", "row"])
def test_reentrant_same_text_path_replacement_is_denied(
    tmp_path: Path, monkeypatch, stage: str,
) -> None:
    audit = _audit(tmp_path)
    original_path = audit.path
    original = (
        continuity._validate_v1_schema if stage == "schema"
        else continuity._row_payload
    )

    if stage == "schema":
        def tamper(conn):
            result = original(conn)
            audit.path = Path(str(original_path))
            return result

        monkeypatch.setattr(continuity, "_validate_v1_schema", tamper)
    else:
        def tamper(row, *, previous_id):
            result = original(row, previous_id=previous_id)
            audit.path = Path(str(original_path))
            return result

        monkeypatch.setattr(continuity, "_row_payload", tamper)

    with pytest.raises(ActionAuditSchemaError, match="source changed"):
        continuity.review_audit_continuity(audit)
    assert audit.path == original_path
    assert audit.path is not original_path


def test_reentrant_retained_witness_change_is_denied_before_next_row(
    tmp_path: Path, monkeypatch,
) -> None:
    audit = _audit(tmp_path)
    witness = continuity.review_audit_continuity(audit)
    original = continuity._row_payload
    calls = []

    def swap_and_restore(row, *, previous_id):
        calls.append(previous_id)
        if len(calls) == 1:
            object.__setattr__(witness, "tail_event_id", 777)
        else:
            object.__setattr__(witness, "tail_event_id", 2)
        return original(row, previous_id=previous_id)

    monkeypatch.setattr(continuity, "_row_payload", swap_and_restore)
    with pytest.raises(ActionAuditSchemaError, match="retained.*changed"):
        continuity.review_audit_continuity(audit, retained=witness)
    assert len(calls) == 1


def test_bad_source_type_is_rejected_before_open(tmp_path: Path) -> None:
    audit = _audit(tmp_path)
    audit.path = str(audit.path)
    with pytest.raises(ActionAuditSchemaError, match="Path source"):
        continuity.review_audit_continuity(audit)


def test_valid_retained_prefix_still_accepts_new_audit_event(tmp_path: Path) -> None:
    audit = _audit(tmp_path)
    first = continuity.review_audit_continuity(audit)
    audit.append(
        ToolCall("fixture", "read", "synthetic", {"n": 3}), outcome="mock"
    )
    second = continuity.review_audit_continuity(audit, retained=first)
    assert second.event_count == 3
    assert first.tail_event_id < second.tail_event_id


def test_monotonic_read_remains_optional_and_never_dispatches(tmp_path: Path) -> None:
    audit = _audit(tmp_path)
    result = continuity.review_audit_continuity(
        audit, require_monotonic_time=True,
    )
    assert result.event_count == 2
    assert not hasattr(result, "dispatch_authorized")
