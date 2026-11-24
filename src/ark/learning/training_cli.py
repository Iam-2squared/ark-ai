"""Official V3 experiment-001 execution entry point.

The CLI is fail-closed: all local evidence and authorization fields are checked before
heavy training dependencies can be imported. It never provisions or purchases compute.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
from pathlib import Path

from .dataset import digest
from .execution import execution_core_sha256, load_snapshot, validate_experiment_001
from .hf_lora import HfLoRAFullRun, HfLoRAPreflightBackend
from .identity import build_code_tree_identity
from .preflight import (
    PreflightEvidence,
    build_preflight_report,
    run_authorized_preflight,
    verify_preflight_measurements,
)
from .runtime_guard import RuntimeIdentity, collect_runtime_identity, verify_runtime_identity

# Reuse existing repository evidence-ingress ceilings rather than inventing
# larger limits: dataset JSON ingress is capped at 64 MiB, while canonical
# run-manifest JSON is capped at 1 MiB. The preflight report is a fixed,
# small-schema JSON artifact; provenance and contamination retain the dataset
# ingress ceiling because their row counts are fixed by experiment-001.
_MAX_PROVENANCE_MANIFEST_BYTES = 64 * 1024 * 1024
_MAX_CONTAMINATION_REPORT_BYTES = 64 * 1024 * 1024
_MAX_PREFLIGHT_REPORT_BYTES = 1_048_576
_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_regular_evidence_file(info: os.stat_result) -> bool:
    mode = info.st_mode
    return type(mode) is int and stat.S_ISREG(mode)


def _is_evidence_reparse_point(info: os.stat_result) -> bool:
    mode = info.st_mode
    attributes = getattr(info, "st_file_attributes", 0)
    if type(mode) is not int or type(attributes) is not int:
        raise RuntimeError("evidence file metadata is malformed")
    return stat.S_ISLNK(mode) or bool(attributes & _REPARSE_POINT_ATTRIBUTE)


def _has_evidence_reparse_ancestor(path: Path) -> bool:
    for parent in path.parents:
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if _is_evidence_reparse_point(info):
            return True
    return False


def _evidence_file_epoch(info: os.stat_result) -> tuple[int, ...]:
    # Windows path-stat and descriptor-stat expose different ctime semantics;
    # compare ctime only on POSIX, matching the existing V3 packet reader.
    changed = info.st_ctime_ns if os.name == "posix" else 0
    values = (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        changed,
    )
    if any(type(value) is not int for value in values):
        raise RuntimeError("evidence file metadata is malformed")
    return values


def _read_bounded_evidence(path: Path, *, max_bytes: int, label: str) -> bytes:
    """Read one bounded regular evidence file and recheck its descriptor epoch.

    This is local file-custody hardening, not an atomic directory-fd traversal,
    authenticated provenance, immutable storage, or protection from a hostile
    concurrent filesystem writer.
    """
    if type(max_bytes) is not int or max_bytes <= 0:
        raise RuntimeError("evidence byte budget must be a positive exact integer")
    path = Path(path)
    if ".." in path.parts or len(str(path)) > 4096:
        raise RuntimeError(f"{label} path is not an accepted local file path")

    try:
        before = path.lstat()
        before_size = before.st_size
        before_links = before.st_nlink
        if (
            not _is_regular_evidence_file(before)
            or _is_evidence_reparse_point(before)
            or type(before_size) is not int
            or not 1 <= before_size <= max_bytes
            or type(before_links) is not int
            or before_links != 1
            or _has_evidence_reparse_ancestor(path)
        ):
            raise RuntimeError(f"{label} path or byte budget denied")

        flags = (
            os.O_RDONLY
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        descriptor = os.open(path, flags)
        try:
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                opened = os.fstat(handle.fileno())
                opened_links = opened.st_nlink
                if (
                    not _is_regular_evidence_file(opened)
                    or _is_evidence_reparse_point(opened)
                    or type(opened_links) is not int
                    or opened_links != 1
                    or before.st_ino == 0
                    or opened.st_ino == 0
                    or not os.path.samestat(before, opened)
                    or _evidence_file_epoch(opened) != _evidence_file_epoch(before)
                ):
                    raise RuntimeError(f"{label} changed before its bytes were read")
                payload = handle.read(max_bytes + 1)
                after_handle = os.fstat(handle.fileno())
        finally:
            if descriptor >= 0:
                os.close(descriptor)

        after = path.lstat()
        after_links = after.st_nlink
        after_handle_links = after_handle.st_nlink
        if (
            not _is_regular_evidence_file(after)
            or _is_evidence_reparse_point(after)
            or type(after_links) is not int
            or after_links != 1
            or not _is_regular_evidence_file(after_handle)
            or _is_evidence_reparse_point(after_handle)
            or type(after_handle_links) is not int
            or after_handle_links != 1
            or _evidence_file_epoch(after) != _evidence_file_epoch(before)
            or _evidence_file_epoch(after_handle) != _evidence_file_epoch(before)
            or _has_evidence_reparse_ancestor(path)
            or len(payload) != before_size
            or len(payload) > max_bytes
        ):
            raise RuntimeError(f"{label} changed during its bounded read")
        return payload
    except OSError as exc:
        raise RuntimeError(f"{label} cannot be read safely") from exc


_EVIDENCE_FILE_BUDGETS = {
    "provenance manifest": _MAX_PROVENANCE_MANIFEST_BYTES,
    "contamination report": _MAX_CONTAMINATION_REPORT_BYTES,
    "preflight report": _MAX_PREFLIGHT_REPORT_BYTES,
}


def _reject_nonstandard_json_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON constant is forbidden: {token}")


def _verify_file(path: Path, expected_sha256: str, label: str) -> bytes:
    max_bytes = _EVIDENCE_FILE_BUDGETS.get(label)
    if max_bytes is None:
        raise RuntimeError("unsupported V3 evidence file label")
    payload = _read_bounded_evidence(path, max_bytes=max_bytes, label=label)
    if digest(payload) != expected_sha256:
        raise RuntimeError(f"{label} bytes do not match frozen snapshot SHA-256")
    return payload


def _verify_git_checkout(code_root: Path, expected_sha: str) -> None:
    """Verify the actual local checkout instead of trusting only a CLI-supplied SHA."""
    root = Path(code_root)
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("runtime code root must be an existing non-symlink directory")
    if re.fullmatch(r"[0-9a-f]{40}", expected_sha) is None:
        raise RuntimeError("exact frozen code git SHA required")

    def git_output(*args: str) -> str:
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), *args],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise RuntimeError("unable to verify local git repository state") from exc
        return completed.stdout.strip()

    observed_head = git_output("rev-parse", "--verify", "HEAD")
    if observed_head != expected_sha:
        raise RuntimeError(
            "runtime git HEAD does not match frozen code SHA: "
            f"expected {expected_sha}, observed {observed_head or '<empty>'}"
        )
    if git_output("status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("clean repository state required before V3 compute")


def _verify_common_evidence(
    snapshot: dict,
    *,
    provenance: Path,
    contamination: Path,
    code_root: Path,
    running_code_sha: str,
) -> None:
    _verify_git_checkout(code_root, snapshot["code"]["git_sha"])
    if running_code_sha != snapshot["code"]["git_sha"]:
        raise RuntimeError("running code SHA does not match frozen execution snapshot")
    code_identity = build_code_tree_identity(code_root)
    if code_identity["manifest_sha256"] != snapshot["code"]["manifest_sha256"]:
        raise RuntimeError("runtime source bytes do not match frozen code manifest")
    _verify_file(
        provenance,
        snapshot["dataset"]["provenance_manifest_sha256"],
        "provenance manifest",
    )
    _verify_file(
        contamination,
        snapshot["dataset"]["contamination_report_sha256"],
        "contamination report",
    )


def _verify_actual_runtime(snapshot: dict) -> RuntimeIdentity:
    """Bind the authorized snapshot to the actual already-provisioned GPU runtime."""
    try:
        import torch
    except ImportError as exc:  # pragma: no cover - real stack intentionally absent in CI
        raise RuntimeError("pinned V3 torch runtime is not installed") from exc
    actual = collect_runtime_identity(torch)
    verify_runtime_identity(snapshot, actual)
    return actual


def _verify_preflight_report(path: Path, snapshot: dict) -> None:
    payload = _verify_file(
        path,
        snapshot["hardware"]["preflight_report_sha256"],
        "preflight report",
    )
    try:
        report = json.loads(payload, parse_constant=_reject_nonstandard_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError("preflight report is not valid canonical JSON") from exc
    if not isinstance(report, dict):
        raise RuntimeError("preflight report must be a JSON object")
    expected_core = execution_core_sha256(snapshot)
    if report.get("execution_core_sha256") != expected_core:
        raise RuntimeError("preflight report belongs to a different execution core")
    if report.get("kind") != "NON_CANDIDATE_PREFLIGHT" or report.get("schema_version") != 1:
        raise RuntimeError("unexpected preflight report schema/kind")
    for field in (
        "candidate_created",
        "validation_opened",
        "historical_v2_opened",
        "full_training_authorized",
    ):
        if report.get(field) is not False:
            raise RuntimeError(f"preflight report violates hard stop: {field}")

    runtime_identity = report.get("runtime_identity")
    if not isinstance(runtime_identity, dict):
        raise RuntimeError("preflight runtime identity evidence missing")
    try:
        recorded_runtime = RuntimeIdentity(**runtime_identity)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("preflight runtime identity evidence is invalid") from exc
    verify_runtime_identity(snapshot, recorded_runtime)

    evidence = report.get("evidence")
    if not isinstance(evidence, dict):
        raise RuntimeError("preflight report evidence missing")
    try:
        recorded_evidence = PreflightEvidence(**evidence)
        recorded_evidence.validate()
    except (TypeError, ValueError) as exc:
        raise RuntimeError("preflight report evidence is invalid") from exc
    if (
        recorded_evidence.tokenizer_probe_sha256
        != snapshot["tokenizer"]["chat_template_probe_sha256"]
    ):
        raise RuntimeError("preflight tokenizer probe does not match frozen snapshot")
    if recorded_evidence.device != snapshot["hardware"]["device"]:
        raise RuntimeError("preflight GPU device does not match frozen snapshot")
    expected_vram = float(snapshot["hardware"]["vram_gib"])
    if abs(float(recorded_evidence.vram_gib) - expected_vram) > 0.05:
        raise RuntimeError("preflight GPU VRAM does not match frozen snapshot")
    # Revalidate the saved report during the training gate, not only when it
    # was first constructed. A hash-matching report with inconsistent
    # measured evidence must never count as successful mechanics.
    try:
        verify_preflight_measurements(snapshot, recorded_evidence, recorded_runtime)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("preflight report measurements are inconsistent") from exc



def _validate_new_preflight_report_path(path: Path) -> Path:
    """Validate a new local report destination before any preflight backend work."""
    if type(path) is not type(Path(".")):
        raise RuntimeError("preflight report path must be an exact native Path")
    try:
        raw = os.fspath(path)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("preflight report path is invalid") from exc
    if (
        type(raw) is not str
        or not raw
        or "\\0" in raw
        or ".." in path.parts
        or len(raw) > 4096
    ):
        raise RuntimeError("preflight report path is not an accepted local path")

    source = path.absolute()
    try:
        parent = source.parent.lstat()
        if (
            type(parent.st_mode) is not int
            or not stat.S_ISDIR(parent.st_mode)
            or _is_evidence_reparse_point(parent)
            or _has_evidence_reparse_ancestor(source)
        ):
            raise RuntimeError(
                "preflight report parent must be an existing non-reparse directory"
            )
        try:
            source.lstat()
        except FileNotFoundError:
            pass
        else:
            raise RuntimeError("preflight report path must be a new file")
    except OSError as exc:
        raise RuntimeError("preflight report path custody cannot be verified") from exc
    return source


def _write_new_preflight_report(path: Path, payload: bytes) -> None:
    """Create one bounded report without following a leaf or reparse-point parent."""
    if type(payload) is not bytes or not 1 <= len(payload) <= _MAX_PREFLIGHT_REPORT_BYTES:
        raise RuntimeError("preflight report payload is outside its byte budget")
    source = _validate_new_preflight_report_path(path)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    descriptor = -1
    try:
        descriptor = os.open(source, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            opened = os.fstat(handle.fileno())
            observed = source.lstat()
            opened_links = opened.st_nlink
            if (
                not _is_regular_evidence_file(opened)
                or _is_evidence_reparse_point(opened)
                or type(opened_links) is not int
                or opened_links != 1
                or opened.st_ino == 0
                or not os.path.samestat(observed, opened)
                or _evidence_file_epoch(observed) != _evidence_file_epoch(opened)
                or _has_evidence_reparse_ancestor(source)
            ):
                raise RuntimeError("preflight report destination changed before write")
            written = handle.write(payload)
            handle.flush()
            if written != len(payload):
                raise RuntimeError("preflight report write was incomplete")
            after_handle = os.fstat(handle.fileno())
        after = source.lstat()
        after_links = after.st_nlink
        handle_links = after_handle.st_nlink
        if (
            not _is_regular_evidence_file(after)
            or _is_evidence_reparse_point(after)
            or type(after_links) is not int
            or after_links != 1
            or not _is_regular_evidence_file(after_handle)
            or _is_evidence_reparse_point(after_handle)
            or type(handle_links) is not int
            or handle_links != 1
            or not os.path.samestat(after, after_handle)
            or _evidence_file_epoch(after) != _evidence_file_epoch(after_handle)
            or _has_evidence_reparse_ancestor(source)
            or after.st_size != len(payload)
        ):
            raise RuntimeError("preflight report destination changed during write")
    except OSError as exc:
        raise RuntimeError("preflight report cannot be created safely") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def run_preflight(args: argparse.Namespace) -> dict:
    snapshot = load_snapshot(args.snapshot)
    # Authorization and every exact identity must close before importing torch/GPU runtime.
    validate_experiment_001(snapshot, authorization_scope="preflight")
    _verify_common_evidence(
        snapshot,
        provenance=args.provenance,
        contamination=args.contamination,
        code_root=args.code_root,
        running_code_sha=args.code_sha,
    )
    runtime_identity = _verify_actual_runtime(snapshot)
    report_path = _validate_new_preflight_report_path(args.report)
    backend = HfLoRAPreflightBackend(
        base_dir=args.base_dir,
        dataset_path=args.dataset,
        chat_template_probe=args.probe,
    )
    evidence = run_authorized_preflight(snapshot, backend)
    payload = build_preflight_report(snapshot, evidence, runtime_identity)
    _write_new_preflight_report(report_path, payload)
    return {
        "kind": "NON_CANDIDATE_PREFLIGHT",
        "report_sha256": digest(payload),
        "execution_core_sha256": execution_core_sha256(snapshot),
        "candidate_created": False,
        "historical_v2_opened": False,
    }


def run_training(args: argparse.Namespace) -> dict:
    snapshot = load_snapshot(args.snapshot)
    # Full-training authorization and prior preflight evidence must close before torch import.
    validate_experiment_001(snapshot, authorization_scope="training")
    _verify_common_evidence(
        snapshot,
        provenance=args.provenance,
        contamination=args.contamination,
        code_root=args.code_root,
        running_code_sha=args.code_sha,
    )
    _verify_preflight_report(args.preflight_report, snapshot)
    _verify_actual_runtime(snapshot)
    runner = HfLoRAFullRun(
        base_dir=args.base_dir,
        dataset_path=args.dataset,
        chat_template_probe=args.probe,
        output_dir=args.output_dir,
    )
    return runner.run(snapshot)


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--base-dir", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--contamination", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--code-sha", required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARK V3 authorized experiment-001 runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    preflight = sub.add_parser("preflight", help="run authorized non-Candidate mechanics probe")
    _common(preflight)
    preflight.add_argument("--report", type=Path, required=True)

    train = sub.add_parser("train", help="run the single authorized full Candidate")
    _common(train)
    train.add_argument("--preflight-report", type=Path, required=True)
    train.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    result = run_preflight(args) if args.command == "preflight" else run_training(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
