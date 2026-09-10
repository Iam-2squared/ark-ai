import hashlib

import pytest

from ark.learning.audit import build_human_review_queue
from ark.learning.dataset import ContaminationGuard, LearningCandidate, build_dataset
from ark.learning.freeze import (
    AuditDecision,
    DatasetFreezeBlocked,
    freeze_experiment_001_dataset,
    required_review_keys,
)


def make_items():
    items = []
    for index in range(150):
        split = "train" if index < 120 else "validation"
        prefix = "train" if split == "train" else "validation"
        source = f"owned://v3/{prefix}/{index}"
        items.append(
            LearningCandidate(
                candidate_id=f"ex-{index:03d}",
                source_type="human_authored",
                source_reference=source,
                input=f"Independent format task {index}",
                model_response="",
                evaluation="manual independent format target",
                approved_target=f"TARGET-{index:03d}",
                rejection_reason="",
                provenance="owned experiment-001 test fixture",
                created_at="2026-09-10T00:00:00+00:00",
                reviewer="fixture-reviewer",
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                rights="owned",
                approved=True,
                independent=True,
                split=split,
                group=f"{prefix}-family-{index // 5:03d}",
            )
        )
    return items


def empty_guard():
    return ContaminationGuard((), (), ())


def decisions_for(items):
    dataset = build_dataset(items, empty_guard())
    accepted = [item for item in items if item.candidate_id in {f"ex-{i:03d}" for i in range(150)}]
    queue = build_human_review_queue(accepted, [])
    return [
        AuditDecision(key, "human-reviewer", "independent", "reviewed")
        for key in required_review_keys(queue)
    ]


def test_freeze_requires_exact_120_30():
    items = make_items()[:-1]
    with pytest.raises(DatasetFreezeBlocked, match="120 train / 30 validation"):
        freeze_experiment_001_dataset(items, empty_guard(), [], [])


def test_freeze_is_deterministic_and_emits_three_snapshot_hashes():
    items = make_items()
    decisions = decisions_for(items)
    first = freeze_experiment_001_dataset(items, empty_guard(), [], decisions)
    second = freeze_experiment_001_dataset(list(reversed(items)), empty_guard(), [], decisions)
    assert first.dataset.sha256 == second.dataset.sha256
    assert first.provenance_sha256 == second.provenance_sha256
    assert first.contamination_sha256 == second.contamination_sha256
    assert len(first.review_queue_sha256) == 64
    assert first.dataset.summary["train_examples"] == 120
    assert first.dataset.summary["validation_examples"] == 30


def test_missing_manual_review_blocks_freeze():
    items = make_items()
    decisions = decisions_for(items)
    with pytest.raises(DatasetFreezeBlocked, match="audit decisions do not match queue"):
        freeze_experiment_001_dataset(items, empty_guard(), [], decisions[:-1])


def test_suspicious_manual_review_blocks_freeze():
    items = make_items()
    decisions = decisions_for(items)
    decisions[0] = AuditDecision(decisions[0].review_key, "human-reviewer", "suspicious", "needs review")
    with pytest.raises(DatasetFreezeBlocked, match="contamination suspicion"):
        freeze_experiment_001_dataset(items, empty_guard(), [], decisions)
