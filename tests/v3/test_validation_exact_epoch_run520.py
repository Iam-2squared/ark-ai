"""Direct paired V3 validation rejects aliases and reflected evidence changes."""

from dataclasses import replace

import pytest

from ark.learning.validation import ValidationCase, ValidationReport, compare_validation


def report(role="paired_current"):
    return ValidationReport(
        model_role=role,
        model_identity="local-synthetic",
        scorer_sha256="a" * 64,
        runtime_identity="mock-runtime",
        prompt_contract_sha256="b" * 64,
        cases=tuple(
            ValidationCase(f"case-{index:02d}", "format", index % 2 == 0)
            for index in range(30)
        ),
    )


def with_case(value, position=0):
    baseline = report()
    values = list(baseline.cases)
    values[position] = value
    return replace(baseline, cases=tuple(values))


def test_valid_direct_paired_comparison_never_authorizes_v2():
    outcome = compare_validation(report(), report("candidate"))
    assert outcome["comparison_kind"] == "v3_validation_only"
    assert outcome["historical_v2_opened"] is False
    assert outcome["promotion_decision"] == "NOT_AUTHORIZED_FROM_VALIDATION"
    assert outcome["blocks_v2_opening"] is False


@pytest.mark.parametrize(
    "field,value",
    (
        ("case_id", " " * 5),
        ("category", " "),
        ("case_id", "a" * 4097),
        ("category", "b" * 4097),
        ("passed", 1),
        ("runtime_failure", 1),
        ("memory_failure", 0),
    ),
)
def test_noncanonical_validation_case_rejected(field, value):
    baseline = report()
    altered = replace(baseline.cases[0], **{field: value})
    with pytest.raises(ValueError):
        with_case(altered).validate()


@pytest.mark.parametrize(
    "field,value",
    (
        ("model_identity", "a" * 4097),
        ("runtime_identity", "r" * 4097),
        ("scorer_sha256", "a" * 63),
        ("model_role", "candidate"),
        ("cases", []),
    ),
)
def test_malformed_report_rejected(field, value):
    altered = replace(report(), **{field: value})
    if field == "model_role":
        # A wrong role is rejected by the paired comparator, not by validate.
        with pytest.raises(ValueError, match="paired_current"):
            compare_validation(altered, report("candidate"))
    else:
        with pytest.raises(ValueError):
            altered.validate()


def test_exact_case_and_report_carriers_required():
    class OtherCase(ValidationCase):
        pass

    class OtherReport(ValidationReport):
        pass

    valid = report()
    with pytest.raises(ValueError, match="case carrier"):
        with_case(OtherCase("case-00", "format", True)).validate()
    forged = OtherReport(**vars(valid))
    with pytest.raises(ValueError, match="exact validation report"):
        forged.validate()
    with pytest.raises(ValueError, match="exact paired validation"):
        compare_validation(forged, report("candidate"))


def test_overall_bounded_input_budget_rejects_60_large_labels():
    base = report()
    cases = tuple(
        replace(case, case_id=f"case-{i:02d}" + ("x" * 500),
                category="c" * 500)
        for i, case in enumerate(base.cases)
    )
    # Each report is within its own 32,768-character budget, but the
    # paired input must be bounded as a whole before comparison.
    one = replace(base, cases=cases)
    one.validate()
    other = replace(report("candidate"), cases=cases)
    other.validate()
    with pytest.raises(ValueError, match="paired validation total text"):
        compare_validation(one, other)


def test_late_current_report_mutation_during_validate_is_rejected(monkeypatch):
    current = report()
    candidate = report("candidate")
    original = ValidationReport.validate

    def altered(self):
        original(self)
        if self is current:
            object.__setattr__(self, "runtime_identity", "changed-runtime")

    monkeypatch.setattr(ValidationReport, "validate", altered)
    with pytest.raises(ValueError, match="changed"):
        compare_validation(current, candidate)


def test_late_candidate_case_mutation_during_validate_is_rejected(monkeypatch):
    current = report()
    candidate = report("candidate")
    original = ValidationReport.validate

    def altered(self):
        original(self)
        if self is candidate:
            object.__setattr__(self.cases[0], "passed", False)

    monkeypatch.setattr(ValidationReport, "validate", altered)
    with pytest.raises(ValueError, match="changed"):
        compare_validation(current, candidate)


def test_replacement_with_equal_valued_case_tuple_is_rejected(monkeypatch):
    current = report()
    candidate = report("candidate")
    original = ValidationReport.validate

    def altered(self):
        original(self)
        if self is current:
            object.__setattr__(self, "cases", tuple(replace(c) for c in self.cases))

    monkeypatch.setattr(ValidationReport, "validate", altered)
    with pytest.raises(ValueError, match="changed"):
        compare_validation(current, candidate)
