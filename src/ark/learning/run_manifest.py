"""Create-only evidence manifest for the single authorized V3 Candidate run.

This module never starts training, opens evaluation data, or performs network access.
It only inventories bytes that already exist in a newly-created Candidate run directory.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from .execution import (
    canonical_json,
    execution_core_sha256,
    sha256_bytes,
    validate_experiment_001,
)
from .identity import directory_file_identities


class CandidateRunManifestError(RuntimeError):
    pass


def _reject_nonstandard_json_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON constant is forbidden: {token}")


def _require_nonempty_directory(root: Path, relative: str) -> None:
    path = root / relative
    if not path.is_dir() or path.is_symlink():
        raise CandidateRunManifestError(
            f"Candidate run requires non-symlink directory: {relative}"
        )
    if not any(child.is_file() for child in path.rglob("*")):
        raise CandidateRunManifestError(f"Candidate run directory is empty: {relative}")


def _load_canonical_json(path: Path, label: str) -> tuple[dict, bytes]:
    payload = path.read_bytes()
    try:
        parsed = json.loads(payload, parse_constant=_reject_nonstandard_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise CandidateRunManifestError(f"{label} is not valid canonical JSON") from exc
    if not isinstance(parsed, dict) or canonical_json(parsed) != payload:
        raise CandidateRunManifestError(f"{label} is not valid canonical JSON")
    return parsed, payload


def _require_exact_int(metrics: dict, field: str, expected: int | None = None) -> int:
    value = metrics.get(field)
    if type(value) is not int or value <= 0:
        raise CandidateRunManifestError(f"training metrics {field} must be a positive integer")
    if expected is not None and value != expected:
        raise CandidateRunManifestError(
            f"training metrics {field} must equal frozen value {expected}"
        )
    return value


def _require_finite_number(
    metrics: dict,
    field: str,
    *,
    allow_zero: bool = False,
) -> float:
    value = metrics.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CandidateRunManifestError(f"training metrics {field} must be numeric")
    measured = float(value)
    if not math.isfinite(measured) or measured < 0 or (not allow_zero and measured == 0):
        qualifier = "finite non-negative" if allow_zero else "finite positive"
        raise CandidateRunManifestError(f"training metrics {field} must be {qualifier}")
    return measured


def _validate_training_metrics(snapshot: dict, metrics: dict, snapshot_sha: str) -> None:
    expected_fields = {
        "schema_version",
        "experiment_id",
        "execution_snapshot_sha256",
        "dataset_sha256",
        "optimizer_steps",
        "microbatches",
        "mean_training_loss",
        "peak_vram_mib",
        "peak_reserved_vram_mib",
        "wall_seconds",
        "trainable_parameters",
        "method",
    }
    if set(metrics) != expected_fields:
        raise CandidateRunManifestError("training metrics schema mismatch")
    if type(metrics["schema_version"]) is not int or metrics["schema_version"] != 1:
        raise CandidateRunManifestError("training metrics schema_version must equal 1")
    if metrics["experiment_id"] != snapshot["experiment_id"]:
        raise CandidateRunManifestError("training metrics experiment identity mismatch")
    if metrics["execution_snapshot_sha256"] != snapshot_sha:
        raise CandidateRunManifestError(
            "training metrics do not match the authorized execution snapshot"
        )
    if metrics["dataset_sha256"] != snapshot["dataset"]["canonical_sha256"]:
        raise CandidateRunManifestError("training metrics dataset identity mismatch")

    _require_exact_int(metrics, "optimizer_steps", 15)
    _require_exact_int(metrics, "microbatches", 120)
    _require_finite_number(metrics, "mean_training_loss", allow_zero=True)
    _require_finite_number(metrics, "peak_vram_mib")
    _require_finite_number(metrics, "peak_reserved_vram_mib")
    _require_finite_number(metrics, "wall_seconds")
    _require_exact_int(metrics, "trainable_parameters")

    method = metrics.get("method")
    if not isinstance(method, dict) or canonical_json(method) != canonical_json(snapshot["method"]):
        raise CandidateRunManifestError("training metrics method does not match frozen recipe")


def _validate_candidate_evidence(snapshot: dict, root: Path) -> str:
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="training")
    if not root.is_dir() or root.is_symlink():
        raise CandidateRunManifestError(
            "Candidate run root must be an existing non-symlink directory"
        )

    _require_nonempty_directory(root, "adapter")
    _require_nonempty_directory(root, "tokenizer")

    metrics_path = root / "training-metrics.json"
    snapshot_path = root / "execution-snapshot.json"
    for path, label in (
        (metrics_path, "training metrics"),
        (snapshot_path, "execution snapshot"),
    ):
        if not path.is_file() or path.is_symlink():
            raise CandidateRunManifestError(f"Candidate run is missing {label}")

    expected_snapshot = canonical_json(snapshot)
    if snapshot_path.read_bytes() != expected_snapshot:
        raise CandidateRunManifestError(
            "saved execution snapshot bytes do not match the authorized snapshot"
        )

    metrics, _ = _load_canonical_json(metrics_path, "training metrics")
    _validate_training_metrics(snapshot, metrics, snapshot_sha)
    return snapshot_sha


def _candidate_file_rows(root: Path) -> list[dict]:
    files = directory_file_identities(root)
    rows = [row.__dict__ for row in files if row.path != "run-manifest.json"]
    if not rows:
        raise CandidateRunManifestError("Candidate run contains no evidence files")
    return rows


def _expected_candidate_run_manifest(snapshot: dict, root: Path) -> dict:
    snapshot_sha = _validate_candidate_evidence(snapshot, root)
    return {
        "schema_version": 1,
        "kind": "V3_CANDIDATE_RUN_EVIDENCE",
        "experiment_id": snapshot["experiment_id"],
        "execution_snapshot_sha256": snapshot_sha,
        "execution_core_sha256": execution_core_sha256(snapshot),
        "code_git_sha": snapshot["code"]["git_sha"],
        "dataset_sha256": snapshot["dataset"]["canonical_sha256"],
        "files": _candidate_file_rows(root),
        "candidate_created": True,
        "validation_opened": False,
        "historical_v2_opened": False,
        "promotion_authorized": False,
    }


def build_candidate_run_manifest(snapshot: dict, output_dir: Path) -> dict:
    """Inventory a completed run directory without mutating it."""
    root = Path(output_dir)
    manifest_path = root / "run-manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        raise CandidateRunManifestError("Candidate run manifest must not already exist")
    return _expected_candidate_run_manifest(snapshot, root)


def write_candidate_run_manifest(snapshot: dict, output_dir: Path) -> tuple[Path, str]:
    """Write the final run manifest exactly once and return path + content digest."""
    root = Path(output_dir)
    manifest = build_candidate_run_manifest(snapshot, root)
    payload = canonical_json(manifest)
    path = root / "run-manifest.json"
    try:
        with path.open("xb") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise CandidateRunManifestError("Candidate run manifest must be create-only") from exc
    return path, sha256_bytes(payload)


def verify_candidate_run_manifest(
    snapshot: dict,
    output_dir: Path,
    *,
    expected_manifest_sha256: str | None = None,
) -> dict:
    """Fail closed if a frozen Candidate run changed after its manifest was written."""
    root = Path(output_dir)
    path = root / "run-manifest.json"
    if not path.is_file() or path.is_symlink():
        raise CandidateRunManifestError("Candidate run manifest is missing or unsafe")

    manifest, payload = _load_canonical_json(path, "Candidate run manifest")
    observed_sha256 = sha256_bytes(payload)
    if expected_manifest_sha256 is not None:
        if (
            not isinstance(expected_manifest_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_manifest_sha256) is None
        ):
            raise CandidateRunManifestError("expected Candidate run manifest SHA-256 is invalid")
        if observed_sha256 != expected_manifest_sha256:
            raise CandidateRunManifestError("Candidate run manifest SHA-256 mismatch")

    expected = _expected_candidate_run_manifest(snapshot, root)
    if manifest != expected:
        raise CandidateRunManifestError(
            "Candidate run manifest does not match current evidence bytes"
        )
    return manifest
