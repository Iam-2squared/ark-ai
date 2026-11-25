"""Synthetic V3 report callback must preserve JSON value types exactly.

An equal-value dict with float counts or bool-as-int results is not a valid
comparison. No model, V2 evaluation, Candidate or external compute is used.
"""

from __future__ import annotations

from copy import deepcopy

import pytest
from test_detached_comparison_recheck_run515 import _reports, _retained

import ark.learning.detached_comparison_recheck as detached
from ark.learning.validation import compare_validation


@pytest.mark.parametrize("mutation", (
    "boolean_runtime_count",
    "float_runtime_count",
    "float_memory_count",
    "float_category_count",
    "float_category_passed",
    "subclass_categories",
    "tuple_regressions",
))
def test_equal_python_values_with_wrong_json_types_fail_closed(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    current, candidate = _reports()
    retained, sha = _retained(current, candidate)

    def replaced(left: object, right: object) -> dict:
        report = deepcopy(compare_validation(left, right))
        if mutation == "boolean_runtime_count":
            assert report["candidate_runtime_failures"] == 1
            report["candidate_runtime_failures"] = True
        elif mutation == "float_runtime_count":
            report["candidate_runtime_failures"] = float(
                report["candidate_runtime_failures"]
            )
        elif mutation == "float_memory_count":
            report["candidate_memory_failures"] = float(
                report["candidate_memory_failures"]
            )
        elif mutation == "float_category_count":
            report["categories"]["math"]["count"] = 15.0
        elif mutation == "float_category_passed":
            report["categories"]["math"]["current_passed"] = float(
                report["categories"]["math"]["current_passed"]
            )
        elif mutation == "subclass_categories":
            class EqualDict(dict):
                pass

            report["categories"] = EqualDict(report["categories"])
        else:
            report["regressions"] = tuple(report["regressions"])
        return report

    monkeypatch.setattr(detached, "compare_validation", replaced)
    with pytest.raises(detached.DetachedComparisonRejected, match="semantics drifted"):
        detached.verify_detached_validation_comparison(
            current, candidate, retained, retained_sha256=sha,
        )


def test_exact_builtin_comparison_still_validates_without_authorizing() -> None:
    current, candidate = _reports()
    retained, sha = _retained(current, candidate)
    assert detached.verify_detached_validation_comparison(
        current, candidate, retained, retained_sha256=sha,
    ) is None
