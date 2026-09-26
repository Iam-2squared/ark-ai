"""Deterministic approved-example export, with explicit contamination limitations."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from difflib import SequenceMatcher


def canonical(value: object) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        + "\n"
    ).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def valid_sha(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


@dataclass(frozen=True)
class LearningCandidate:
    candidate_id: str
    source_type: str
    source_reference: str
    input: str
    model_response: str
    evaluation: str
    approved_target: str
    rejection_reason: str
    provenance: str
    created_at: str
    reviewer: str
    source_sha256: str
    rights: str
    approved: bool
    independent: bool
    split: str
    group: str
    schema_version: int = 1

    def validate(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("schema_version")
        for name in (
            "candidate_id",
            "source_reference",
            "input",
            "evaluation",
            "approved_target",
            "provenance",
            "reviewer",
            "group",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > 16000:
                raise ValueError(f"invalid {name}")
        if self.source_type not in {"human_authored", "approved_correction", "generated_reviewed"}:
            raise ValueError("unapproved source type")
        if self.approved is not True or self.independent is not True or self.rejection_reason:
            raise ValueError("approval and independence review required")
        if self.rights not in {"owned", "licensed", "public_domain"}:
            raise ValueError("rights review required")
        if not valid_sha(self.source_sha256):
            raise ValueError("source digest required")
        if self.split not in {"train", "validation"}:
            raise ValueError("evaluation is not an export split")
        if datetime.fromisoformat(self.created_at).tzinfo is None:
            raise ValueError("timestamp requires timezone")


@dataclass(frozen=True)
class ContaminationGuard:
    protected_inputs: tuple[str, ...]
    protected_targets: tuple[str, ...]
    reference_markers: tuple[str, ...] = ("ark-v2-foundation", "evidence/v2", "evaluation/")

    @classmethod
    def frozen_v2(cls) -> ContaminationGuard:
        # Read-only screening, never a candidate-model evaluation call.
        from ..evaluation.suite import load_suite

        cases = load_suite()["cases"]
        inputs = tuple(p for c in cases for p in [*c.get("setup", []), c["prompt"]])
        targets = tuple(str(c["expected"]) for c in cases if "expected" in c)
        return cls(inputs, targets)

    def reason(self, item: LearningCandidate) -> str | None:
        reference = normalized(item.source_reference + " " + item.provenance)
        if any(marker in reference for marker in self.reference_markers):
            return "protected_source_reference"
        prompt = normalized(item.input)
        for protected in self.protected_inputs:
            protected = normalized(protected)
            if protected in prompt or SequenceMatcher(None, prompt, protected).ratio() >= 0.85:
                return "protected_or_similar_input"
        combined = normalized(item.input + " " + item.approved_target + " " + item.model_response)
        for target in self.protected_targets:
            target = normalized(target)
            # Common one-word labels/numbers are not proof of leakage on their own.
            if (len(target) >= 4 or "/" in target) and target in combined:
                return "distinctive_protected_target"
        return None


@dataclass(frozen=True)
class DatasetArtifact:
    payload: bytes
    sha256: str
    summary: dict


def build_dataset(items: list[LearningCandidate], guard: ContaminationGuard) -> DatasetArtifact:
    if len({item.candidate_id for item in items}) != len(items):
        raise ValueError("duplicate candidate IDs")
    accepted, rejected, seen = [], [], {}
    duplicates = contamination = 0
    group_splits = {}
    for item in sorted(items, key=lambda c: c.candidate_id):
        try:
            item.validate()
            reason = guard.reason(item)
            if reason:
                contamination += 1
                raise ValueError(reason)
            key = normalized(item.input)
            if key in seen:
                prior = seen[key]
                if (prior.approved_target, prior.split, prior.group) != (
                    item.approved_target,
                    item.split,
                    item.group,
                ):
                    raise RuntimeError("conflicting duplicate input/target/split/group")
                duplicates += 1
                continue
            if item.group in group_splits and group_splits[item.group] != item.split:
                raise RuntimeError("source group crosses train/validation")
            group_splits[item.group] = item.split
            seen[key] = item
            accepted.append(item)
        except (ValueError, TypeError) as exc:
            rejected.append({"candidate_id": item.candidate_id, "reason": str(exc)})
    payload = canonical({"schema_version": 1, "examples": [asdict(i) for i in accepted]})
    summary = {
        "raw_candidates": len(items),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "duplicates": duplicates,
        "contamination_rejects": contamination,
        "train_examples": sum(i.split == "train" for i in accepted),
        "validation_examples": sum(i.split == "validation" for i in accepted),
        "dataset_bytes": len(payload),
        "dataset_sha256": digest(payload),
        "rejections": rejected,
        "semantic_independence": "human_attested_not_automatically_proven",
    }
    return DatasetArtifact(payload, digest(payload), summary)
