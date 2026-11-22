"""Fail-closed validation for V3 real-experiment execution snapshots.

This module never starts training, downloads models, or contacts external compute.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from pathlib import Path
from typing import Literal

_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_REPARSE_POINT_ATTRIBUTE = _REPARSE_POINT_ATTRIBUTE
_ORIGINAL_OS = os
_ORIGINAL_FSTAT = os.fstat
_ORIGINAL_STAT = stat
_ORIGINAL_S_ISREG = stat.S_ISREG
_ORIGINAL_S_ISLNK = stat.S_ISLNK


def _require_original_stat_policy(
    _original_os: object = _ORIGINAL_OS,
    _original_fstat: object = _ORIGINAL_FSTAT,
) -> None:
    if (
        os is not _original_os
        or _ORIGINAL_OS is not _original_os
        or _ORIGINAL_FSTAT is not _original_fstat
        or _original_os.fstat is not _original_fstat
        or stat is not _ORIGINAL_STAT
        or _ORIGINAL_STAT.S_ISREG is not _ORIGINAL_S_ISREG
        or _ORIGINAL_STAT.S_ISLNK is not _ORIGINAL_S_ISLNK
        or type(_REPARSE_POINT_ATTRIBUTE) is not int
        or _REPARSE_POINT_ATTRIBUTE != _ORIGINAL_REPARSE_POINT_ATTRIBUTE
    ):
        raise ValueError("execution snapshot stat policy changed")


def _is_regular_file(info: object) -> bool:
    _require_original_stat_policy()
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise ValueError("execution snapshot file mode is malformed")
    return _ORIGINAL_S_ISREG(mode)


def _is_reparse_point(info: object) -> bool:
    _require_original_stat_policy()
    attributes = getattr(info, "st_file_attributes", 0)
    _require_original_stat_policy()
    if type(attributes) is not int:
        raise ValueError("execution snapshot reparse metadata is malformed")
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise ValueError("execution snapshot file mode is malformed")
    return _ORIGINAL_S_ISLNK(mode) or bool(
        attributes & _REPARSE_POINT_ATTRIBUTE
    )


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

_REQUIRED_SECTION_KEYS = {
    "authorization": {
        "external_compute_authorized",
        "preflight_authorized",
        "real_training_authorized",
        "v2_opening_authorized",
        "promotion_authorized",
    },
    "code": {"git_sha", "manifest_sha256", "clean_tree_required"},
    "base": {"model_id", "revision", "file_sha256_manifest"},
    "tokenizer": {
        "revision",
        "file_sha256_manifest",
        "chat_template_probe_sha256",
    },
    "dataset": {
        "train_count",
        "validation_count",
        "canonical_sha256",
        "provenance_manifest_sha256",
        "contamination_report_sha256",
    },
    "method": {
        "name",
        "rank",
        "alpha",
        "dropout",
        "target_modules",
        "epochs",
        "learning_rate",
        "seed",
        "max_sequence_length",
        "microbatch",
        "gradient_accumulation",
        "optimizer",
        "optimizer_betas",
        "optimizer_eps",
        "optimizer_weight_decay",
        "optimizer_amsgrad",
        "optimizer_maximize",
        "scheduler",
        "precision",
        "gradient_checkpointing",
    },
    "environment": {
        "os_or_image_digest",
        "python",
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "cuda_runtime",
        "bitsandbytes",
    },
    "hardware": {"device", "vram_gib", "driver", "preflight_report_sha256"},
    "budget": {"full_candidate_runs", "max_cost_jpy", "wall_clock_timeout_minutes"},
    "export": {
        "llama_cpp_revision",
        "converter_identity",
        "quantizer_identity",
        "quantization",
        "paired_baseline_required",
    },
    "evaluation": {
        "validation_count",
        "v2_current_runs",
        "v2_candidate_runs",
        "v2_opening_requires_explicit_authorization",
        "no_retuning_after_v2_opening",
    },
    "privacy": {
        "private_sessions_allowed",
        "personal_memory_allowed",
        "secrets_allowed",
        "unattributed_text_allowed",
    },
}


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject_nonstandard_json_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON constant is forbidden: {token}")


_MAX_EXECUTION_SNAPSHOT_BYTES = 1_048_576
_MAX_EXECUTION_SNAPSHOT_DEPTH = 128


def _require_exact_json_tree(value: object) -> None:
    """Reject non-JSON carriers before validation can invoke their callbacks.

    Direct in-memory callers receive the same exact built-in JSON value
    boundary as the local snapshot loader. Shared mutable containers are
    rejected because JSON cannot represent aliases and validation must not
    read one object through multiple changing paths.
    """
    pending = [(value, 0)]
    seen_containers: set[int] = set()
    while pending:
        current, depth = pending.pop()
        if depth > _MAX_EXECUTION_SNAPSHOT_DEPTH:
            raise ExecutionBlocked("execution snapshot JSON nesting budget exceeded")
        kind = type(current)
        if kind is dict:
            identity = id(current)
            if identity in seen_containers:
                raise ExecutionBlocked("execution snapshot JSON containers must not be aliased")
            seen_containers.add(identity)
            for key, child in current.items():
                if type(key) is not str:
                    raise ExecutionBlocked(
                        "execution snapshot JSON object keys require exact strings"
                    )
                try:
                    key.encode("utf-8", errors="strict")
                except UnicodeError as exc:
                    raise ExecutionBlocked(
                        "execution snapshot JSON key is not valid UTF-8"
                    ) from exc
                pending.append((child, depth + 1))
        elif kind is list:
            identity = id(current)
            if identity in seen_containers:
                raise ExecutionBlocked("execution snapshot JSON containers must not be aliased")
            seen_containers.add(identity)
            pending.extend((child, depth + 1) for child in current)
        elif kind is str:
            try:
                current.encode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise ExecutionBlocked("execution snapshot JSON string is not valid UTF-8") from exc
        elif kind is float:
            # Field-specific numeric validators preserve their precise diagnostics.
            continue
        elif current is None or kind is bool or kind is int:
            continue
        else:
            raise ExecutionBlocked("execution snapshot must contain exact JSON value types")


def _require_bounded_snapshot_nesting(raw: bytes) -> None:
    """Reject excessive container depth without relying on Python recursion."""
    depth = 0
    quoted = False
    escaped = False
    for byte in raw:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                quoted = False
        elif byte == 0x22:
            quoted = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            if depth > _MAX_EXECUTION_SNAPSHOT_DEPTH:
                raise ValueError("execution snapshot JSON nesting budget exceeded")
        elif byte in (0x7D, 0x5D):
            depth -= 1


def _finite_json_float(text: str) -> float:
    value = float(text)
    if not math.isfinite(value):
        raise ValueError("execution snapshot JSON contains nonfinite numeric value")
    return value


def _unique_snapshot_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous duplicate authorization/identity keys at every depth.

    Noncanonical whitespace and key ordering remain accepted, but two textual
    declarations of the same JSON member must never silently use last-wins.
    """
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("execution snapshot contains duplicate JSON key")
        result[name] = value
    return result


def _snapshot_stat_identity(info: os.stat_result) -> tuple[int, int, int, int]:
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


def load_snapshot(path: Path) -> dict:
    """Read only bounded, finite local snapshot JSON; never start compute.

    This loader intentionally preserves noncanonical-but-valid object JSON.
    Frozen experiment semantics and authorization gates remain the responsibility
    of validate_experiment_001; loading is never proof of approval.
    """
    _require_original_stat_policy()
    source = Path(path)
    # PathLike conversion can execute caller code; do not inspect the path
    # until the import-original classification policy is rechecked.
    _require_original_stat_policy()
    try:
        initial_path_stat = source.lstat()
        _require_original_stat_policy()
    except OSError as exc:
        raise ValueError("execution snapshot cannot be read") from exc
    if (
        not _is_regular_file(initial_path_stat)
        or _is_reparse_point(initial_path_stat)
    ):
        raise ValueError("execution snapshot source must be a regular local file")
    if initial_path_stat.st_size > _MAX_EXECUTION_SNAPSHOT_BYTES:
        raise ValueError("execution snapshot exceeds JSON byte budget")
    try:
        _require_original_stat_policy()
        with source.open("rb") as handle:
            _require_original_stat_policy()
            initial_stat = _ORIGINAL_FSTAT(handle.fileno())
            if (
                not _is_regular_file(initial_stat)
                or _is_reparse_point(initial_stat)
                or _snapshot_stat_identity(initial_stat)
                != _snapshot_stat_identity(initial_path_stat)
            ):
                raise ValueError(
                    "execution snapshot source changed before JSON decode"
                )
            raw = handle.read(_MAX_EXECUTION_SNAPSHOT_BYTES + 1)
            _require_original_stat_policy()
    except OSError as exc:
        raise ValueError("execution snapshot cannot be read") from exc
    if len(raw) > _MAX_EXECUTION_SNAPSHOT_BYTES:
        raise ValueError("execution snapshot exceeds JSON byte budget")
    _require_bounded_snapshot_nesting(raw)
    try:
        parsed = json.loads(
            raw,
            parse_constant=_reject_nonstandard_json_constant,
            parse_float=_finite_json_float,
            object_pairs_hook=_unique_snapshot_pairs,
        )
    except (UnicodeDecodeError, RecursionError, OverflowError, json.JSONDecodeError) as exc:
        raise ValueError("execution snapshot JSON cannot be decoded") from exc
    if not isinstance(parsed, dict):
        raise ValueError("execution snapshot must be a JSON object")

    # The decoded object must still represent the same local file epoch.
    # Recheck the actual bytes and file identity after arbitrary decoder
    # callbacks. This is local TOCTOU defense, not a filesystem lock,
    # authenticated provenance, or compute authorization.
    try:
        _require_original_stat_policy()
        final_path_stat = source.lstat()
        _require_original_stat_policy()
        with source.open("rb") as handle:
            _require_original_stat_policy()
            final_stat = _ORIGINAL_FSTAT(handle.fileno())
            if (
                not _is_regular_file(final_path_stat)
                or _is_reparse_point(final_path_stat)
                or not _is_regular_file(final_stat)
                or _is_reparse_point(final_stat)
                or _snapshot_stat_identity(final_stat)
                != _snapshot_stat_identity(initial_stat)
                or _snapshot_stat_identity(final_path_stat)
                != _snapshot_stat_identity(initial_stat)
            ):
                raise ValueError(
                    "execution snapshot source changed during JSON decode"
                )
            final_bytes = handle.read(_MAX_EXECUTION_SNAPSHOT_BYTES + 1)
            _require_original_stat_policy()
    except OSError as exc:
        raise ValueError(
            "execution snapshot source changed during JSON decode"
        ) from exc
    if (
        final_bytes != raw
        or _snapshot_stat_identity(final_stat)
        != _snapshot_stat_identity(initial_stat)
        or _snapshot_stat_identity(final_path_stat)
        != _snapshot_stat_identity(initial_stat)
    ):
        raise ValueError("execution snapshot source changed during JSON decode")
    _require_original_stat_policy()
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
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ExecutionBlocked(f"exact SHA-256 required: {field}")


def _require_git_sha(value: object, field: str) -> None:
    if type(value) is not str or re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ExecutionBlocked(f"exact git commit SHA required: {field}")


def _require_text(value: object, field: str) -> None:
    if type(value) is not str or not value.strip():
        raise ExecutionBlocked(f"exact identity required: {field}")


def _require_positive_number(value: object, field: str) -> None:
    message = f"finite positive numeric value required: {field}"
    if type(value) not in (int, float) or value <= 0:
        raise ExecutionBlocked(message)
    try:
        measured = float(value)
    except (OverflowError, ValueError) as exc:
        raise ExecutionBlocked(message) from exc
    if not math.isfinite(measured):
        raise ExecutionBlocked(message)
    # Unit conversions must remain finite before any authorized compute.
    scales = {
        "hardware.vram_gib": 1024.0,
        "budget.wall_clock_timeout_minutes": 60.0,
    }
    if field in scales and not math.isfinite(measured * scales[field]):
        raise ExecutionBlocked(message)


def _require_exact_section_shape(snapshot: dict, section: str) -> None:
    value = snapshot.get(section)
    if type(value) is not dict:
        raise ExecutionBlocked(f"snapshot section must be an exact object: {section}")
    expected = _REQUIRED_SECTION_KEYS[section]
    missing = sorted(expected - value.keys())
    unexpected = sorted(value.keys() - expected)
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unexpected:
            details.append("unexpected=" + ",".join(unexpected))
        raise ExecutionBlocked(f"snapshot section shape mismatch: {section} ({'; '.join(details)})")


def validate_experiment_001(
    snapshot: dict, *, authorization_scope: AuthorizationScope = "none"
) -> str:
    # The scope is an execution authorization boundary, not a duck-typed
    # equality comparison: bool, str subclasses and custom objects must not
    # impersonate the literal preflight/training scopes.
    if type(authorization_scope) is not str or authorization_scope not in {
        "none", "preflight", "training",
    }:
        raise ValueError("invalid authorization scope")
    if type(snapshot) is not dict:
        raise ExecutionBlocked("exact execution snapshot mapping required")
    _require_exact_json_tree(snapshot)
    missing = sorted(_REQUIRED_TOP - snapshot.keys())
    if missing:
        raise ExecutionBlocked(f"snapshot missing sections: {', '.join(missing)}")
    unexpected = sorted(snapshot.keys() - _REQUIRED_TOP)
    if unexpected:
        raise ExecutionBlocked(f"snapshot contains unknown sections: {', '.join(unexpected)}")
    for section in _REQUIRED_SECTION_KEYS:
        _require_exact_section_shape(snapshot, section)
    if (
        type(snapshot.get("schema_version")) is not int
        or snapshot.get("schema_version") != 1
        or type(snapshot.get("experiment_id")) is not str
        or snapshot.get("experiment_id") != "v3-format-compliance-001"
    ):
        raise ExecutionBlocked("unexpected snapshot schema/experiment")
    method = snapshot["method"]
    integer_method_fields = (
        "rank",
        "alpha",
        "epochs",
        "seed",
        "max_sequence_length",
        "microbatch",
        "gradient_accumulation",
    )
    if any(type(method.get(key)) is not int for key in integer_method_fields):
        raise ExecutionBlocked("experiment-001 integer method fields require exact integers")
    numeric_method_fields = (
        "dropout",
        "learning_rate",
        "optimizer_eps",
        "optimizer_weight_decay",
    )
    if any(type(method.get(key)) not in (int, float) for key in numeric_method_fields):
        raise ExecutionBlocked("experiment-001 numeric method fields may not be booleans")
    boolean_method_fields = (
        "optimizer_amsgrad",
        "optimizer_maximize",
        "gradient_checkpointing",
    )
    if any(type(method.get(key)) is not bool for key in boolean_method_fields):
        raise ExecutionBlocked("experiment-001 boolean method fields require exact booleans")

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
    train_count = dataset.get("train_count")
    validation_count = dataset.get("validation_count")
    if (
        type(train_count) is not int
        or type(validation_count) is not int
        or train_count != 120
        or validation_count != 30
    ):
        raise ExecutionBlocked("experiment-001 requires exactly 120 train / 30 validation")
    full_candidate_runs = snapshot["budget"].get("full_candidate_runs")
    if type(full_candidate_runs) is not int or full_candidate_runs != 1:
        raise ExecutionBlocked("experiment-001 allows exactly one full Candidate run")
    if snapshot["export"].get("quantization") != "Q4_K_M":
        raise ExecutionBlocked("deployment comparison quantization must be Q4_K_M")
    if snapshot["export"].get("paired_baseline_required") is not True:
        raise ExecutionBlocked("paired Q4_K_M baseline is required")
    evaluation = snapshot["evaluation"]
    evaluation_counts = (
        evaluation.get("validation_count"),
        evaluation.get("v2_current_runs"),
        evaluation.get("v2_candidate_runs"),
    )
    if (
        any(type(value) is not int for value in evaluation_counts)
        or evaluation_counts != (30, 2, 2)
    ):
        raise ExecutionBlocked("validation/V2 budget must remain 30 and 2 Current + 2 Candidate")
    if snapshot["evaluation"].get("v2_opening_requires_explicit_authorization") is not True:
        raise ExecutionBlocked("V2 opening must remain behind explicit authorization")
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
            raise ExecutionBlocked(
                "pre-authorization snapshot must keep compute authorizations false"
            )
    elif authorization_scope == "preflight":
        if (
            auth["external_compute_authorized"] is not True
            or auth["preflight_authorized"] is not True
        ):
            raise ExecutionBlocked("explicit external-compute and preflight authorization required")
        if auth["real_training_authorized"]:
            raise ExecutionBlocked(
                "preflight authorization must not imply full training authorization"
            )
    else:
        if (
            auth["external_compute_authorized"] is not True
            or auth["real_training_authorized"] is not True
        ):
            raise ExecutionBlocked(
                "explicit external-compute and real-training authorization required"
            )
        if auth["preflight_authorized"] is not True:
            raise ExecutionBlocked("successful authorized preflight must precede full training")

    return sha256_bytes(canonical_json(snapshot))
