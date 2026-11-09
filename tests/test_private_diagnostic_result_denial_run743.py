"""Detached diagnostics reject replaced denial descriptors before input access."""

from __future__ import annotations

import pytest

from ark import private_diagnostic_ledger as writer
from ark import private_diagnostic_segment_review as coordinator

ANCHOR = "a" * 64


def _segments():
    one = writer.render_private_diagnostic_ledger(
        (writer.PrivateDiagnosticEvent(
            5, "memory", "recovery", "deferred", "nonreplay_required",
        ),),
        start_sequence=5, retained_anchor_sha256=ANCHOR,
    )
    two = writer.render_private_diagnostic_ledger(
        (writer.PrivateDiagnosticEvent(
            6, "planner", "preflight", "rejected", "conflict",
        ),),
        start_sequence=6, retained_anchor_sha256=one.final_sha256,
    )
    return (
        coordinator.RetainedDiagnosticSegment(
            5, 1, ANCHOR, one.final_sha256, one.canonical_jsonl,
        ),
        coordinator.RetainedDiagnosticSegment(
            6, 1, one.final_sha256, two.final_sha256, two.canonical_jsonl,
        ),
    )


def _review(parts):
    return coordinator.verify_retained_diagnostic_segments(
        parts, expected_start_sequence=5, expected_count=2,
        retained_anchor_sha256=ANCHOR,
        expected_final_sha256=parts[-1].tip_sha256,
    )


def test_no_reentrancy_still_returns_public_only_denied_receipt():
    result = _review(_segments())
    assert (result.first_sequence, result.last_sequence) == (5, 6)
    assert (result.count, result.segment_count) == (2, 2)
    assert result.private_data_export_authorized is False
    assert result.audit_authenticated is False
    assert result.cleanup_authorized is False
    assert result.tool_execution_authorized is False


@pytest.mark.parametrize("field", (
    "first_sequence", "last_sequence", "count", "segment_count", "final_sha256",
))
def test_last_denial_descriptor_replacement_rejected_before_callback(monkeypatch, field):
    parts = _segments()
    calls = 0

    def last_denial(self):
        nonlocal calls
        calls += 1
        original = getattr(self, field)
        if type(original) is str:
            replacement = ("!" + original)[1:]
            assert replacement == original
            assert replacement is not original
        else:
            replacement = original + 1
        object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        coordinator.RetainedDiagnosticChainReview,
        "private_data_export_authorized", property(last_denial),
    )
    with pytest.raises(
        coordinator.RetainedDiagnosticChainRejected, match="protocol changed",
    ):
        _review(parts)
    # The protocol rejects the replaced descriptor before any getter runs.\n    assert calls == 0


def test_earlier_denial_descriptor_replacement_rejected_before_callback(monkeypatch):
    parts = _segments()
    called = False

    def early_denial(self):
        nonlocal called
        called = True
        object.__setattr__(self, "final_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        coordinator.RetainedDiagnosticChainReview, "audit_authenticated",
        property(early_denial),
    )
    with pytest.raises(
        coordinator.RetainedDiagnosticChainRejected, match="protocol changed",
    ):
        _review(parts)
    assert called is False
