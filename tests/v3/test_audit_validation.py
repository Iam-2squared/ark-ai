import pytest

from ark.learning.audit import ReviewPair, build_human_review_queue, deterministic_sample_ids
from ark.learning.dataset import LearningCandidate
from ark.learning.validation import ValidationCase, ValidationReport, compare_validation


def candidate(identifier: str) -> LearningCandidate:
    return LearningCandidate(
        candidate_id=identifier,
        source_type="human_authored",
        source_reference=f"owned:{identifier}",
        input=f"Return token {identifier}",
        model_response=identifier,
        evaluation="fixture",
        approved_target=identifier,
        rejection_reason="",
        provenance="owned fixture",
        created_at="2026-09-10T00:00:00Z",
        reviewer="fixture-reviewer",
        source_sha256="a" * 64,
        rights="owned",
        approved=True,
        independent=True,
        split="train" if identifier != "v" else "validation",
        group=f"g-{identifier}",
    )


def test_review_queue_is_deterministic_and_reviews_all_flags():
    items = [candidate(f"id-{i:02d}") for i in range(30)]
    flags = [ReviewPair("id-00", "v2-x", 0.91, "semantic-v1", "similar")]
    a = build_human_review_queue(items, flags)
    b = build_human_review_queue(items[::-1], flags)
    assert a == b
    assert a["flagged_candidate_ids"] == ["id-00"]
    assert len(a["sampled_non_flagged_candidate_ids"]) >= 15


def test_review_queue_rejects_conflicting_duplicate_flags():
    items = [candidate("id-00")]
    flags = [
        ReviewPair("id-00", "v2-x", 0.91, "semantic-v1", "similar"),
        ReviewPair("id-00", "v2-x", 0.72, "semantic-v1", "different evidence"),
    ]
    with pytest.raises(ValueError, match="conflicting duplicate review pair"):
        build_human_review_queue(items, flags)


def test_review_pair_rejects_boolean_score_and_blank_metadata():
    with pytest.raises(ValueError, match="finite similarity score"):
        ReviewPair("id-00", "v2-x", True, "semantic-v1", "similar").validate()
    with pytest.raises(ValueError, match="complete review-pair metadata"):
        ReviewPair("id-00", "   ", 0.5, "semantic-v1", "similar").validate()


def test_small_nonflagged_pool_samples_all_available():
    items = [candidate(f"id-{i}") for i in range(5)]
    assert len(deterministic_sample_ids(items)) == 5


def report(role: str, outcomes: tuple[bool, ...], *, runtime_failure=False):
    if len(outcomes) > 30:
        raise ValueError("fixture outcomes may not exceed frozen validation size")
    padded = outcomes + (True,) * (30 - len(outcomes))
    return ValidationReport(
        model_role=role,
        model_identity=role,
        scorer_sha256="a" * 64,
        runtime_identity="llama.cpp-paired",
        prompt_contract_sha256="b" * 64,
        cases=tuple(
            ValidationCase(
                f"c{i}",
                "json" if i % 2 == 0 else "instruction",
                passed,
                runtime_failure=runtime_failure and i == 0,
            )
            for i, passed in enumerate(padded)
        ),
    )


def test_validation_comparison_never_opens_v2_or_promotes():
    result = compare_validation(
        report("paired_current", (True, False, True)),
        report("candidate", (True, True, False)),
    )
    assert result["historical_v2_opened"] is False
    assert result["promotion_decision"] == "NOT_AUTHORIZED_FROM_VALIDATION"
    assert result["improvements"] == ["c1"]
    assert result["regressions"] == ["c2"]


def test_runtime_failure_blocks_v2_opening():
    result = compare_validation(
        report("paired_current", (True, True)),
        report("candidate", (True, True), runtime_failure=True),
    )
    assert result["blocks_v2_opening"] is True
