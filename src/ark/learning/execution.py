"""Fail-closed validation for V3 real-experiment execution snapshots.

This module never starts training, downloads models, or contacts external compute.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


class ExecutionBlocked(RuntimeError):
    """Raised when a real-experiment snapshot is not fully frozen/authorized."""


_REQUIRED_TOP = {
    "schema_version",
    "experiment_id",
    "authorization",
    "code",
    "base",
    "tokenizer",
    "dataset",
    "method",
    "environment",
    "hardware",
    "budget",
    "export",
    "evaluation",
    "privacy",
}


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_snapshot(path: Path) -> dict:
    raw = Path(path).read_bytes()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("execution snapshot must be a JSON object")
    return parsed


def unresolved_paths(value: object, prefix: str = "") -> list[str]:
    unresolved: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            unresolved.extend(unresolved_paths(child, path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            unresolved.extend(unresolved_paths(child, f"{prefix}[{index}]"))
    elif isinstance(value, str) and (
        value == "UNRESOLVED" or value.endswith("_REQUIRED") or value == "USER_APPROVAL_REQUIRED"
    ):
        unresolved.append(prefix)
    return unresolved


def validate_experiment_001(snapshot: dict, *, require_training_authorization: bool = False) -> str:
    missing = sorted(_REQUIRED_TOP - snapshot.keys())
    if missing:
        raise ExecutionBlocked(f"snapshot missing sections: {', '.join(missing)}")
    if snapshot.get("schema_version") != 1 or snapshot.get("experiment_id") != "v3-format-compliance-001":
        raise ExecutionBlocked("unexpected snapshot schema/experiment")

    method = snapshot["method"]
    expected = {
        "name": "lora",
        "rank": 8,
        "alpha": 16,
        "dropout": 0.0,
        "target_modules": ["q_proj", "v_proj"],
        "epochs": 1,
        "learning_rate": 0.0001,
        "seed": 42,
        "max_sequence_length": 256,
        "microbatch": 1,
        "gradient_accumulation": 8,
    }
    for key, value in expected.items():
        if method.get(key) != value:
            raise ExecutionBlocked(f"experiment-001 precommit mismatch: method.{key}")

    dataset = snapshot["dataset"]
    if dataset.get("train_count") != 120 or dataset.get("validation_count") != 30:
        raise ExecutionBlocked("experiment-001 requires exactly 120 train / 30 validation")
    if snapshot["budget"].get("full_candidate_runs") != 1:
        raise ExecutionBlocked("experiment-001 allows exactly one full Candidate run")
    if snapshot["export"].get("quantization") != "Q4_K_M":
        raise ExecutionBlocked("deployment comparison quantization must be Q4_K_M")
    if snapshot["evaluation"].get("v2_current_runs") != 2 or snapshot["evaluation"].get("v2_candidate_runs") != 2:
        raise ExecutionBlocked("historical V2 opening budget must remain 2 Current + 2 Candidate")

    privacy = snapshot["privacy"]
    forbidden = ("private_sessions_allowed", "personal_memory_allowed", "secrets_allowed", "unattributed_text_allowed")
    if any(privacy.get(key) is not False for key in forbidden):
        raise ExecutionBlocked("experiment-001 privacy policy violated")

    pending = unresolved_paths(snapshot)
    if pending:
        raise ExecutionBlocked("unresolved execution identities: " + ", ".join(sorted(pending)))

    auth = snapshot["authorization"]
    if auth.get("v2_opening_authorized") or auth.get("promotion_authorized"):
        raise ExecutionBlocked("training snapshot may not pre-authorize V2 opening or promotion")
    if require_training_authorization:
        if auth.get("real_training_authorized") is not True or auth.get("external_compute_authorized") is not True:
            raise ExecutionBlocked("explicit real-training and external-compute authorization required")
    else:
        if auth.get("real_training_authorized") or auth.get("external_compute_authorized"):
            raise ExecutionBlocked("pre-authorization snapshot must keep real/external authorization false")

    return sha256_bytes(canonical_json(snapshot))
