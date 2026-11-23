"""Deterministic contamination-review planning without model/network calls."""

from __future__ import annotations

import hashlib
import math
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
        if type(self) is not ReviewPair:
            raise ValueError("exact ReviewPair required")
        for name in ("candidate_id", "protected_id", "detector", "reason"):
            value = object.__getattribute__(self, name)
            if type(value) is not str or not value.strip():
                raise ValueError("complete review-pair metadata required")
        score = object.__getattribute__(self, "score")
        if type(score) not in (int, float):
            raise ValueError("finite similarity score must be an exact number")
        try:
            measured = float(score)
        except (OverflowError, ValueError) as exc:
            raise ValueError("finite similarity score must be within [0, 1]") from exc
        if not math.isfinite(measured) or not 0.0 <= measured <= 1.0:
            raise ValueError("finite similarity score must be within [0, 1]")


def _require_exact_items(value: object, name: str) -> list:
    if type(value) is not list:
        raise ValueError(f"{name} must be an exact list")
    return value


def _require_candidate_id(item: object) -> str:
    if type(item) is not LearningCandidate:
        raise ValueError("exact LearningCandidate required")
    candidate_id = object.__getattribute__(item, "candidate_id")
    if type(candidate_id) is not str or not candidate_id.strip():
        raise ValueError("accepted candidate ID must be exact non-empty text")
    return candidate_id


def _validate_sample_policy(fraction: object, minimum: object) -> tuple[float, int]:
    if type(fraction) not in (int, float) or type(minimum) is not int:
        raise ValueError("invalid sample policy")
    try:
        measured_fraction = float(fraction)
    except (OverflowError, ValueError) as exc:
        raise ValueError("invalid sample policy") from exc
    if not math.isfinite(measured_fraction) or not 0.0 < measured_fraction <= 1.0:
        raise ValueError("invalid sample policy")
    if minimum < 1:
        raise ValueError("invalid sample policy")
    return measured_fraction, minimum


def deterministic_sample_ids(
    items: list[LearningCandidate],
    *,
    fraction: float = 0.10,
    minimum: int = 15,
) -> list[str]:
    """Choose a stable SHA-ordered human-review sample from non-flagged examples."""
    rows = _require_exact_items(items, "items")
    measured_fraction, minimum = _validate_sample_policy(fraction, minimum)
    identifiers = [_require_candidate_id(item) for item in rows]
    unique = {
        candidate_id: item
        for candidate_id, item in zip(identifiers, rows, strict=True)
    }
    count = min(
        len(unique),
        max(minimum, (len(unique) * int(measured_fraction * 100) + 99) // 100),
    )
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
    accepted_rows = _require_exact_items(accepted, "accepted")
    flagged_rows = _require_exact_items(flagged_pairs, "flagged_pairs")
    measured_fraction, minimum = _validate_sample_policy(fraction, minimum)
    accepted_with_ids = [
        (item, _require_candidate_id(item)) for item in accepted_rows
    ]
    ids = {candidate_id for _, candidate_id in accepted_with_ids}
    flagged_ids: set[str] = set()
    pairs: list[dict] = []
    seen_pairs: dict[tuple[str, str, str], tuple[float, str]] = {}
    for pair in flagged_rows:
        if type(pair) is not ReviewPair:
            raise ValueError("exact ReviewPair required")
        pair.validate()
        if pair.candidate_id not in ids:
            raise ValueError("flag references a non-accepted candidate")
        key = (pair.candidate_id, pair.protected_id, pair.detector)
        evidence = (pair.score, pair.reason)
        if key in seen_pairs:
            if seen_pairs[key] != evidence:
                raise ValueError("conflicting duplicate review pair")
            continue
        seen_pairs[key] = evidence
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

    non_flagged = [
        item for item, candidate_id in accepted_with_ids
        if candidate_id not in flagged_ids
    ]
    sampled = (
        deterministic_sample_ids(
            non_flagged, fraction=measured_fraction, minimum=minimum,
        )
        if non_flagged
        else []
    )
    return {
        "policy": {
            "flagged_pair_review": "100_percent",
            "non_flagged_fraction": measured_fraction,
            "non_flagged_minimum": minimum,
            "escalation": (
                "any suspicious sampled item -> review 100% accepted examples"
            ),
        },
        "flagged_pairs": sorted(
            pairs,
            key=lambda row: (
                row["candidate_id"],
                row["protected_id"],
                row["detector"],
            ),
        ),
        "flagged_candidate_ids": sorted(flagged_ids),
        "sampled_non_flagged_candidate_ids": sampled,
        "accepted_count": len(accepted),
    }
