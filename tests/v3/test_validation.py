import pytest

from ark.learning.validation import ValidationCase, ValidationReport, compare_validation


def report(role: str, *, count: int = 30, passed: bool = True) -> ValidationReport:
    return ValidationReport(
        model_role=role,
        model_identity=f"{role}-identity",
        scorer_sha256="a" * 64,
        runtime_identity="runtime-v1",
        prompt_contract_sha256="b" * 64,
        cases=tuple(
            ValidationCase(
                case_id=f"case-{index:02d}",
                category="format",
                passed=passed,
            )
            for index in range(count)
        ),
    )


def test_validation_requires_exactly_frozen_30_cases():
    for count in (29, 31):
        with pytest.raises(ValueError, match="exactly 30"):
            report("paired_current", count=count).validate()


def test_validation_requires_exact_boolean_outcomes():
    valid = report("candidate")
    cases = list(valid.cases)
    cases[0] = ValidationCase(
        case_id=cases[0].case_id,
        category=cases[0].category,
        passed=1,  # type: ignore[arg-type]
    )
    invalid = ValidationReport(
        model_role=valid.model_role,
        model_identity=valid.model_identity,
        scorer_sha256=valid.scorer_sha256,
        runtime_identity=valid.runtime_identity,
        prompt_contract_sha256=valid.prompt_contract_sha256,
        cases=tuple(cases),
    )
    with pytest.raises(ValueError, match="exact booleans"):
        invalid.validate()


def test_validation_rejects_passed_case_with_runtime_or_memory_failure():
    valid = report("candidate")
    for failure_field in ("runtime_failure", "memory_failure"):
        cases = list(valid.cases)
        kwargs = {failure_field: True}
        cases[0] = ValidationCase(
            case_id=cases[0].case_id,
            category=cases[0].category,
            passed=True,
            **kwargs,
        )
        invalid = ValidationReport(
            model_role=valid.model_role,
            model_identity=valid.model_identity,
            scorer_sha256=valid.scorer_sha256,
            runtime_identity=valid.runtime_identity,
            prompt_contract_sha256=valid.prompt_contract_sha256,
            cases=tuple(cases),
        )
        with pytest.raises(ValueError, match="may not be marked passed"):
            invalid.validate()


def test_paired_validation_stays_validation_only():
    result = compare_validation(report("paired_current"), report("candidate"))
    assert result["comparison_kind"] == "v3_validation_only"
    assert result["historical_v2_opened"] is False
    assert result["promotion_decision"] == "NOT_AUTHORIZED_FROM_VALIDATION"
    assert result["blocks_v2_opening"] is False
