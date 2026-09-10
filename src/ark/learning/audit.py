"""Deterministic contamination-review planning without model/network calls."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .dataset import LearningCandidate


@dataclass(frozen=True)
class ReviewPair:
    candidate_id: str
    protected_id: str
    score: float
    detector: str
    reason: str

    def validate(self) -> None:
        if not self.candidate_id or not self.protected_id or not self.detector or not self.reason:
            raise ValueError("complete review-pair metadata required")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("similarity score must be within [0, 1]")


def deterministic_sample_ids(items: list[LearningCandidate], *, fraction: float = 0.10, minimum: int = 15) -> list[str]:
    """Choose a stable SHA-ordered human-review sample from non-flagged examples."""
    if not 0 < fraction <= 1 or minimum < 1:
        raise ValueError("invalid sample policy")
    unique = {item.candidate_id: item for item in items}
    count = min(len(unique), max(minimum, (len(unique) * int(fraction * 100) + 99) // 100))
    ordered = sorted(
        unique,
        key=lambda cid: hashlib.sha256(cid.encode("utf-8")).hexdigest(),
    )
    return ordered[:count]


def build_human_review_queue(
    accepted: list[LearningCandidate],
    flagged_pairs: list[ReviewPair],
    *,
    fraction: float = 0.10,
    minimum: int = 15,
) -> dict:
    """Return the exact manual-review queue required by the execution supplement.

    All flagged pairs are reviewed. Non-flagged accepted examples get a deterministic
    sample. This function does not claim that semantic leakage has been detected or
    excluded; it only freezes the review workload.
    """
    ids = {item.candidate_id for item in accepted}
    flagged_ids: set[str] = set()
    pairs: list[dict] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    for pair in flagged_pairs:
        pair.validate()
        if pair.candidate_id not in ids:
            raise ValueError("flag references a non-accepted candidate")
        key = (pair.candidate_id, pair.protected_id, pair.detector)
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        flagged_ids.add(pair.candidate_id)
        pairs.append(
            {
                "candidate_id": pair.candidate_id,
                "protected_id": pair.protected_id,
                "score": pair.score,
                "detector": pair.detector,
                "reason": pair.reason,
            }
        )

    non_flagged = [item for item in accepted if item.candidate_id not in flagged_ids]
    sampled = deterministic_sample_ids(non_flagged, fraction=fraction, minimum=minimum) if non_flagged else []
    return {
        "policy": {
            "flagged_pair_review": "100_percent",
            "non_flagged_fraction": fraction,
            "non_flagged_minimum": minimum,
            "escalation": "any suspicious sampled item -> review 100% accepted examples",
        },
        "flagged_pairs": sorted(pairs, key=lambda row: (row["candidate_id"], row["protected_id"], row["detector"])),
        "flagged_candidate_ids": sorted(flagged_ids),
        "sampled_non_flagged_candidate_ids": sampled,
        "accepted_count": len(accepted),
    }
