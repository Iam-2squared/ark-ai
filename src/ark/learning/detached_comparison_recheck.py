"""Detached byte-for-byte audit of synthetic V3 paired validation output.

Neither a matching report nor its independently retained hash authorizes a
Candidate, protected V2 opening, training, promotion, external compute or spend.
No model or filesystem access occurs in this verifier.
"""

from __future__ import annotations

import hashlib
import re

from .execution import canonical_json
from .validation import ValidationCase, ValidationReport, compare_validation

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = (
    "model_role", "model_identity", "scorer_sha256",
    "runtime_identity", "prompt_contract_sha256", "cases",
)
_CASE_FIELDS = (
    "case_id", "category", "passed", "runtime_failure", "memory_failure",
)
_MAX_BYTES = 128 * 1024
_MAX_FIELD_CHARS = 4096
_MAX_INPUT_CHARS = 32768


class DetachedComparisonRejected(ValueError):
    """Retained paired-validation output cannot be independently reproduced."""


def verify_detached_validation_comparison(
    current: ValidationReport,
    candidate: ValidationReport,
    retained_report_bytes: bytes,
    *,
    retained_sha256: str,
) -> None:
    """Recompute a validation-only comparison; never return a permission token.

    The caller must separately retain both the report bytes and their hash.
    Recomputing checks consistency, not authenticity of model runs, human
    review, source identity or consent.
    """
    if (
        type(current) is not ValidationReport
        or type(candidate) is not ValidationReport
        or type(retained_report_bytes) is not bytes
        or not 0 < len(retained_report_bytes) <= _MAX_BYTES
        or type(retained_sha256) is not str
        or _SHA.fullmatch(retained_sha256) is None
    ):
        raise DetachedComparisonRejected("exact bounded validation inputs required")

    originals = []
    cumulative_text_chars = 0
    for report in (current, candidate):
        fields = tuple(getattr(report, name) for name in _FIELDS)
        cases = report.cases
        if (
            any(type(field) is not str for field in fields[:5])
            or type(cases) is not tuple
            or len(cases) != 30
            or any(type(case) is not ValidationCase for case in cases)
        ):
            raise DetachedComparisonRejected("validation report carrier invalid")
        case_epochs = tuple(
            (case, tuple(getattr(case, name) for name in _CASE_FIELDS))
            for case in cases
        )
        if any(
            type(values[0]) is not str
            or type(values[1]) is not str
            or any(type(flag) is not bool for flag in values[2:])
            for _, values in case_epochs
        ):
            raise DetachedComparisonRejected("validation case carrier invalid")
        # The retained byte bound alone is too late: caller-held model/case
        # strings could be huge before the comparison is serialized. Charge
        # them before invoking any report validation or comparison callback.
        texts = fields[:5] + tuple(
            value for _, values in case_epochs for value in values[:2]
        )
        cumulative_text_chars += sum(len(value) for value in texts)
        if (
            any(len(value) > _MAX_FIELD_CHARS for value in texts)
            or cumulative_text_chars > _MAX_INPUT_CHARS
        ):
            raise DetachedComparisonRejected("validation text input budget exceeded")
        originals.append((report, fields, case_epochs))

    def stable() -> None:
        try:
            for report, fields, case_epochs in originals:
                if (
                    type(report) is not ValidationReport
                    or any(
                        getattr(report, name) is not original
                        for name, original in zip(_FIELDS, fields, strict=True)
                    )
                    or len(report.cases) != len(case_epochs)
                    or any(
                        actual is not case
                        or any(
                            getattr(actual, name) is not original
                            for name, original in zip(
                                _CASE_FIELDS, values, strict=True,
                            )
                        )
                        for actual, (case, values) in zip(
                            report.cases, case_epochs, strict=True,
                        )
                    )
                ):
                    raise DetachedComparisonRejected("validation input epoch changed")
        except DetachedComparisonRejected:
            raise
        except (AttributeError, TypeError, ValueError) as exc:
            raise DetachedComparisonRejected("validation input epoch invalid") from exc

    stable()
    try:
        current.validate()
        candidate.validate()
        stable()
        # Re-derive the outcome independently of the potentially substituted
        # compare_validation callback. This is strictly fixture comparison.
        previous = {case.case_id: case for case in current.cases}
        upcoming = {case.case_id: case for case in candidate.cases}
        if (
            current.model_role != "paired_current"
            or candidate.model_role != "candidate"
            or len(previous) != 30
            or len(upcoming) != 30
            or previous.keys() != upcoming.keys()
            or tuple(previous) != tuple(upcoming)
            or any(previous[k].category != upcoming[k].category for k in previous)
            or any(
                getattr(current, name) != getattr(candidate, name)
                for name in (
                    "scorer_sha256", "runtime_identity",
                    "prompt_contract_sha256",
                )
            )
        ):
            raise DetachedComparisonRejected("paired validation identity mismatch")
        regressions = [
            k for k in previous if previous[k].passed and not upcoming[k].passed
        ]
        improvements = [
            k for k in previous if not previous[k].passed and upcoming[k].passed
        ]
        runtime_failures = sum(c.runtime_failure for c in upcoming.values())
        memory_failures = sum(c.memory_failure for c in upcoming.values())
        categories = {}
        for category in sorted({c.category for c in previous.values()}):
            old = [c for c in previous.values() if c.category == category]
            new = [c for c in upcoming.values() if c.category == category]
            categories[category] = {
                "count": len(old),
                "current_passed": sum(c.passed for c in old),
                "candidate_passed": sum(c.passed for c in new),
            }
        expected = {
            "comparison_kind": "v3_validation_only",
            "historical_v2_opened": False,
            "regressions": regressions,
            "improvements": improvements,
            "candidate_runtime_failures": runtime_failures,
            "candidate_memory_failures": memory_failures,
            "categories": categories,
            "blocks_v2_opening": bool(runtime_failures or memory_failures),
            "promotion_decision": "NOT_AUTHORIZED_FROM_VALIDATION",
        }
        stable()
        actual = compare_validation(current, candidate)
        stable()
        if (
            type(actual) is not dict
            or actual != expected
            or type(actual.get("historical_v2_opened")) is not bool
            or actual["historical_v2_opened"] is not False
            or type(actual.get("blocks_v2_opening")) is not bool
            or actual["promotion_decision"] != "NOT_AUTHORIZED_FROM_VALIDATION"
        ):
            raise DetachedComparisonRejected("comparison semantics drifted")
        encoded = canonical_json(expected)
        stable()
        if (
            encoded != retained_report_bytes
            or hashlib.sha256(encoded).hexdigest() != retained_sha256
        ):
            raise DetachedComparisonRejected("retained validation bytes mismatch")
        stable()
        return None
    except DetachedComparisonRejected:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError) as exc:
        raise DetachedComparisonRejected("paired validation could not be reproduced") from exc
