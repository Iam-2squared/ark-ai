"""Direct paired V3 validation retains detached recheck's exact case ordering.

Only 30 synthetic validation cases are involved; no V2 scorer, GPU, Candidate
weights, training, or promotion is accessed by these tests.
"""

from dataclasses import replace

import pytest

from ark.learning.validation import ValidationCase, ValidationReport, compare_validation


def make_report(role="paired_current"):
    return ValidationReport(
        model_role=role,
        model_identity="synthetic-v3-offline",
        scorer_sha256="a" * 64,
        runtime_identity="local-fixture",
        prompt_contract_sha256="b" * 64,
        cases=tuple(
            ValidationCase(f"case-{i:02d}", "json", i % 2 == 0)
            for i in range(30)
        ),
    )


@pytest.mark.parametrize(
    ("first", "second"),
    ((0, 1), (0, 29), (14, 15), (2, 27), (13, 20)),
)
def test_equal_id_sets_with_different_order_are_rejected(first, second):
    original = make_report()
    candidate = make_report("candidate")
    altered = list(candidate.cases)
    altered[first], altered[second] = altered[second], altered[first]
    assert set(c.case_id for c in altered) == set(c.case_id for c in original.cases)
    with pytest.raises(ValueError, match="case order"):
        compare_validation(original, replace(candidate, cases=tuple(altered)))


def test_distinct_but_equal_carriers_in_same_order_remain_accepted():
    current = make_report()
    candidate = make_report("candidate")
    candidate = replace(
        candidate, cases=tuple(replace(item) for item in candidate.cases),
    )
    result = compare_validation(current, candidate)
    assert result["comparison_kind"] == "v3_validation_only"
    assert result["historical_v2_opened"] is False
    assert result["promotion_decision"] == "NOT_AUTHORIZED_FROM_VALIDATION"


def test_shared_unsorted_case_order_remains_eligible_for_comparison():
    current = make_report()
    candidate = make_report("candidate")
    reverse = tuple(reversed(range(30)))
    current = replace(current, cases=tuple(current.cases[i] for i in reverse))
    candidate = replace(candidate, cases=tuple(candidate.cases[i] for i in reverse))
    output = compare_validation(current, candidate)
    assert output["regressions"] == []
    assert output["improvements"] == []
    assert output["blocks_v2_opening"] is False


def test_missing_case_id_preserves_existing_mismatch_rejection():
    current = make_report()
    candidate = make_report("candidate")
    changed = list(candidate.cases)
    changed[-1] = replace(changed[-1], case_id="different-case")
    with pytest.raises(ValueError, match="case identities"):
        compare_validation(current, replace(candidate, cases=tuple(changed)))
