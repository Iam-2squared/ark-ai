"""The synthetic V3 comparator cannot drift during a JSON serializer callback.

No Candidate, model, GPU, V2 evaluation, or promotion is authorized.
"""

from __future__ import annotations

import pytest
from test_detached_comparison_recheck_run515 import _reports, _retained

import ark.learning.detached_comparison_recheck as detached


@pytest.mark.parametrize("mutation", (
    "historical_v2", "promotion", "runtime_count", "category_passed",
    "regressions",
))
def test_serializer_mutation_of_comparison_callback_result_denied(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    current, candidate = _reports()
    retained, sha = _retained(current, candidate)
    original_compare = detached.compare_validation
    original_serializer = detached.canonical_json
    actual: list[dict] = []
    changed = False

    def compare(left, right):
        result = original_compare(left, right)
        actual.append(result)
        return result

    def serialize(value):
        nonlocal changed
        if actual and not changed:
            changed = True
            tree = actual[0]
            if mutation == "historical_v2":
                tree["historical_v2_opened"] = True
            elif mutation == "promotion":
                tree["promotion_decision"] = "APPROVED"
            elif mutation == "runtime_count":
                tree["candidate_runtime_failures"] += 1
            elif mutation == "category_passed":
                tree["categories"]["math"]["current_passed"] += 1
            else:
                tree["regressions"] = []
        return original_serializer(value)

    with monkeypatch.context() as patch:
        patch.setattr(detached, "compare_validation", compare)
        patch.setattr(detached, "canonical_json", serialize)
        with pytest.raises(
            detached.DetachedComparisonRejected,
            match="comparison callback changed",
        ):
            detached.verify_detached_validation_comparison(
                current, candidate, retained, retained_sha256=sha,
            )
    assert changed
    assert len(actual) == 1


def test_comparison_mutation_after_actual_serialization_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current, candidate = _reports()
    retained, sha = _retained(current, candidate)
    original_compare = detached.compare_validation
    original_serializer = detached.canonical_json
    actual: list[dict] = []

    def compare(left, right):
        outcome = original_compare(left, right)
        actual.append(outcome)
        return outcome

    def serialize(value):
        encoded = original_serializer(value)
        if actual and value is actual[0]:
            actual[0]["historical_v2_opened"] = True
        return encoded

    with monkeypatch.context() as patch:
        patch.setattr(detached, "compare_validation", compare)
        patch.setattr(detached, "canonical_json", serialize)
        with pytest.raises(
            detached.DetachedComparisonRejected,
            match="comparison callback changed",
        ):
            detached.verify_detached_validation_comparison(
                current, candidate, retained, retained_sha256=sha,
            )


def test_stable_comparison_requires_same_callback_and_expected_bytes() -> None:
    current, candidate = _reports()
    retained, sha = _retained(current, candidate)
    assert detached.verify_detached_validation_comparison(
        current, candidate, retained, retained_sha256=sha,
    ) is None
