"""Local audit continuity witnesses cannot execute replaced class-level code.

The fixture audits are read-only evidence, not trusted time, permission, or
proof of external tool execution. No actual backend is called.
"""

from __future__ import annotations

import pytest

import ark.agency.audit_continuity_review as review
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall

_FIELDS_AND_HOOKS = (
    "event_count", "tail_event_id", "chain_sha256",
    "__init__", "__post_init__", "__getattribute__", "__getattr__",
)


def _fixture(tmp_path):
    audit = SQLiteActionAudit(
        tmp_path / "local-audit-custody.sqlite3",
        clock_ms=lambda: 42,
    )
    audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:local", {"x": 1}),
        outcome="synthetic",
    )
    return audit, review.review_audit_continuity(audit)


def _inject(monkeypatch, field, calls):
    if field in ("__init__", "__post_init__"):
        def bad_initializer(self, *args):
            calls.append(field)
            raise AssertionError("poisoned audit initializer executed")

        monkeypatch.setattr(review.AuditContinuityWitness, field, bad_initializer)
    elif field in ("__getattribute__", "__getattr__"):
        def bad_getattr(self, name):
            calls.append((field, name))
            raise AssertionError("poisoned audit lookup executed")

        monkeypatch.setattr(
            review.AuditContinuityWitness, field, bad_getattr, raising=False,
        )
    else:
        def bad_descriptor(self):
            calls.append(field)
            raise AssertionError("poisoned audit field executed")

        monkeypatch.setattr(
            review.AuditContinuityWitness, field, property(bad_descriptor),
        )


@pytest.mark.parametrize("field", _FIELDS_AND_HOOKS)
@pytest.mark.parametrize("with_retained", (False, True))
def test_witness_mutation_is_rejected_before_sqlite_or_retained_field_access(
    tmp_path, monkeypatch, field, with_retained,
):
    audit, retained = _fixture(tmp_path)
    calls = []
    opened = []
    _inject(monkeypatch, field, calls)

    def forbid_sqlite(*args, **kwargs):
        opened.append(True)
        raise AssertionError("poisoned witness must not open SQLite")

    monkeypatch.setattr(review.sqlite3, "connect", forbid_sqlite)
    with pytest.raises(ActionAuditSchemaError, match="witness constructor changed"):
        review.review_audit_continuity(
            audit, retained=retained if with_retained else None,
        )
    assert calls == []
    assert opened == []


@pytest.mark.parametrize(
    "field", ("event_count", "chain_sha256", "__getattribute__"),
)
def test_mid_scan_witness_substitution_is_rejected_without_poison_execution(
    tmp_path, monkeypatch, field,
):
    audit, _ = _fixture(tmp_path)
    calls = []
    original = review._row_payload

    def after_row(row, *, previous_id):
        result = original(row, previous_id=previous_id)
        _inject(monkeypatch, field, calls)
        return result

    monkeypatch.setattr(review, "_row_payload", after_row)
    with pytest.raises(ActionAuditSchemaError, match="witness constructor changed"):
        review.review_audit_continuity(audit)
    assert calls == []


def test_original_witness_still_tracks_append_only_audit_prefix(tmp_path):
    audit, retained = _fixture(tmp_path)
    audit.append(
        ToolCall("fixture.read", "fixture.read", "fixture:local", {"x": 2}),
        outcome="synthetic",
    )
    latest = review.review_audit_continuity(audit, retained=retained)
    assert (retained.event_count, latest.event_count) == (1, 2)
    assert latest.tail_event_id == 2
    assert latest.chain_sha256 != retained.chain_sha256
    assert not hasattr(latest, "dispatch_authorized")
