"""Validation-only paired comparison for V3 before historical V2 opening."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_FIELD_CHARS = 4096
_MAX_TOTAL_TEXT = 32768
_REPORT_FIELDS = (
    "model_role", "model_identity", "scorer_sha256",
    "runtime_identity", "prompt_contract_sha256", "cases",
)
_CASE_FIELDS = (
    "case_id", "category", "passed", "runtime_failure", "memory_failure",
)


@dataclass(frozen=True)
class ValidationCase:
    case_id: str
    category: str
    passed: bool
    runtime_failure: bool = False
    memory_failure: bool = False


@dataclass(frozen=True)
class ValidationReport:
    model_role: str
    model_identity: str
    scorer_sha256: str
    runtime_identity: str
    prompt_contract_sha256: str
    cases: tuple[ValidationCase, ...]

    def validate(self) -> None:
        if type(self) is not ValidationReport:
            raise ValueError("exact validation report required")
        if type(self.model_role) is not str or self.model_role not in {
            "paired_current", "candidate",
        }:
            raise ValueError("invalid validation model role")
        for value in (self.model_identity, self.runtime_identity):
            if type(value) is not str or not value.strip():
                raise ValueError("validation identity missing")
        for value in (self.scorer_sha256, self.prompt_contract_sha256):
            if type(value) is not str or _SHA.fullmatch(value) is None:
                raise ValueError("validation SHA-256 identity required")
        if type(self.cases) is not tuple or len(self.cases) != 30:
            raise ValueError("experiment-001 validation requires exactly 30 cases")
        if any(type(case) is not ValidationCase for case in self.cases):
            raise ValueError("validation case carrier must be exact")
        total_text = 0
        for value in (
            self.model_role, self.model_identity, self.scorer_sha256,
            self.runtime_identity, self.prompt_contract_sha256,
        ):
            if len(value) > _MAX_FIELD_CHARS:
                raise ValueError("validation identity text budget exceeded")
            total_text += len(value)
        for case in self.cases:
            if type(case.case_id) is not str or not case.case_id.strip():
                raise ValueError("validation case identity required")
            if type(case.category) is not str or not case.category.strip():
                raise ValueError("validation category required")
            if any(
                type(value) is not bool
                for value in (case.passed, case.runtime_failure, case.memory_failure)
            ):
                raise ValueError("validation outcomes must be exact booleans")
            for value in (case.case_id, case.category):
                if len(value) > _MAX_FIELD_CHARS:
                    raise ValueError("validation case text budget exceeded")
                total_text += len(value)
        if len({case.case_id for case in self.cases}) != len(self.cases):
            raise ValueError("validation cases must be unique")
        if total_text > _MAX_TOTAL_TEXT:
            raise ValueError("validation total text budget exceeded")


def _epoch(report: ValidationReport) -> tuple[object, ...]:
    """Pin exact report/case carriers before any potentially patched validator."""
    fields = tuple(getattr(report, name) for name in _REPORT_FIELDS)
    if (
        type(fields[-1]) is not tuple
        or len(fields[-1]) != 30
        or any(type(case) is not ValidationCase for case in fields[-1])
    ):
        raise ValueError("validation requires exactly 30 exact case carriers")
    cases = tuple(
        (case, tuple(getattr(case, name) for name in _CASE_FIELDS))
        for case in fields[-1]
    )
    return (report, fields, cases)


def _same_epoch(epoch: tuple[object, ...]) -> bool:
    report, fields, cases = epoch
    try:
        return (
            type(report) is ValidationReport
            and all(
                getattr(report, name) is original
                for name, original in zip(_REPORT_FIELDS, fields, strict=True)
            )
            and len(report.cases) == len(cases)
            and all(
                now is original_case
                and type(now) is ValidationCase
                and all(
                    getattr(now, name) is old
                    for name, old in zip(_CASE_FIELDS, values, strict=True)
                )
                for now, (original_case, values) in zip(
                    report.cases, cases, strict=True,
                )
            )
        )
    except (AttributeError, TypeError, ValueError):
        return False


def compare_validation(current: ValidationReport, candidate: ValidationReport) -> dict:
    """Compare exact, bounded non-V2 validation without promotion semantics."""
    if type(current) is not ValidationReport or type(candidate) is not ValidationReport:
        raise ValueError("exact paired validation carriers required")
    current_epoch = _epoch(current)
    candidate_epoch = _epoch(candidate)

    def stable() -> None:
        if not _same_epoch(current_epoch) or not _same_epoch(candidate_epoch):
            raise ValueError("paired validation carriers changed during comparison")

    stable()
    current.validate()
    stable()
    candidate.validate()
    stable()
    # Direct comparisons must enforce the same combined input budget as the
    # detached V3 rechecker, not permit two individually maximal reports.
    total_text = sum(
        len(value)
        for _, fields, cases in (current_epoch, candidate_epoch)
        for value in (
            *fields[:5],
            *(text for _, values in cases for text in values[:2]),
        )
    )
    stable()
    if total_text > _MAX_TOTAL_TEXT:
        raise ValueError("paired validation total text budget exceeded")
    if current.model_role != "paired_current" or candidate.model_role != "candidate":
        raise ValueError("expected paired_current vs candidate")
    for field in ("scorer_sha256", "runtime_identity", "prompt_contract_sha256"):
        if getattr(current, field) != getattr(candidate, field):
            raise ValueError(f"validation mismatch: {field}")
    stable()

    old = {case.case_id: case for case in current.cases}
    new = {case.case_id: case for case in candidate.cases}
    if old.keys() != new.keys():
        raise ValueError("validation case identities differ")
    for case_id in old:
        if old[case_id].category != new[case_id].category:
            raise ValueError("validation category mismatch")
    stable()

    regressions = [case_id for case_id in old if old[case_id].passed and not new[case_id].passed]
    improvements = [case_id for case_id in old if not old[case_id].passed and new[case_id].passed]
    candidate_runtime_failures = sum(case.runtime_failure for case in new.values())
    candidate_memory_failures = sum(case.memory_failure for case in new.values())
    categories = {}
    for category in sorted({case.category for case in old.values()}):
        current_subset = [case for case in old.values() if case.category == category]
        candidate_subset = [case for case in new.values() if case.category == category]
        categories[category] = {
            "count": len(current_subset),
            "current_passed": sum(case.passed for case in current_subset),
            "candidate_passed": sum(case.passed for case in candidate_subset),
        }
    stable()
    report = {
        "comparison_kind": "v3_validation_only",
        "historical_v2_opened": False,
        "regressions": regressions,
        "improvements": improvements,
        "candidate_runtime_failures": candidate_runtime_failures,
        "candidate_memory_failures": candidate_memory_failures,
        "categories": categories,
        "blocks_v2_opening": bool(candidate_runtime_failures or candidate_memory_failures),
        "promotion_decision": "NOT_AUTHORIZED_FROM_VALIDATION",
    }
    stable()
    return report
