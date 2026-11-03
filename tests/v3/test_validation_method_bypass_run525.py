"""Public method replacement cannot bypass V3's exact validation contract.

These are synthetic in-memory comparisons only: no model loading, Candidate
generation, protected V2 evaluation, promotion or external compute.
"""

from dataclasses import replace

import pytest

from ark.learning.validation import (
    ValidationCase,
    ValidationReport,
    compare_validation,
)


def _paired():
    cases = tuple(
        ValidationCase(f"case-{index:02d}", "math", True)
        for index in range(30)
    )
    common = {
        "model_identity": "synthetic-local-current",
        "scorer_sha256": "a" * 64,
        "runtime_identity": "offline-fixture",
        "prompt_contract_sha256": "b" * 64,
        "cases": cases,
    }
    return (
        ValidationReport("paired_current", **common),
        ValidationReport("candidate", **{
            **common, "model_identity": "synthetic-local-candidate",
        }),
    )


@pytest.mark.parametrize("invalid", (
    "non_boolean_pass",
    "non_boolean_failure",
    "duplicate_ids",
    "blank_category",
    "invalid_scorer_hash",
    "blank_model_identity",
    "excessive_identity",
))
def test_patched_public_validator_cannot_approve_invalid_comparison(
    monkeypatch, invalid,
):
    current, candidate = _paired()
    cases = list(current.cases)
    if invalid == "non_boolean_pass":
        cases[0] = replace(cases[0], passed=1)
    elif invalid == "non_boolean_failure":
        cases[0] = replace(cases[0], runtime_failure=0)
    elif invalid == "duplicate_ids":
        cases[1] = replace(cases[1], case_id=cases[0].case_id)
    elif invalid == "blank_category":
        cases[0] = replace(cases[0], category=" ")
    elif invalid == "invalid_scorer_hash":
        current = replace(current, scorer_sha256="not-a-sha")
        candidate = replace(candidate, scorer_sha256="not-a-sha")
    elif invalid == "blank_model_identity":
        current = replace(current, model_identity=" ")
    elif invalid == "excessive_identity":
        current = replace(current, model_identity="X" * 4097)
    if invalid in {
        "non_boolean_pass", "non_boolean_failure",
        "duplicate_ids", "blank_category",
    }:
        current = replace(current, cases=tuple(cases))
        candidate = replace(candidate, cases=tuple(cases))

    observed = []

    def bypass(self):
        observed.append(self.model_role)
        return None

    monkeypatch.setattr(ValidationReport, "validate", bypass)
    with pytest.raises(ValueError):
        compare_validation(current, candidate)
    assert observed == ["paired_current"]


def test_unpatched_pair_remains_validation_only():
    current, candidate = _paired()
    comparison = compare_validation(current, candidate)
    assert comparison["comparison_kind"] == "v3_validation_only"
    assert comparison["historical_v2_opened"] is False
    assert comparison["promotion_decision"] == "NOT_AUTHORIZED_FROM_VALIDATION"
    assert comparison["regressions"] == []
    assert comparison["improvements"] == []
