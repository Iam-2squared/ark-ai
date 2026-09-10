"""Fail-closed validation for V3 real-experiment execution snapshots.

This module never starts training, downloads models, or contacts external compute.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Literal


class ExecutionBlocked(RuntimeError):
    """Raised when a real-experiment snapshot is not fully frozen/authorized."""


AuthorizationScope = Literal["none", "preflight", "training"]

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
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_snapshot(path: Path) -> dict:
    raw = Path(path).read_bytes()
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("execution snapshot must be a JSON object")
    return parsed


def execution_core(snapshot: dict) -> dict:
    """Return the immutable experiment identity shared by preflight and full training.

    Authorization flags and the preflight report hash are intentionally excluded because
    they change between the preflight approval and the later full-training approval.
    Every experimental, data, code, runtime, hardware, budget and export identity remains.
    """
    core = {key: value for key, value in snapshot.items() if key != "authorization"}
    hardware = dict(snapshot.get("hardware", {}))
    hardware.pop("preflight_report_sha256", None)
    core["hardware"] = hardware
    return core


def execution_core_sha256(snapshot: dict) -> str:
    return sha256_bytes(canonical_json(execution_core(snapshot)))


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
        value == "UNRESOLVED"
        or value.endswith("_REQUIRED")
        or value == "USER_APPROVAL_REQUIRED"
    ):
        unresolved.append(prefix)
    return unresolved


def _require_sha256(value: object, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ExecutionBlocked(f"exact SHA-256 required: {field}")


def _require_git_sha(value: object, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ExecutionBlocked(f"exact git commit SHA required: {field}")


def _require_text(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ExecutionBlocked(f"exact identity required: {field}")


def _require_positive_number(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ExecutionBlocked(f"positive numeric value required: {field}")


def validate_experiment_001(
    snapshot: dict, *, authorization_scope: AuthorizationScope = "none"
) -> str:
    missing = sorted(_REQUIRED_TOP - snapshot.keys())
    if missing:
        raise ExecutionBlocked(f"snapshot missing sections: {', '.join(missing)}")
    if (
        snapshot.get("schema_version") != 1
        or snapshot.get("experiment_id") != "v3-format-compliance-001"
    ):
        raise ExecutionBlocked("unexpected snapshot schema/experiment")
    if authorization_scope not in {"none", "preflight", "training"}:
        raise ValueError("invalid authorization scope")

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
        "optimizer": "adamw_torch",
        "optimizer_betas": [0.9, 0.999],
        "optimizer_eps": 1e-8,
        "optimizer_weight_decay": 0.01,
        "optimizer_amsgrad": False,
        "optimizer_maximize": False,
        "scheduler": "constant",
        "precision": "bf16",
        "gradient_checkpointing": False,
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
    if snapshot["export"].get("paired_baseline_required") is not True:
        raise ExecutionBlocked("paired Q4_K_M baseline is required")
    if (
        snapshot["evaluation"].get("validation_count") != 30
        or snapshot["evaluation"].get("v2_current_runs") != 2
        or snapshot["evaluation"].get("v2_candidate_runs") != 2
    ):
        raise ExecutionBlocked("validation/V2 budget must remain 30 and 2 Current + 2 Candidate")
    if snapshot["evaluation"].get("no_retuning_after_v2_opening") is not True:
        raise ExecutionBlocked("V2 opening may not permit retuning experiment 001")

    privacy = snapshot["privacy"]
    forbidden = (
        "private_sessions_allowed",
        "personal_memory_allowed",
        "secrets_allowed",
        "unattributed_text_allowed",
    )
    if any(privacy.get(key) is not False for key in forbidden):
        raise ExecutionBlocked("experiment-001 privacy policy violated")

    allowed_pending = (
        {"hardware.preflight_report_sha256"}
        if authorization_scope in {"none", "preflight"}
        else set()
    )
    pending = sorted(set(unresolved_paths(snapshot)) - allowed_pending)
    if pending:
        raise ExecutionBlocked("unresolved execution identities: " + ", ".join(pending))

    code = snapshot["code"]
    _require_git_sha(code.get("git_sha"), "code.git_sha")
    _require_sha256(code.get("manifest_sha256"), "code.manifest_sha256")
    if code.get("clean_tree_required") is not True:
        raise ExecutionBlocked("clean repository state is required")

    base = snapshot["base"]
    if base.get("model_id") != "Qwen/Qwen3-4B-Instruct-2507":
        raise ExecutionBlocked("unexpected base model identity")
    _require_git_sha(base.get("revision"), "base.revision")
    _require_sha256(base.get("file_sha256_manifest"), "base.file_sha256_manifest")

    tokenizer = snapshot["tokenizer"]
    token_revision = tokenizer.get("revision")
    if token_revision not in {"SAME_AS_BASE", base.get("revision")}:
        raise ExecutionBlocked("tokenizer revision must equal the frozen base revision")
    _require_sha256(tokenizer.get("file_sha256_manifest"), "tokenizer.file_sha256_manifest")
    _require_sha256(
        tokenizer.get("chat_template_probe_sha256"), "tokenizer.chat_template_probe_sha256"
    )

    for field in (
        "canonical_sha256",
        "provenance_manifest_sha256",
        "contamination_report_sha256",
    ):
        _require_sha256(dataset.get(field), f"dataset.{field}")

    environment = snapshot["environment"]
    for field in (
        "os_or_image_digest",
        "python",
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "cuda_runtime",
    ):
        _require_text(environment.get(field), f"environment.{field}")
    if environment.get("bitsandbytes") != "NOT_REQUIRED_FOR_LORA":
        raise ExecutionBlocked("bitsandbytes must remain unused for experiment-001 LoRA")

    hardware = snapshot["hardware"]
    _require_text(hardware.get("device"), "hardware.device")
    _require_positive_number(hardware.get("vram_gib"), "hardware.vram_gib")
    _require_text(hardware.get("driver"), "hardware.driver")
    if authorization_scope == "training":
        _require_sha256(
            hardware.get("preflight_report_sha256"), "hardware.preflight_report_sha256"
        )
    elif hardware.get("preflight_report_sha256") != "UNRESOLVED":
        _require_sha256(
            hardware.get("preflight_report_sha256"), "hardware.preflight_report_sha256"
        )

    budget = snapshot["budget"]
    _require_positive_number(budget.get("max_cost_jpy"), "budget.max_cost_jpy")
    _require_positive_number(
        budget.get("wall_clock_timeout_minutes"), "budget.wall_clock_timeout_minutes"
    )

    export = snapshot["export"]
    _require_git_sha(export.get("llama_cpp_revision"), "export.llama_cpp_revision")
    _require_sha256(export.get("converter_identity"), "export.converter_identity")
    _require_sha256(export.get("quantizer_identity"), "export.quantizer_identity")

    auth = snapshot["authorization"]
    required_auth = {
        "external_compute_authorized",
        "preflight_authorized",
        "real_training_authorized",
        "v2_opening_authorized",
        "promotion_authorized",
    }
    if set(auth) != required_auth or any(type(auth[name]) is not bool for name in required_auth):
        raise ExecutionBlocked("authorization record must contain exact boolean fields")
    if auth["v2_opening_authorized"] or auth["promotion_authorized"]:
        raise ExecutionBlocked("training snapshot may not pre-authorize V2 opening or promotion")

    if authorization_scope == "none":
        if (
            auth["external_compute_authorized"]
            or auth["preflight_authorized"]
            or auth["real_training_authorized"]
        ):
            raise ExecutionBlocked("pre-authorization snapshot must keep compute authorizations false")
    elif authorization_scope == "preflight":
        if (
            auth["external_compute_authorized"] is not True
            or auth["preflight_authorized"] is not True
        ):
            raise ExecutionBlocked("explicit external-compute and preflight authorization required")
        if auth["real_training_authorized"]:
            raise ExecutionBlocked("preflight authorization must not imply full training authorization")
    else:
        if (
            auth["external_compute_authorized"] is not True
            or auth["real_training_authorized"] is not True
        ):
            raise ExecutionBlocked("explicit external-compute and real-training authorization required")
        if auth["preflight_authorized"] is not True:
            raise ExecutionBlocked("successful authorized preflight must precede full training")

    return sha256_bytes(canonical_json(snapshot))
