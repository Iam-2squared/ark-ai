"""Run1226: V3 review-queue APIs admit exact local carriers only."""

from __future__ import annotations

import pytest

from ark.learning.audit import ReviewPair, build_human_review_queue, deterministic_sample_ids
from ark.learning.dataset import LearningCandidate


def _candidate(candidate_id: str = "candidate-a") -> LearningCandidate:
    return LearningCandidate(
        candidate_id=candidate_id,
        source_type="human_authored",
        source_reference=f"synthetic://{candidate_id}",
        input=f"synthetic task {candidate_id}",
        model_response="",
        evaluation="synthetic review fixture",
        approved_target=f"target {candidate_id}",
        rejection_reason="",
        provenance="synthetic only",
        created_at="2026-09-10T00:00:00+00:00",
        reviewer="fixture-reviewer",
        source_sha256="a" * 64,
        rights="owned",
        approved=True,
        independent=True,
        split="train",
        group=candidate_id,
    )


def test_review_pair_rejects_text_subclasses_before_string_callbacks() -> None:
    class CallbackText(str):
        def strip(self):
            raise AssertionError("subclass strip callback must not run")

    pair = ReviewPair(
        CallbackText("candidate-a"),
        "protected-a",
        0.5,
        "detector-a",
        "synthetic reason",
    )
    with pytest.raises(ValueError, match="complete review-pair metadata"):
        ReviewPair.validate(pair)


def test_review_pair_rejects_numeric_subclasses_before_float_callbacks() -> None:
    class CallbackFloat(float):
        def __float__(self):
            raise AssertionError("subclass float callback must not run")

    pair = ReviewPair(
        "candidate-a",
        "protected-a",
        CallbackFloat(0.5),
        "detector-a",
        "synthetic reason",
    )
    with pytest.raises(ValueError, match="exact number"):
        ReviewPair.validate(pair)


def test_review_pair_rejects_bool_score() -> None:
    pair = ReviewPair(
        "candidate-a", "protected-a", True, "detector-a", "synthetic reason"
    )
    with pytest.raises(ValueError, match="exact number"):
        ReviewPair.validate(pair)


def test_review_pair_subclass_is_rejected_before_attribute_callbacks() -> None:
    class CallbackPair(ReviewPair):
        def __getattribute__(self, name):
            raise AssertionError("subclass attribute callback must not run")

    pair = CallbackPair(
        "candidate-a", "protected-a", 0.5, "detector-a", "synthetic reason"
    )
    with pytest.raises(ValueError, match="exact ReviewPair"):
        build_human_review_queue([_candidate()], [pair])


def test_candidate_subclass_is_rejected_before_attribute_callbacks() -> None:
    class CallbackCandidate(LearningCandidate):
        def __getattribute__(self, name):
            raise AssertionError("subclass attribute callback must not run")

    hostile = CallbackCandidate(**vars(_candidate()))
    with pytest.raises(ValueError, match="exact LearningCandidate"):
        deterministic_sample_ids([hostile])


def test_list_subclasses_are_rejected_before_iteration() -> None:
    class CallbackList(list):
        def __iter__(self):
            raise AssertionError("list subclass iterator must not run")

    with pytest.raises(ValueError, match="items must be an exact list"):
        deterministic_sample_ids(CallbackList([_candidate()]))

    with pytest.raises(ValueError, match="flagged_pairs must be an exact list"):
        build_human_review_queue([_candidate()], CallbackList())


@pytest.mark.parametrize(
    ("fraction", "minimum"),
    ((True, 1), (0.5, True), (float("inf"), 1), (0.0, 1), (0.5, 0)),
)
def test_sample_policy_rejects_bool_and_nonfinite_or_out_of_range_values(
    fraction, minimum,
) -> None:
    with pytest.raises(ValueError, match="sample policy"):
        deterministic_sample_ids([_candidate()], fraction=fraction, minimum=minimum)


def test_sample_fraction_subclass_is_rejected_before_float_callback() -> None:
    class CallbackFloat(float):
        def __float__(self):
            raise AssertionError("fraction callback must not run")

    with pytest.raises(ValueError, match="sample policy"):
        deterministic_sample_ids([_candidate()], fraction=CallbackFloat(0.5))


def test_valid_exact_review_queue_preserves_ordered_semantics() -> None:
    first = _candidate("candidate-a")
    second = _candidate("candidate-b")
    pair = ReviewPair(
        "candidate-a", "protected-a", 0.75, "detector-a", "synthetic overlap"
    )

    queue = build_human_review_queue(
        [first, second], [pair], fraction=1.0, minimum=1
    )

    assert queue["accepted_count"] == 2
    assert queue["flagged_candidate_ids"] == ["candidate-a"]
    assert queue["sampled_non_flagged_candidate_ids"] == ["candidate-b"]
    assert queue["flagged_pairs"] == [
        {
            "candidate_id": "candidate-a",
            "protected_id": "protected-a",
            "score": 0.75,
            "detector": "detector-a",
            "reason": "synthetic overlap",
        }
    ]
    assert queue["policy"]["non_flagged_fraction"] == 1.0
