"""Synthetic SQLite audit continuity; no tool backend or real approval."""

import sqlite3

import pytest

import ark.agency.audit_continuity_review as review
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall


def _audit(tmp_path):
    return SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 100)


def _append(audit, label):
    return audit.append(
        ToolCall(
            "fixture.read",
            "fixture.read",
            "synthetic:scope",
            {"label": label},
        ),
        outcome="synthetic-only",
    )


def test_empty_witness_is_stable_and_not_execution_evidence(tmp_path):
    audit = _audit(tmp_path)
    first = review.review_audit_continuity(audit)
    assert first.event_count == first.tail_event_id == 0
    assert len(first.chain_sha256) == 64
    assert review.review_audit_continuity(audit, retained=first) == first


def test_append_preserves_externally_retained_prefix(tmp_path):
    audit = _audit(tmp_path)
    _append(audit, "first")
    anchor = review.review_audit_continuity(audit)
    _append(audit, "second")
    later = review.review_audit_continuity(audit, retained=anchor)
    assert later.event_count == 2
    assert later.tail_event_id > anchor.tail_event_id
    assert later.chain_sha256 != anchor.chain_sha256


def test_retained_witness_detects_rewritten_history(tmp_path):
    audit = _audit(tmp_path)
    _append(audit, "first")
    anchor = review.review_audit_continuity(audit)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("UPDATE action_events SET outcome='forged' WHERE event_id=1")
    with pytest.raises(ActionAuditSchemaError, match="prefix differs"):
        review.review_audit_continuity(audit, retained=anchor)


def test_retained_witness_detects_truncation(tmp_path):
    audit = _audit(tmp_path)
    _append(audit, "first")
    _append(audit, "second")
    anchor = review.review_audit_continuity(audit)
    with sqlite3.connect(audit.path) as conn:
        conn.execute("DELETE FROM action_events WHERE event_id=2")
    with pytest.raises(ActionAuditSchemaError, match="shorter"):
        review.review_audit_continuity(audit, retained=anchor)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("outcome", sqlite3.Binary(b"allowed")),
        ("occurred_at_ms", sqlite3.Binary(b"100")),
        ("arguments_sha256", "bad-digest"),
    ],
)
def test_malformed_sqlite_storage_and_identity_fail_closed(tmp_path, column, value):
    audit = _audit(tmp_path)
    _append(audit, "first")
    with sqlite3.connect(audit.path) as conn:
        conn.execute(f"UPDATE action_events SET {column}=?", (value,))
    with pytest.raises(ActionAuditSchemaError):
        review.review_audit_continuity(audit)


def test_limit_rejects_unreviewed_suffix(tmp_path):
    audit = _audit(tmp_path)
    _append(audit, "first")
    _append(audit, "second")
    with pytest.raises(ActionAuditSchemaError, match="budget"):
        review.review_audit_continuity(audit, max_events=1)


def test_retained_empty_witness_does_not_authorize_nonempty_history(tmp_path):
    audit = _audit(tmp_path)
    empty = review.review_audit_continuity(audit)
    _append(audit, "new")
    assert review.review_audit_continuity(audit, retained=empty).event_count == 1


def test_reflected_retained_witness_mutation_during_review_is_rejected(
    tmp_path, monkeypatch
):
    audit = _audit(tmp_path)
    _append(audit, "first")
    retained = review.review_audit_continuity(audit)
    original = review._row_payload

    def mutate(row, *, previous_id):
        object.__setattr__(retained, "tail_event_id", 777)
        return original(row, previous_id=previous_id)

    monkeypatch.setattr(review, "_row_payload", mutate)
    with pytest.raises(ActionAuditSchemaError, match="changed during"):
        review.review_audit_continuity(audit, retained=retained)


def test_argument_plaintext_is_not_stored_in_history_witness(tmp_path):
    audit = _audit(tmp_path)
    secret_fixture = "synthetic-no-real-secret-string"
    _append(audit, secret_fixture)
    witness = review.review_audit_continuity(audit)
    assert secret_fixture not in repr(witness)
    assert not hasattr(witness, "arguments")
    assert not hasattr(witness, "backend")
