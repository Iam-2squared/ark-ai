"""Official V3 experiment-001 execution entry point.

The CLI is fail-closed: all local evidence and authorization fields are checked before
heavy training dependencies can be imported. It never provisions or purchases compute.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dataset import digest
from .execution import load_snapshot
from .hf_lora import HfLoRAFullRun, HfLoRAPreflightBackend
from .identity import build_code_tree_identity
from .preflight import build_preflight_report, run_authorized_preflight


def _verify_file(path: Path, expected_sha256: str, label: str) -> None:
    path = Path(path)
    if not path.is_file() or digest(path.read_bytes()) != expected_sha256:
        raise RuntimeError(f"{label} bytes do not match frozen snapshot SHA-256")


def _verify_common_evidence(
    snapshot: dict,
    *,
    provenance: Path,
    contamination: Path,
    code_root: Path,
    running_code_sha: str,
) -> None:
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


def run_preflight(args: argparse.Namespace) -> dict:
    snapshot = load_snapshot(args.snapshot)
    _verify_common_evidence(
        snapshot,
        provenance=args.provenance,
        contamination=args.contamination,
        code_root=args.code_root,
        running_code_sha=args.code_sha,
    )
    report_path = Path(args.report)
    if report_path.exists() or report_path.is_symlink() or not report_path.parent.is_dir():
        raise RuntimeError("preflight report path must be a new file under an existing directory")
    backend = HfLoRAPreflightBackend(
        base_dir=args.base_dir,
        dataset_path=args.dataset,
        chat_template_probe=args.probe,
    )
    evidence = run_authorized_preflight(snapshot, backend)
    payload = build_preflight_report(snapshot, evidence)
    with report_path.open("xb") as handle:
        handle.write(payload)
    return {
        "kind": "NON_CANDIDATE_PREFLIGHT",
        "report_sha256": digest(payload),
        "candidate_created": False,
        "historical_v2_opened": False,
    }


def run_training(args: argparse.Namespace) -> dict:
    snapshot = load_snapshot(args.snapshot)
    _verify_common_evidence(
        snapshot,
        provenance=args.provenance,
        contamination=args.contamination,
        code_root=args.code_root,
        running_code_sha=args.code_sha,
    )
    _verify_file(
        args.preflight_report,
        snapshot["hardware"]["preflight_report_sha256"],
        "preflight report",
    )
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
