"""Offline V3 synthetic paired comparison has no execution or V2 authority."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.learning.detached_comparison_recheck as detached
from ark.learning.execution import canonical_json, sha256_bytes
from ark.learning.validation import (
    ValidationCase, ValidationReport, compare_validation,
)


def _reports():
    current = ValidationReport(
        "paired_current", "current-fixture", "a" * 64, "local-runtime",
        "b" * 64,
        tuple(ValidationCase(
            f"case-{i:02d}", "math" if i < 15 else "coding", i != 1,
        ) for i in range(30)),
    )
    candidate = ValidationReport(
        "candidate", "candidate-fixture", "a" * 64, "local-runtime",
        "b" * 64,
        tuple(ValidationCase(
            f"case-{i:02d}", "math" if i < 15 else "coding",
            i != 0, runtime_failure=i == 2, memory_failure=i == 3,
        ) for i in range(30)),
    )
    return current, candidate


def _retained(current, candidate):
    data = canonical_json(compare_validation(current, candidate))
    return data, sha256_bytes(data)


def test_stable_rederived_validation_is_inert_and_repeatable():
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    for _ in range(2):
        assert detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        ) is None
    assert b'NOT_AUTHORIZED_FROM_VALIDATION' in payload
    assert b'v3_validation_only' in payload
    assert b'"historical_v2_opened":false' in payload
    assert b'"blocks_v2_opening":true' in payload


@pytest.mark.parametrize("mode", (
    "wrong_bytes", "wrong_hash", "trailing", "wrong_type", "oversized",
))
def test_unretained_or_noncanonical_report_rejected(mode):
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    if mode == "wrong_bytes":
        payload = payload.replace(b'v3_validation_only', b'v3_validation_none')
    elif mode == "wrong_hash":
        sha = "0" * 64
    elif mode == "trailing":
        payload += b" "
    elif mode == "wrong_type":
        payload = bytearray(payload)
    else:
        payload = b"z" * (128 * 1024 + 1)
    with pytest.raises(detached.DetachedComparisonRejected):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )


@pytest.mark.parametrize("mode", (
    "wrong_role", "wrong_scorer", "wrong_category", "wrong_count",
    "wrong_case_type", "wrong_boolean", "duplicate_id",
))
def test_invalid_pair_never_verifies_retained_report(mode):
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    if mode == "wrong_role":
        candidate = replace(candidate, model_role="paired_current")
    elif mode == "wrong_scorer":
        candidate = replace(candidate, scorer_sha256="e" * 64)
    elif mode == "wrong_category":
        cases = list(candidate.cases)
        cases[0] = replace(cases[0], category="unexpected")
        candidate = replace(candidate, cases=tuple(cases))
    elif mode == "wrong_count":
        candidate = replace(candidate, cases=candidate.cases[:29])
    elif mode == "wrong_case_type":
        candidate = replace(candidate, cases=(object(),) + candidate.cases[1:])
    elif mode == "wrong_boolean":
        cases = list(candidate.cases)
        cases[0] = replace(cases[0], passed=1)
        candidate = replace(candidate, cases=tuple(cases))
    else:
        cases = list(candidate.cases)
        cases[0] = replace(cases[0], case_id=cases[1].case_id)
        candidate = replace(candidate, cases=tuple(cases))
    with pytest.raises(detached.DetachedComparisonRejected):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )


def test_reentrant_comparator_cannot_rewrite_original_case(
    monkeypatch: pytest.MonkeyPatch,
):
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    original = detached.compare_validation

    def changing(left, right):
        result = original(left, right)
        object.__setattr__(candidate.cases[0], "passed", True)
        return result

    monkeypatch.setattr(detached, "compare_validation", changing)
    with pytest.raises(detached.DetachedComparisonRejected, match="epoch changed"):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )


def test_equal_value_string_carrier_swap_not_accepted(
    monkeypatch: pytest.MonkeyPatch,
):
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    original = detached.compare_validation

    def changing(left, right):
        result = original(left, right)
        old = current.model_identity
        new = ("_" + old)[1:]
        assert old == new and old is not new
        object.__setattr__(current, "model_identity", new)
        return result

    monkeypatch.setattr(detached, "compare_validation", changing)
    with pytest.raises(detached.DetachedComparisonRejected, match="epoch changed"):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )


def test_forged_callback_cannot_suppress_regressions(
    monkeypatch: pytest.MonkeyPatch,
):
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    original = detached.compare_validation

    def forged(left, right):
        result = original(left, right)
        result["regressions"] = []
        return result

    monkeypatch.setattr(detached, "compare_validation", forged)
    with pytest.raises(detached.DetachedComparisonRejected, match="semantics drifted"):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )


def test_forged_callback_cannot_open_historical_v2(
    monkeypatch: pytest.MonkeyPatch,
):
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)

    def forged(left, right):
        result = compare_validation(left, right)
        result["historical_v2_opened"] = True
        return result

    monkeypatch.setattr(detached, "compare_validation", forged)
    with pytest.raises(detached.DetachedComparisonRejected, match="semantics drifted"):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )


def test_retained_report_is_bound_to_current_and_candidate_case_order():
    current, candidate = _reports()
    payload, sha = _retained(current, candidate)
    candidate = replace(candidate, cases=tuple(reversed(candidate.cases)))
    with pytest.raises(detached.DetachedComparisonRejected):
        detached.verify_detached_validation_comparison(
            current, candidate, payload, retained_sha256=sha,
        )
