"""Create-only evidence manifest for the single authorized V3 Candidate run.

This module never starts training, opens evaluation data, or performs network access.
It only inventories bytes that already exist in a newly-created Candidate run directory.
"""

from __future__ import annotations

import json
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


def _require_nonempty_directory(root: Path, relative: str) -> None:
    path = root / relative
    if not path.is_dir() or path.is_symlink():
        raise CandidateRunManifestError(
            f"Candidate run requires non-symlink directory: {relative}"
        )
    if not any(child.is_file() for child in path.rglob("*")):
        raise CandidateRunManifestError(f"Candidate run directory is empty: {relative}")


def build_candidate_run_manifest(snapshot: dict, output_dir: Path) -> dict:
    """Inventory a completed run directory without mutating it."""
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="training")
    root = Path(output_dir)
    if not root.is_dir() or root.is_symlink():
        raise CandidateRunManifestError(
            "Candidate run root must be an existing non-symlink directory"
        )

    manifest_path = root / "run-manifest.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        raise CandidateRunManifestError("Candidate run manifest must not already exist")

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

    try:
        metrics = json.loads(metrics_path.read_bytes())
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise CandidateRunManifestError("training metrics are not valid JSON") from exc
    if not isinstance(metrics, dict):
        raise CandidateRunManifestError("training metrics must be a JSON object")
    if metrics.get("execution_snapshot_sha256") != snapshot_sha:
        raise CandidateRunManifestError(
            "training metrics do not match the authorized execution snapshot"
        )
    if metrics.get("dataset_sha256") != snapshot["dataset"]["canonical_sha256"]:
        raise CandidateRunManifestError("training metrics dataset identity mismatch")

    files = directory_file_identities(root)
    file_rows = [row.__dict__ for row in files]
    if any(row["path"] == "run-manifest.json" for row in file_rows):
        raise CandidateRunManifestError("run manifest must not self-reference")

    return {
        "schema_version": 1,
        "kind": "V3_CANDIDATE_RUN_EVIDENCE",
        "experiment_id": snapshot["experiment_id"],
        "execution_snapshot_sha256": snapshot_sha,
        "execution_core_sha256": execution_core_sha256(snapshot),
        "code_git_sha": snapshot["code"]["git_sha"],
        "dataset_sha256": snapshot["dataset"]["canonical_sha256"],
        "files": file_rows,
        "candidate_created": True,
        "validation_opened": False,
        "historical_v2_opened": False,
        "promotion_authorized": False,
    }


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
