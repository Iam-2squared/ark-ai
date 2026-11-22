"""Create-only evidence manifest for the single authorized V3 Candidate run.

This module never starts training, opens evaluation data, or performs network access.
It only inventories bytes that already exist in a newly-created Candidate run directory.
"""

from __future__ import annotations

import json
import math
import os
import re
import stat
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


_MAX_CANONICAL_JSON_BYTES = 1_048_576
_MAX_CANONICAL_JSON_DEPTH = 128
_MAX_MANIFEST_DIRECTORY_ENTRIES = 10_000
_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_REPARSE_POINT_ATTRIBUTE = _REPARSE_POINT_ATTRIBUTE
_ORIGINAL_STAT = stat
_ORIGINAL_S_ISDIR = stat.S_ISDIR
_ORIGINAL_S_ISREG = stat.S_ISREG
_ORIGINAL_S_ISLNK = stat.S_ISLNK
_ORIGINAL_FSTAT = os.fstat
_ORIGINAL_DIRECTORY_FILE_IDENTITIES = directory_file_identities


def _require_original_stat_policy() -> None:
    if (
        stat is not _ORIGINAL_STAT
        or _ORIGINAL_STAT.S_ISDIR is not _ORIGINAL_S_ISDIR
        or _ORIGINAL_STAT.S_ISREG is not _ORIGINAL_S_ISREG
        or _ORIGINAL_STAT.S_ISLNK is not _ORIGINAL_S_ISLNK
        or os.fstat is not _ORIGINAL_FSTAT
        or directory_file_identities is not _ORIGINAL_DIRECTORY_FILE_IDENTITIES
        or type(_REPARSE_POINT_ATTRIBUTE) is not int
        or _REPARSE_POINT_ATTRIBUTE != _ORIGINAL_REPARSE_POINT_ATTRIBUTE
    ):
        raise CandidateRunManifestError("Candidate run path stat policy changed")


def _is_directory(info: object) -> bool:
    _require_original_stat_policy()
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise CandidateRunManifestError("Candidate run directory mode is malformed")
    return _ORIGINAL_S_ISDIR(mode)


def _is_regular_file(info: object) -> bool:
    _require_original_stat_policy()
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise CandidateRunManifestError("Candidate run file mode is malformed")
    return _ORIGINAL_S_ISREG(mode)


def _is_reparse_point(info: object) -> bool:
    _require_original_stat_policy()
    attributes = getattr(info, "st_file_attributes", 0)
    _require_original_stat_policy()
    if type(attributes) is not int:
        raise CandidateRunManifestError("Candidate run reparse metadata is malformed")
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise CandidateRunManifestError("Candidate run file mode is malformed")
    return _ORIGINAL_S_ISLNK(mode) or bool(
        attributes & _REPARSE_POINT_ATTRIBUTE
    )


def _path_lstat(path: Path, label: str):
    _require_original_stat_policy()
    info = path.lstat()
    _require_original_stat_policy()
    return info


def _file_identity(info: object) -> tuple[int, int, int]:
    values = (info.st_dev, info.st_ino, info.st_size, info.st_nlink)
    if any(type(value) is not int or value < 0 for value in values):
        raise CandidateRunManifestError("Candidate run file identity is malformed")
    if values[3] != 1:
        raise CandidateRunManifestError("Candidate run file must not be hard-linked")
    return values[:3]


def _require_nonreparse_ancestors(path: Path, label: str) -> None:
    for parent in path.parents:
        info = _path_lstat(parent, label)
        if not _is_directory(info) or _is_reparse_point(info):
            raise CandidateRunManifestError(
                f"{label} path has a symlink or reparse-point ancestor"
            )


def _read_bounded_file(path: Path, label: str, limit: int) -> bytes:
    _require_original_stat_policy()
    if type(limit) is not int or not 0 <= limit <= _MAX_CANONICAL_JSON_BYTES:
        raise CandidateRunManifestError(f"{label} read budget is invalid")
    try:
        _require_nonreparse_ancestors(path, label)
        before = _path_lstat(path, label)
        if not _is_regular_file(before) or _is_reparse_point(before):
            raise CandidateRunManifestError(f"{label} must be a regular non-reparse file")
        before_identity = _file_identity(before)
        with path.open("rb") as handle:
            # Path.open can be reentrant; check the classification policy
            # before fstat or reading any private evidence bytes.
            _require_original_stat_policy()
            opened = _ORIGINAL_FSTAT(handle.fileno())
            if (
                not _is_regular_file(opened)
                or _is_reparse_point(opened)
                or _file_identity(opened) != before_identity
            ):
                raise CandidateRunManifestError(f"{label} changed before read")
            payload = handle.read(limit + 1)
            _require_original_stat_policy()
        after = _path_lstat(path, label)
    except CandidateRunManifestError:
        raise
    except OSError as exc:
        raise CandidateRunManifestError(f"{label} cannot be read") from exc
    if (
        not _is_regular_file(after)
        or _is_reparse_point(after)
        or _file_identity(after) != before_identity
        or len(payload) > limit
    ):
        raise CandidateRunManifestError(f"{label} changed or exceeded its byte budget")
    return payload


def _reject_excessive_json_nesting(payload: bytes) -> None:
    """Refuse deep containers independently of platform JSON recursion limits.

    Only brackets outside JSON strings count. The parser still validates syntax,
    including escapes, after this bounded linear preflight.
    """
    depth = 0
    in_string = False
    escaped = False
    for byte in payload:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:  # Backslash
                escaped = True
            elif byte == 0x22:  # Quote
                in_string = False
        elif byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):  # Opening object or array
            depth += 1
            if depth > _MAX_CANONICAL_JSON_DEPTH:
                raise CandidateRunManifestError(
                    "evidence is not valid canonical JSON: nesting budget exceeded"
                )
        elif byte in (0x7D, 0x5D):  # Closing object or array
            depth -= 1


def _reject_nonstandard_json_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON constant is forbidden: {token}")


def _require_nonempty_directory(root: Path, relative: str) -> None:
    path = root / relative
    _require_nonreparse_ancestors(path, relative)
    info = _path_lstat(path, relative)
    if not _is_directory(info) or _is_reparse_point(info):
        raise CandidateRunManifestError(
            f"Candidate run requires non-reparse directory: {relative}"
        )
    found_file = False
    visited = 0
    try:
        for child in path.rglob("*"):
            visited += 1
            if visited > _MAX_MANIFEST_DIRECTORY_ENTRIES:
                raise CandidateRunManifestError(
                    f"Candidate run directory exceeds entry budget: {relative}"
                )
            child_info = _path_lstat(child, relative)
            if _is_reparse_point(child_info):
                raise CandidateRunManifestError(
                    f"Candidate run directory contains a reparse point: {relative}"
                )
            if _is_regular_file(child_info):
                found_file = True
            elif not _is_directory(child_info):
                raise CandidateRunManifestError(
                    f"Candidate run directory contains an unsupported entry: {relative}"
                )
    except OSError as exc:
        raise CandidateRunManifestError(
            f"Candidate run directory cannot be inspected: {relative}"
        ) from exc
    _require_original_stat_policy()
    if not found_file:
        raise CandidateRunManifestError(f"Candidate run directory is empty: {relative}")


def _load_canonical_json(path: Path, label: str) -> tuple[dict, bytes]:
    # A forged or unexpectedly huge evidence file must never be read without
    # a byte limit before canonical JSON validation. This is local-only.
    payload = _read_bounded_file(path, label, _MAX_CANONICAL_JSON_BYTES)
    if len(payload) > _MAX_CANONICAL_JSON_BYTES:
        raise CandidateRunManifestError(f"{label} exceeds canonical JSON byte budget")
    _reject_excessive_json_nesting(payload)
    try:
        parsed = json.loads(payload, parse_constant=_reject_nonstandard_json_constant)
        # A lexically valid JSON exponent may decode to infinity even when
        # NaN/Infinity tokens are forbidden. Canonical re-serialization and
        # hostile nesting must fail with this domain's error, not leak raw
        # RecursionError/ValueError into the evidence decision path.
        if type(parsed) is not dict or canonical_json(parsed) != payload:
            raise CandidateRunManifestError(f"{label} is not valid canonical JSON")
    except (
        UnicodeDecodeError, json.JSONDecodeError, ValueError,
        RecursionError, OverflowError, TypeError,
    ) as exc:
        raise CandidateRunManifestError(f"{label} is not valid canonical JSON") from exc
    return parsed, payload


def _require_expected_snapshot_bytes(path: Path, expected: bytes) -> None:
    """Compare saved snapshot bytes without unbounded reads of untrusted files.

    This is a local size guard, not a file-descriptor seal or a guarantee
    against a concurrently hostile filesystem writer.
    """
    if type(expected) is not bytes or len(expected) > _MAX_CANONICAL_JSON_BYTES:
        raise CandidateRunManifestError("authorized snapshot exceeds canonical JSON byte budget")
    observed = _read_bounded_file(
        path, "saved execution snapshot", len(expected),
    )
    if observed != expected:
        raise CandidateRunManifestError(
            "saved execution snapshot bytes do not match the authorized snapshot"
        )


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
    if type(value) not in (int, float):
        raise CandidateRunManifestError(f"training metrics {field} must be numeric")
    try:
        measured = float(value)
    except (OverflowError, ValueError) as exc:
        raise CandidateRunManifestError(
            f"training metrics {field} must be finite numeric"
        ) from exc
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
    _require_original_stat_policy()
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="training")
    root_info = _path_lstat(root, "Candidate run root")
    if not _is_directory(root_info) or _is_reparse_point(root_info):
        raise CandidateRunManifestError(
            "Candidate run root must be an existing non-reparse directory"
        )

    _require_nonempty_directory(root, "adapter")
    _require_nonempty_directory(root, "tokenizer")

    metrics_path = root / "training-metrics.json"
    snapshot_path = root / "execution-snapshot.json"
    for path, label in (
        (metrics_path, "training metrics"),
        (snapshot_path, "execution snapshot"),
    ):
        info = _path_lstat(path, label)
        if not _is_regular_file(info) or _is_reparse_point(info):
            raise CandidateRunManifestError(f"Candidate run is missing or unsafe: {label}")

    expected_snapshot = canonical_json(snapshot)
    _require_expected_snapshot_bytes(snapshot_path, expected_snapshot)

    metrics, _ = _load_canonical_json(metrics_path, "training metrics")
    _validate_training_metrics(snapshot, metrics, snapshot_sha)
    return snapshot_sha


def _candidate_file_rows(root: Path) -> list[dict]:
    _require_original_stat_policy()
    files = _ORIGINAL_DIRECTORY_FILE_IDENTITIES(root)
    _require_original_stat_policy()
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
    _require_original_stat_policy()
    root = Path(output_dir)
    _require_original_stat_policy()
    manifest_path = root / "run-manifest.json"
    try:
        _path_lstat(manifest_path, "Candidate run manifest")
    except FileNotFoundError:
        pass
    else:
        raise CandidateRunManifestError("Candidate run manifest must not already exist")
    return _expected_candidate_run_manifest(snapshot, root)


def write_candidate_run_manifest(snapshot: dict, output_dir: Path) -> tuple[Path, str]:
    """Write the final run manifest exactly once and return path + content digest."""
    _require_original_stat_policy()
    root = Path(output_dir)
    _require_original_stat_policy()
    manifest = build_candidate_run_manifest(snapshot, root)
    payload = canonical_json(manifest)
    _require_original_stat_policy()
    path = root / "run-manifest.json"
    try:
        with path.open("xb") as handle:
            _require_original_stat_policy()
            opened = _ORIGINAL_FSTAT(handle.fileno())
            if not _is_regular_file(opened) or _is_reparse_point(opened):
                raise CandidateRunManifestError("Candidate run manifest output is unsafe")
            written = handle.write(payload)
            _require_original_stat_policy()
            if type(written) is not int or written != len(payload):
                raise CandidateRunManifestError("Candidate run manifest write was incomplete")
    except FileExistsError as exc:
        raise CandidateRunManifestError("Candidate run manifest must be create-only") from exc
    saved = _read_bounded_file(path, "Candidate run manifest", _MAX_CANONICAL_JSON_BYTES)
    if saved != payload:
        raise CandidateRunManifestError("Candidate run manifest bytes changed after write")
    return path, sha256_bytes(payload)


def verify_candidate_run_manifest(
    snapshot: dict,
    output_dir: Path,
    *,
    expected_manifest_sha256: str | None = None,
) -> dict:
    """Fail closed if a frozen Candidate run changed after its manifest was written."""
    _require_original_stat_policy()
    root = Path(output_dir)
    _require_original_stat_policy()
    path = root / "run-manifest.json"
    info = _path_lstat(path, "Candidate run manifest")
    if not _is_regular_file(info) or _is_reparse_point(info):
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
