"""Freeze approved experiment-001 dataset/audit evidence without training or network calls."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .audit import ReviewPair, build_human_review_queue
from .dataset import (
    ContaminationGuard,
    DatasetArtifact,
    LearningCandidate,
    build_dataset,
    canonical,
    digest,
)


class DatasetFreezeBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class AuditDecision:
    review_key: str
    reviewer: str
    decision: str
    notes: str = ""

    def validate(self) -> None:
        if not self.review_key.strip() or not self.reviewer.strip():
            raise ValueError("audit review key/reviewer required")
        if self.decision not in {"independent", "suspicious"}:
            raise ValueError("audit decision must be independent or suspicious")


@dataclass(frozen=True)
class FrozenDatasetEvidence:
    dataset: DatasetArtifact
    provenance_payload: bytes
    provenance_sha256: str
    contamination_payload: bytes
    contamination_sha256: str
    review_queue_sha256: str


def _accepted_items(dataset: DatasetArtifact) -> list[LearningCandidate]:
    import json

    parsed = json.loads(dataset.payload)
    return [LearningCandidate(**row) for row in parsed["examples"]]


def _review_key_for_pair(row: dict) -> str:
    return "pair:{candidate}|{protected}|{detector}".format(
        candidate=row["candidate_id"],
        protected=row["protected_id"],
        detector=row["detector"],
    )


def required_review_keys(queue: dict) -> tuple[str, ...]:
    keys = [_review_key_for_pair(row) for row in queue["flagged_pairs"]]
    keys.extend(f"sample:{candidate_id}" for candidate_id in queue["sampled_non_flagged_candidate_ids"])
    return tuple(sorted(keys))


def freeze_experiment_001_dataset(
    items: list[LearningCandidate],
    guard: ContaminationGuard,
    flagged_pairs: list[ReviewPair],
    decisions: list[AuditDecision],
) -> FrozenDatasetEvidence:
    """Produce deterministic hashes only after all experiment-001 review gates close.

    The protected V2 prompt/target text is never written to these evidence payloads.
    `protected_id` is an opaque detector-side identifier supplied by the audit stage.
    """
    dataset = build_dataset(items, guard)
    if dataset.summary["train_examples"] != 120 or dataset.summary["validation_examples"] != 30:
        raise DatasetFreezeBlocked("experiment-001 dataset must contain exactly 120 train / 30 validation")
    if dataset.summary["rejected"] or dataset.summary["duplicates"] or dataset.summary["contamination_rejects"]:
        raise DatasetFreezeBlocked("final dataset freeze requires zero rejected/duplicate/contaminated inputs")

    accepted = _accepted_items(dataset)
    queue = build_human_review_queue(accepted, flagged_pairs)
    queue_payload = canonical(queue)
    queue_sha = digest(queue_payload)
    required = set(required_review_keys(queue))

    decision_map: dict[str, AuditDecision] = {}
    for decision in decisions:
        decision.validate()
        if decision.review_key in decision_map:
            raise DatasetFreezeBlocked("duplicate audit decision")
        decision_map[decision.review_key] = decision
    if set(decision_map) != required:
        missing = sorted(required - set(decision_map))
        extra = sorted(set(decision_map) - required)
        raise DatasetFreezeBlocked(f"audit decisions do not match queue; missing={missing}; extra={extra}")
    suspicious = sorted(
        decision.review_key for decision in decisions if decision.decision == "suspicious"
    )
    if suspicious:
        raise DatasetFreezeBlocked(
            "contamination suspicion requires expanded/manual resolution before freeze: "
            + ", ".join(suspicious)
        )

    provenance_rows = [
        {
            "candidate_id": item.candidate_id,
            "source_type": item.source_type,
            "source_reference": item.source_reference,
            "source_sha256": item.source_sha256,
            "rights": item.rights,
            "reviewer": item.reviewer,
            "approved": item.approved,
            "independent": item.independent,
            "split": item.split,
            "group": item.group,
        }
        for item in sorted(accepted, key=lambda row: row.candidate_id)
    ]
    provenance_payload = canonical(
        {
            "schema_version": 1,
            "experiment_id": "v3-format-compliance-001",
            "dataset_sha256": dataset.sha256,
            "examples": provenance_rows,
        }
    )

    ordered_decisions = [
        asdict(decision_map[key])
        for key in sorted(decision_map)
    ]
    decisions_payload = canonical(ordered_decisions)
    contamination_payload = canonical(
        {
            "schema_version": 1,
            "experiment_id": "v3-format-compliance-001",
            "dataset_sha256": dataset.sha256,
            "review_queue_sha256": queue_sha,
            "decision_set_sha256": digest(decisions_payload),
            "required_review_count": len(required),
            "flagged_pair_count": len(queue["flagged_pairs"]),
            "sampled_non_flagged_count": len(queue["sampled_non_flagged_candidate_ids"]),
            "reviewers": sorted({decision.reviewer for decision in decisions}),
            "result": "CLEAR_FOR_PRETRAINING_IDENTITY_FREEZE",
            "limitations": "heuristic detectors plus human review do not prove semantic independence",
        }
    )
    return FrozenDatasetEvidence(
        dataset=dataset,
        provenance_payload=provenance_payload,
        provenance_sha256=digest(provenance_payload),
        contamination_payload=contamination_payload,
        contamination_sha256=digest(contamination_payload),
        review_queue_sha256=queue_sha,
    )
