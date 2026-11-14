"""Reentrant detached diagnostic segment consistency; no real audit/export."""

from __future__ import annotations

import pytest

from ark import private_diagnostic_ledger as writer
from ark import private_diagnostic_ledger_verify as verifier
from ark import private_diagnostic_segment_review as coordinator

ANCHOR = "a" * 64
SECRET = "NEVER_EXPORT_PRIVATE_RUN742"


def _segments():
    first = writer.render_private_diagnostic_ledger(
        (writer.PrivateDiagnosticEvent(
            5, "memory", "recovery", "deferred", "nonreplay_required",
        ),),
        start_sequence=5,
        retained_anchor_sha256=ANCHOR,
    )
    second = writer.render_private_diagnostic_ledger(
        (writer.PrivateDiagnosticEvent(
            6, "planner", "preflight", "rejected", "conflict",
        ),),
        start_sequence=6,
        retained_anchor_sha256=first.final_sha256,
    )
    return (
        coordinator.RetainedDiagnosticSegment(
            5, 1, ANCHOR, first.final_sha256, first.canonical_jsonl,
        ),
        coordinator.RetainedDiagnosticSegment(
            6, 1, first.final_sha256, second.final_sha256,
            second.canonical_jsonl,
        ),
    )


def _review(parts):
    return coordinator.verify_retained_diagnostic_segments(
        parts, expected_start_sequence=5, expected_count=2,
        retained_anchor_sha256=ANCHOR,
        expected_final_sha256=parts[-1].tip_sha256,
    )


def test_untouched_segments_still_review_and_carry_no_authority():
    parts = _segments()
    result = _review(parts)
    assert (result.first_sequence, result.last_sequence, result.count) == (5, 6, 2)
    assert result.final_sha256 == parts[-1].tip_sha256
    assert result.audit_authenticated is False
    assert result.cleanup_authorized is False
    assert result.tool_execution_authorized is False
    assert result.private_data_export_authorized is False


@pytest.mark.parametrize(("segment_index", "field_name"), (
    (0, "canonical_jsonl"),
    (0, "first_sequence"),
    (0, "count"),
    (0, "anchor_sha256"),
    (0, "tip_sha256"),
    (1, "canonical_jsonl"),
    (1, "tip_sha256"),
))
def test_reentrant_verifier_cannot_mutate_any_snapshot_carrier(
    segment_index, field_name, monkeypatch,
):
    parts = _segments()
    expected_tip = parts[-1].tip_sha256
    original_guard = verifier._require_original_protocol
    invoked = False

    def reentrant_guard():
        nonlocal invoked
        original_guard()
        if not invoked:
            invoked = True
            subject = parts[segment_index]
            previous = getattr(subject, field_name)
            if type(previous) is str:
                # Even equal-valued replacement loses the original custody
                # epoch. The verifier can still validate its pinned argument.
                replacement = ("x" + previous)[1:]
                assert replacement == previous
                assert replacement is not previous
            else:
                replacement = previous + 1
            object.__setattr__(subject, field_name, replacement)

    monkeypatch.setattr(verifier, "_require_original_protocol", reentrant_guard)
    with pytest.raises(coordinator.RetainedDiagnosticChainRejected, match="carrier") as err:
        coordinator.verify_retained_diagnostic_segments(
            parts, expected_start_sequence=5, expected_count=2,
            retained_anchor_sha256=ANCHOR, expected_final_sha256=expected_tip,
        )
    assert invoked
    assert SECRET not in str(err.value)


def test_mutation_after_prior_segment_was_verified_is_rejected(monkeypatch):
    parts = _segments()
    original_guard = verifier._require_original_protocol
    calls = 0

    def change_earlier_after_first_verification():
        nonlocal calls
        original_guard()
        calls += 1
        # A verifier invokes its guard many times per segment; the mutation
        # deliberately happens after the coordinator has pinned all segments.
        if calls == 2:
            object.__setattr__(parts[0], "tip_sha256", "e" * 64)

    monkeypatch.setattr(
        verifier, "_require_original_protocol",
        change_earlier_after_first_verification,
    )
    expected_tip = parts[-1].tip_sha256
    with pytest.raises(coordinator.RetainedDiagnosticChainRejected, match="carrier"):
        coordinator.verify_retained_diagnostic_segments(
            parts, expected_start_sequence=5, expected_count=2,
            retained_anchor_sha256=ANCHOR, expected_final_sha256=expected_tip,
        )
    assert calls >= 2
