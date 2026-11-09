"""Detached, caller-held, public-only segmented diagnostic recovery checks.

No file IO, trusted audit, private export, approval, cleanup, or tool dispatch.
"""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark import private_diagnostic_ledger as writer
from ark import private_diagnostic_segment_review as review

ANCHOR = "a" * 64
SECRET = "NEVER_LEAK_PRIVATE_CONTEXT_RUN741"


def _fixtures():
    batches = (
        (writer.PrivateDiagnosticEvent(9, "memory", "recovery", "deferred", "nonreplay_required"),
         writer.PrivateDiagnosticEvent(10, "privacy", "postcheck", "reviewed", "missing_evidence")),
        (writer.PrivateDiagnosticEvent(11, "planner", "preflight", "rejected", "conflict"),),
        (writer.PrivateDiagnosticEvent(12, "registry", "ingress", "rejected", "invalid_type"),
         writer.PrivateDiagnosticEvent(13, "startup", "recovery", "deferred", "quarantined")),
    )
    previous = ANCHOR
    segments = []
    for batch in batches:
        p = writer.render_private_diagnostic_ledger(
            batch, start_sequence=batch[0].sequence,
            retained_anchor_sha256=previous,
        )
        segments.append(review.RetainedDiagnosticSegment(
            p.first_sequence, p.count, previous, p.final_sha256,
            p.canonical_jsonl,
        ))
        previous = p.final_sha256
    return tuple(segments)


def _check(segments=None, **updates):
    parts = _fixtures() if segments is None else segments
    claims = {
        "expected_start_sequence": 9,
        "expected_count": 5,
        "retained_anchor_sha256": ANCHOR,
        "expected_final_sha256": _fixtures()[-1].tip_sha256,
    }
    claims.update(updates)
    return review.verify_retained_diagnostic_segments(parts, **claims)


def test_exact_three_segment_roundtrip_and_false_authority():
    parts = _fixtures()
    result = _check(parts)
    assert (result.first_sequence, result.last_sequence) == (9, 13)
    assert result.count == 5
    assert result.segment_count == 3
    assert result.final_sha256 == parts[-1].tip_sha256
    assert result.audit_authenticated is False
    assert result.cleanup_authorized is False
    assert result.tool_execution_authorized is False
    assert result.private_data_export_authorized is False
    assert parts[0].canonical_jsonl not in repr(parts[0])
    assert "canonical_jsonl" not in repr(parts[0])


def test_one_segment_exact_bounds():
    part = _fixtures()[0]
    result = _check(
        (part,), expected_count=2,
        expected_final_sha256=part.tip_sha256,
    )
    assert (result.first_sequence, result.last_sequence, result.segment_count) == (
        9, 10, 1,
    )


@pytest.mark.parametrize("case", [
    "drop_last", "drop_first", "duplicate", "reorder", "count",
    "start", "anchor", "tip", "truncate", "append", "unicode", "blank",
    "raw_secret", "first_count", "last_anchor",
])
def test_boundary_conflicts_or_private_payload_cannot_pass(case):
    parts = list(_fixtures())
    if case == "drop_last":
        parts.pop()
    elif case == "drop_first":
        parts.pop(0)
    elif case == "duplicate":
        parts.insert(1, parts[0])
    elif case == "reorder":
        parts[0], parts[1] = parts[1], parts[0]
    elif case == "count":
        parts[1] = replace(parts[1], count=3)
    elif case == "start":
        parts[1] = replace(parts[1], first_sequence=12)
    elif case == "anchor":
        parts[1] = replace(parts[1], anchor_sha256="b" * 64)
    elif case == "tip":
        parts[1] = replace(parts[1], tip_sha256="b" * 64)
    elif case == "truncate":
        parts[1] = replace(
            parts[1], canonical_jsonl=parts[1].canonical_jsonl[:-1],
        )
    elif case == "append":
        parts[1] = replace(
            parts[1], canonical_jsonl=parts[1].canonical_jsonl + "{}\n",
        )
    elif case == "unicode":
        parts[1] = replace(
            parts[1], canonical_jsonl=parts[1].canonical_jsonl + "秘密",
        )
    elif case == "blank":
        parts[1] = replace(parts[1], canonical_jsonl="")
    elif case == "raw_secret":
        parts[1] = replace(parts[1], canonical_jsonl=SECRET)
    elif case == "first_count":
        parts[0] = replace(parts[0], count=1)
    else:
        parts[2] = replace(parts[2], anchor_sha256="f" * 64)
    with pytest.raises(review.RetainedDiagnosticChainRejected) as error:
        _check(tuple(parts))
    assert SECRET not in str(error.value)


@pytest.mark.parametrize(("field", "value"), [
    ("expected_start_sequence", True),
    ("expected_start_sequence", 0),
    ("expected_start_sequence", 2**63),
    ("expected_count", True),
    ("expected_count", 0),
    ("expected_count", 129),
    ("expected_count", 4),
    ("retained_anchor_sha256", "B" * 64),
    ("retained_anchor_sha256", SECRET),
    ("expected_final_sha256", "b" * 64),
    ("expected_final_sha256", 42),
])
def test_retained_global_envelope_is_exact(field, value):
    with pytest.raises(review.RetainedDiagnosticChainRejected):
        _check(**{field: value})


@pytest.mark.parametrize("invalid", [
    [], (), (object(),), tuple(_fixtures()[:1] * 9),
])
def test_invalid_segment_container_or_limit_rejected(invalid):
    with pytest.raises(review.RetainedDiagnosticChainRejected):
        _check(invalid)


def test_cumulative_byte_budget_before_verification():
    parts = list(_fixtures())
    parts[-1] = replace(
        parts[-1], canonical_jsonl="x" * 49_600,
    )
    with pytest.raises(
        review.RetainedDiagnosticChainRejected, match="budget",
    ):
        _check(tuple(parts))


@pytest.mark.parametrize(("name", "replacement"), [
    ("_MAX_SEGMENTS", 1000),
    ("_MAX_EVENTS", 999),
    ("_MAX_BYTES", 999_999),
    ("_MAX_SEQUENCE", True),
    ("_SHA", object()),
])
def test_coordinator_protocol_change_is_refused_before_payload(name, replacement, monkeypatch):
    monkeypatch.setattr(review, name, replacement)
    with pytest.raises(review.RetainedDiagnosticChainRejected, match="protocol"):
        _check()


def test_replaced_verifier_cannot_see_any_payload(monkeypatch):
    invoked = []

    def poison(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("private data read by substituted verifier")

    monkeypatch.setattr(
        review.verifier, "verify_private_diagnostic_jsonl", poison,
    )
    with pytest.raises(review.RetainedDiagnosticChainRejected, match="protocol"):
        _check()
    assert invoked == []


def test_replaced_verifier_namespace_is_rejected(monkeypatch):
    monkeypatch.setattr(
        review, "verifier", SimpleNamespace(verify_private_diagnostic_jsonl=lambda *_: None),
    )
    with pytest.raises(review.RetainedDiagnosticChainRejected, match="protocol"):
        _check()


def test_result_contains_no_private_context_or_execution_claim():
    result = _check()
    assert SECRET not in repr(result)
    assert "canonical_jsonl" not in repr(result)
    assert result.tool_execution_authorized is False
    assert result.private_data_export_authorized is False
