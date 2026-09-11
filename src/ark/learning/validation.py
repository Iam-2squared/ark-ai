"""Validation-only paired comparison for V3 before historical V2 opening."""

from __future__ import annotations

import re
from dataclasses import dataclass


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
        if self.model_role not in {"paired_current", "candidate"}:
            raise ValueError("invalid validation model role")
        for value in (self.model_identity, self.runtime_identity):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("validation identity missing")
        for value in (self.scorer_sha256, self.prompt_contract_sha256):
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise ValueError("validation SHA-256 identity required")
        if len(self.cases) != 30:
            raise ValueError("experiment-001 validation requires exactly 30 cases")
        ids = [case.case_id for case in self.cases]
        if len(set(ids)) != len(ids):
            raise ValueError("validation cases must be unique")
        for case in self.cases:
            if not isinstance(case.case_id, str) or not case.case_id.strip():
                raise ValueError("validation case identity required")
            if not isinstance(case.category, str) or not case.category.strip():
                raise ValueError("validation category required")
            if any(
                type(value) is not bool
                for value in (case.passed, case.runtime_failure, case.memory_failure)
            ):
                raise ValueError("validation outcomes must be exact booleans")
            if case.passed and (case.runtime_failure or case.memory_failure):
                raise ValueError("a failed runtime/memory case may not be marked passed")


def compare_validation(current: ValidationReport, candidate: ValidationReport) -> dict:
    """Compare matched non-V2 validation evidence without promotion semantics."""
    current.validate()
    candidate.validate()
    if current.model_role != "paired_current" or candidate.model_role != "candidate":
        raise ValueError("expected paired_current vs candidate")
    for field in ("scorer_sha256", "runtime_identity", "prompt_contract_sha256"):
        if getattr(current, field) != getattr(candidate, field):
            raise ValueError(f"validation mismatch: {field}")

    old = {case.case_id: case for case in current.cases}
    new = {case.case_id: case for case in candidate.cases}
    if old.keys() != new.keys():
        raise ValueError("validation case identities differ")
    for case_id in old:
        if old[case_id].category != new[case_id].category:
            raise ValueError("validation category mismatch")

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

    return {
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
