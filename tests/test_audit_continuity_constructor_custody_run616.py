"""Offline audit witness constructors must not become executable authority.

Only temporary SQLite fixture rows are reviewed; no real action is dispatched.
"""

from __future__ import annotations

import pytest
from test_action_audit_continuity_review_run361 import _append, _audit

import ark.agency.audit_continuity_review as review
from ark.agency.contracts import ActionAuditSchemaError


@pytest.mark.parametrize("stage", ("preinstalled", "row_callback"))
def test_forged_witness_init_rejected_before_execution(tmp_path, monkeypatch, stage):
    audit = _audit(tmp_path)
    _append(audit, "synthetic")
    calls = []
    original_row = review._row_payload

    def forged_init(self, *args):
        calls.append(args)

    if stage == "preinstalled":
        monkeypatch.setattr(review.AuditContinuityWitness, "__init__", forged_init)
    else:
        def patch_after_row(row, *, previous_id):
            fields = original_row(row, previous_id=previous_id)
            monkeypatch.setattr(
                review.AuditContinuityWitness, "__init__", forged_init,
            )
            return fields

        monkeypatch.setattr(review, "_row_payload", patch_after_row)

    with pytest.raises(ActionAuditSchemaError, match="witness constructor changed"):
        review.review_audit_continuity(audit)
    assert calls == []


def test_substituted_witness_factory_rejected_before_call(tmp_path, monkeypatch):
    audit = _audit(tmp_path)
    calls = []

    def fabricated(*args):
        calls.append(args)

    monkeypatch.setattr(review, "AuditContinuityWitness", fabricated)
    with pytest.raises(ActionAuditSchemaError, match="witness constructor changed"):
        review.review_audit_continuity(audit)
    assert calls == []


def test_normal_audit_witness_still_reports_only_local_history(tmp_path):
    audit = _audit(tmp_path)
    _append(audit, "synthetic")
    first = review.review_audit_continuity(audit)
    second = review.review_audit_continuity(audit, retained=first)
    assert type(first) is review.AuditContinuityWitness
    assert first == second
    assert first.event_count == first.tail_event_id == 1
    assert len(first.chain_sha256) == 64
    assert not hasattr(first, "dispatch_authorized")
