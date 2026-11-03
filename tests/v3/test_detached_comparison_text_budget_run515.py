"""Bound synthetic paired-validation text before callback or canonicalization."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.detached_comparison_recheck import (
    DetachedComparisonRejected,
    verify_detached_validation_comparison,
)
from ark.learning.execution import canonical_json, sha256_bytes
from ark.learning.validation import (
    ValidationCase,
    ValidationReport,
    compare_validation,
)


def _fixture():
    cases = tuple(
        ValidationCase(f"case-{i:02d}", "format", passed=i != 0)
        for i in range(30)
    )
    current = ValidationReport(
        "paired_current", "fixture-current", "a" * 64,
        "local-mock", "b" * 64, cases,
    )
    candidate = ValidationReport(
        "candidate", "fixture-candidate", "a" * 64,
        "local-mock", "b" * 64, cases,
    )
    output = canonical_json(compare_validation(current, candidate))
    return current, candidate, output, sha256_bytes(output)


@pytest.mark.parametrize("field", (
    "model_identity", "runtime_identity", "case_id", "category",
))
def test_oversized_single_text_field_rejected_before_comparison(field: str):
    current, candidate, output, digest = _fixture()
    oversized = "x" * 4097
    if field in ("case_id", "category"):
        altered = replace(current.cases[0], **{field: oversized})
        current = replace(current, cases=(altered,) + current.cases[1:])
    else:
        current = replace(current, **{field: oversized})
    with pytest.raises(DetachedComparisonRejected, match="text input budget"):
        verify_detached_validation_comparison(
            current, candidate, output, retained_sha256=digest,
        )


def test_total_text_budget_rejects_many_individually_bounded_ids():
    current, candidate, output, digest = _fixture()
    ids = tuple(f"case-{i:02d}-" + "x" * 700 for i in range(30))
    old = tuple(replace(case, case_id=key) for case, key in zip(
        current.cases, ids, strict=True,
    ))
    new = tuple(replace(case, case_id=key) for case, key in zip(
        candidate.cases, ids, strict=True,
    ))
    current = replace(current, cases=old)
    candidate = replace(candidate, cases=new)
    with pytest.raises(DetachedComparisonRejected, match="text input budget"):
        verify_detached_validation_comparison(
            current, candidate, output, retained_sha256=digest,
        )


def test_exact_per_field_limit_is_allowed_with_bounded_total():
    current, candidate, output, digest = _fixture()
    current = replace(current, model_identity="x" * 4096)
    assert verify_detached_validation_comparison(
        current, candidate, output, retained_sha256=digest,
    ) is None


def test_invalid_unicode_surrogate_has_controlled_fail_closed_error():
    current, candidate, output, digest = _fixture()
    bad = replace(current.cases[0], category="\ud800")
    current = replace(current, cases=(bad,) + current.cases[1:])
    with pytest.raises(DetachedComparisonRejected):
        verify_detached_validation_comparison(
            current, candidate, output, retained_sha256=digest,
        )
