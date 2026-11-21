"""Paired validation pre-scans cannot hide excess or hostile carriers."""

from dataclasses import replace

import pytest

from ark.learning.validation import ValidationCase, ValidationReport, compare_validation


def report(role="paired_current"):
    return ValidationReport(
        model_role=role,
        model_identity="fixture",
        scorer_sha256="a" * 64,
        runtime_identity="local",
        prompt_contract_sha256="b" * 64,
        cases=tuple(
            ValidationCase(f"id-{i:02d}", "json", True) for i in range(30)
        ),
    )


def test_unhashable_case_identity_rejects_before_duplicate_set():
    r = report()
    entries = list(r.cases)
    entries[0] = replace(entries[0], case_id=["not-hashable"])
    with pytest.raises(ValueError, match="case identity"):
        replace(r, cases=tuple(entries)).validate()


def test_overlength_tuple_is_rejected_before_any_validation_callback(monkeypatch):
    current = report()
    too_long = replace(current, cases=current.cases + current.cases[:1])
    invoked = []

    def blocked(self):
        invoked.append(self)
        raise AssertionError("must reject before report.validate callback")

    monkeypatch.setattr(ValidationReport, "validate", blocked)
    with pytest.raises(ValueError, match="exactly 30"):
        compare_validation(too_long, report("candidate"))
    assert invoked == []


def test_foreign_case_getter_is_not_invoked_during_early_snapshot():
    class ForeignCase:
        @property
        def case_id(self):
            raise AssertionError("must not access foreign case callback")

    current = report()
    altered = replace(current, cases=(ForeignCase(), *current.cases[1:]))
    with pytest.raises(ValueError, match="exact case carriers"):
        compare_validation(altered, report("candidate"))


class StringSubclass(str):
    pass


@pytest.mark.parametrize(
    "field,value",
    (
        ("model_role", StringSubclass("paired_current")),
        ("model_identity", StringSubclass("fixture")),
        ("scorer_sha256", StringSubclass("a" * 64)),
    ),
)
def test_string_subclasses_are_not_validation_identity_evidence(field, value):
    with pytest.raises(ValueError):
        replace(report(), **{field: value}).validate()


def test_exact_bounded_pair_still_never_promotes_or_opens_v2():
    result = compare_validation(report(), report("candidate"))
    assert result["historical_v2_opened"] is False
    assert result["promotion_decision"] == "NOT_AUTHORIZED_FROM_VALIDATION"
    assert result["blocks_v2_opening"] is False
