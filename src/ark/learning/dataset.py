"""Deterministic approved-example export, with explicit contamination limitations."""

from __future__ import annotations

import hashlib
import json
import math
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


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous duplicate object members at every JSON nesting level."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(value: str) -> None:
    """Reject JavaScript-style NaN/Infinity tokens that are not JSON values."""
    raise ValueError(f"non-standard JSON constant: {value}")


def _finite_json_float(value: str) -> float:
    """Reject exponent overflow that json.loads otherwise converts to infinity."""
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("non-finite JSON number")
    return parsed


def loads_unique_json(payload: str | bytes) -> object:
    """Parse strict JSON from exact built-in text/bytes without caller callbacks."""
    if type(payload) not in (str, bytes):
        raise TypeError("JSON payload must be an exact str or bytes value")
    return json.loads(
        payload,
        object_pairs_hook=_unique_json_object,
        parse_constant=_reject_nonstandard_json_constant,
        parse_float=_finite_json_float,
    )


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
        if type(self) is not _ORIGINAL_LEARNING_CANDIDATE_TYPE:
            raise ValueError("exact LearningCandidate required")
        if vars(_ORIGINAL_LEARNING_CANDIDATE_TYPE).get("validate") is not _ORIGINAL_LEARNING_CANDIDATE_VALIDATE:
            raise ValueError("LearningCandidate validator changed")
        if (
            type(object.__getattribute__(self, "schema_version")) is not int
            or object.__getattribute__(self, "schema_version") != 1
        ):
            raise ValueError("schema_version")
        text_fields = (
            "candidate_id", "source_type", "source_reference", "input",
            "model_response", "evaluation", "approved_target", "rejection_reason",
            "provenance", "created_at", "reviewer", "source_sha256", "rights",
            "split", "group",
        )
        values = {
            name: object.__getattribute__(self, name)
            for name in text_fields
        }
        for name, value in values.items():
            if type(value) is not str:
                raise ValueError(f"invalid {name}: exact string required")
        for name in (
            "candidate_id", "source_reference", "input", "evaluation",
            "approved_target", "provenance", "reviewer", "group",
        ):
            value = values[name]
            if not value.strip() or len(value) > 16000:
                raise ValueError(f"invalid {name}")
        if values["source_type"] not in {
            "human_authored", "approved_correction", "generated_reviewed",
        }:
            raise ValueError("unapproved source type")
        if (
            object.__getattribute__(self, "approved") is not True
            or object.__getattribute__(self, "independent") is not True
            or values["rejection_reason"]
        ):
            raise ValueError("approval and independence review required")
        if values["rights"] not in {"owned", "licensed", "public_domain"}:
            raise ValueError("rights review required")
        if not valid_sha(values["source_sha256"]):
            raise ValueError("source digest required")
        if values["split"] not in {"train", "validation"}:
            raise ValueError("evaluation is not an export split")
        if datetime.fromisoformat(values["created_at"]).tzinfo is None:
            raise ValueError("timestamp requires timezone")


_ORIGINAL_LEARNING_CANDIDATE_TYPE = LearningCandidate
_ORIGINAL_LEARNING_CANDIDATE_VALIDATE = vars(_ORIGINAL_LEARNING_CANDIDATE_TYPE)["validate"]


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
        if type(self) is not _ORIGINAL_CONTAMINATION_GUARD_TYPE:
            raise ValueError("exact ContaminationGuard required")
        if type(item) is not _ORIGINAL_LEARNING_CANDIDATE_TYPE:
            raise ValueError("exact LearningCandidate required")
        protected_inputs = object.__getattribute__(self, "protected_inputs")
        protected_targets = object.__getattribute__(self, "protected_targets")
        reference_markers = object.__getattribute__(self, "reference_markers")
        if any(
            type(values) is not tuple
            or any(type(value) is not str for value in values)
            for values in (protected_inputs, protected_targets, reference_markers)
        ):
            raise ValueError("contamination guard inputs must be exact immutable text tuples")
        source_reference = object.__getattribute__(item, "source_reference")
        provenance = object.__getattribute__(item, "provenance")
        candidate_input = object.__getattribute__(item, "input")
        approved_target = object.__getattribute__(item, "approved_target")
        model_response = object.__getattribute__(item, "model_response")
        if any(
            type(value) is not str
            for value in (
                source_reference, provenance, candidate_input,
                approved_target, model_response,
            )
        ):
            raise ValueError("contamination review requires exact candidate text")
        reference = normalized(source_reference + " " + provenance)
        if any(marker in reference for marker in reference_markers):
            return "protected_source_reference"
        prompt = normalized(candidate_input)
        for protected in protected_inputs:
            protected = normalized(protected)
            if protected in prompt or SequenceMatcher(None, prompt, protected).ratio() >= 0.85:
                return "protected_or_similar_input"
        combined = normalized(candidate_input + " " + approved_target + " " + model_response)
        for target in protected_targets:
            target = normalized(target)
            # Common one-word labels/numbers are not proof of leakage on their own.
            if (len(target) >= 4 or "/" in target) and target in combined:
                return "distinctive_protected_target"
        return None


_ORIGINAL_CONTAMINATION_GUARD_TYPE = ContaminationGuard
_ORIGINAL_CONTAMINATION_GUARD_REASON = vars(_ORIGINAL_CONTAMINATION_GUARD_TYPE)["reason"]


@dataclass(frozen=True)
class DatasetArtifact:
    payload: bytes
    sha256: str
    summary: dict


def build_dataset(items: list[LearningCandidate], guard: ContaminationGuard) -> DatasetArtifact:
    # This is the dataset admission boundary: reject callback-capable containers,
    # candidate subclasses and substituted validators before sorting or inspecting IDs.
    if type(items) is not list:
        raise ValueError("items must be an exact list")
    if type(guard) is not _ORIGINAL_CONTAMINATION_GUARD_TYPE:
        raise ValueError("exact ContaminationGuard required")
    if (
        vars(_ORIGINAL_LEARNING_CANDIDATE_TYPE).get("validate")
        is not _ORIGINAL_LEARNING_CANDIDATE_VALIDATE
        or vars(_ORIGINAL_CONTAMINATION_GUARD_TYPE).get("reason")
        is not _ORIGINAL_CONTAMINATION_GUARD_REASON
    ):
        raise ValueError("dataset admission policy implementation changed")
    identifiers: list[str] = []
    for item in items:
        if type(item) is not _ORIGINAL_LEARNING_CANDIDATE_TYPE:
            raise ValueError("exact LearningCandidate required")
        candidate_id = object.__getattribute__(item, "candidate_id")
        if type(candidate_id) is not str:
            raise ValueError("candidate ID must be an exact string")
        identifiers.append(candidate_id)
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate candidate IDs")
    ordered_items = (
        item for _, item in sorted(zip(identifiers, items), key=lambda pair: pair[0])
    )
    accepted, rejected, seen = [], [], {}
    duplicates = contamination = 0
    group_splits = {}
    for item in ordered_items:
        try:
            _ORIGINAL_LEARNING_CANDIDATE_VALIDATE(item)
            reason = _ORIGINAL_CONTAMINATION_GUARD_REASON(guard, item)
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
