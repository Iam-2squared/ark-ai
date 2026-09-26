"""Official V3 experiment-001 execution entry point.

The CLI is fail-closed: all local evidence and authorization fields are checked before
heavy training dependencies can be imported. It never provisions or purchases compute.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from .dataset import digest
from .execution import execution_core_sha256, load_snapshot, validate_experiment_001
from .hf_lora import HfLoRAFullRun, HfLoRAPreflightBackend
from .identity import build_code_tree_identity
from .preflight import PreflightEvidence, build_preflight_report, run_authorized_preflight
from .runtime_guard import RuntimeIdentity, collect_runtime_identity, verify_runtime_identity


def _reject_nonstandard_json_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON constant is forbidden: {token}")


def _verify_file(path: Path, expected_sha256: str, label: str) -> bytes:
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(f"{label} is not a file")
    payload = path.read_bytes()
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
    report_path = Path(args.report)
    if report_path.exists() or report_path.is_symlink() or not report_path.parent.is_dir():
        raise RuntimeError("preflight report path must be a new file under an existing directory")
    backend = HfLoRAPreflightBackend(
        base_dir=args.base_dir,
        dataset_path=args.dataset,
        chat_template_probe=args.probe,
    )
    evidence = run_authorized_preflight(snapshot, backend)
    payload = build_preflight_report(snapshot, evidence, runtime_identity)
    with report_path.open("xb") as handle:
        handle.write(payload)
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
