"""Offline-only CLI for experiment-001 dataset review planning and evidence freeze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audit import ReviewPair, build_human_review_queue
from .dataset import ContaminationGuard, LearningCandidate, build_dataset, canonical, digest
from .freeze import AuditDecision, freeze_experiment_001_dataset, required_review_keys


def _load_json_list(path: Path, label: str) -> list[dict]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
        raise ValueError(f"{label} must be a JSON array of objects")
    return value


def _candidates(path: Path) -> list[LearningCandidate]:
    return [LearningCandidate(**row) for row in _load_json_list(path, "candidates")]


def _pairs(path: Path) -> list[ReviewPair]:
    return [ReviewPair(**row) for row in _load_json_list(path, "flags")]


def _decisions(path: Path) -> list[AuditDecision]:
    return [AuditDecision(**row) for row in _load_json_list(path, "decisions")]


def _accepted(dataset_payload: bytes) -> list[LearningCandidate]:
    rows = json.loads(dataset_payload)["examples"]
    return [LearningCandidate(**row) for row in rows]


def make_review_queue(candidates_path: Path, flags_path: Path) -> bytes:
    items = _candidates(candidates_path)
    dataset = build_dataset(items, ContaminationGuard.frozen_v2())
    if dataset.summary["train_examples"] != 120 or dataset.summary["validation_examples"] != 30:
        raise RuntimeError(
            "review queue requires exactly 120 accepted train / 30 validation examples"
        )
    if dataset.summary["rejected"] or dataset.summary["duplicates"]:
        raise RuntimeError("resolve deterministic dataset rejections/duplicates before human audit")
    queue = build_human_review_queue(_accepted(dataset.payload), _pairs(flags_path))
    result = {
        "schema_version": 1,
        "experiment_id": "v3-format-compliance-001",
        "dataset_sha256": dataset.sha256,
        "queue": queue,
        "required_review_keys": list(required_review_keys(queue)),
    }
    return canonical(result)


def freeze_to_directory(
    candidates_path: Path,
    flags_path: Path,
    decisions_path: Path,
    output_dir: Path,
) -> dict:
    output_dir = Path(output_dir)
    if output_dir.exists() or output_dir.is_symlink() or not output_dir.parent.is_dir():
        raise ValueError("output directory must be new and have an existing parent")
    evidence = freeze_experiment_001_dataset(
        _candidates(candidates_path),
        ContaminationGuard.frozen_v2(),
        _pairs(flags_path),
        _decisions(decisions_path),
    )
    output_dir.mkdir()
    files = {
        "dataset.json": evidence.dataset.payload,
        "provenance.json": evidence.provenance_payload,
        "contamination.json": evidence.contamination_payload,
    }
    for name, payload in files.items():
        with (output_dir / name).open("xb") as handle:
            handle.write(payload)
    manifest = {
        "schema_version": 1,
        "experiment_id": "v3-format-compliance-001",
        "dataset_sha256": evidence.dataset.sha256,
        "provenance_sha256": evidence.provenance_sha256,
        "contamination_sha256": evidence.contamination_sha256,
        "review_queue_sha256": evidence.review_queue_sha256,
        "files": {
            name: {"sha256": digest(payload), "bytes": len(payload)}
            for name, payload in files.items()
        },
    }
    manifest_payload = canonical(manifest)
    with (output_dir / "manifest.json").open("xb") as handle:
        handle.write(manifest_payload)
    return {**manifest, "manifest_sha256": digest(manifest_payload)}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARK V3 offline dataset evidence tooling")
    sub = parser.add_subparsers(dest="command", required=True)

    queue = sub.add_parser("queue", help="build deterministic human-review queue")
    queue.add_argument("--candidates", type=Path, required=True)
    queue.add_argument("--flags", type=Path, required=True)
    queue.add_argument("--output", type=Path, required=True)

    freeze = sub.add_parser("freeze", help="freeze reviewed dataset evidence")
    freeze.add_argument("--candidates", type=Path, required=True)
    freeze.add_argument("--flags", type=Path, required=True)
    freeze.add_argument("--decisions", type=Path, required=True)
    freeze.add_argument("--output-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "queue":
        output = Path(args.output)
        if output.exists() or output.is_symlink() or not output.parent.is_dir():
            raise ValueError("queue output must be a new file under an existing directory")
        payload = make_review_queue(args.candidates, args.flags)
        with output.open("xb") as handle:
            handle.write(payload)
        print(f"review_queue_sha256={digest(payload)}")
        return 0

    manifest = freeze_to_directory(
        args.candidates,
        args.flags,
        args.decisions,
        args.output_dir,
    )
    print(f"dataset_sha256={manifest['dataset_sha256']}")
    print(f"provenance_sha256={manifest['provenance_sha256']}")
    print(f"contamination_sha256={manifest['contamination_sha256']}")
    print(f"manifest_sha256={manifest['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
