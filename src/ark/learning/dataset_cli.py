"""Offline-only CLI for experiment-001 dataset review planning and evidence freeze."""

from __future__ import annotations

import argparse
from pathlib import Path

from .audit import ReviewPair, build_human_review_queue
from .dataset import (
    ContaminationGuard,
    LearningCandidate,
    build_dataset,
    canonical,
    digest,
    loads_unique_json,
)
from .freeze import (
    AuditDecision,
    build_review_queue_artifact,
    freeze_experiment_001_dataset,
)

# Operational CLI ingress limits only. These do not alter the frozen dataset schema,
# example counts, review policy, canonical serialization, or training/evaluation gates.
MAX_DATASET_INPUT_BYTES = 64 * 1024 * 1024
MAX_JSON_NESTING = 64


def _check_json_nesting(payload: bytes, label: str) -> None:
    """Bound structural nesting without counting brackets inside JSON strings."""
    depth = 0
    in_string = False
    escaped = False
    for byte in payload:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_JSON_NESTING:
                raise ValueError(
                    f"{label} JSON nesting exceeds {MAX_JSON_NESTING} levels"
                )
        elif byte in (0x5D, 0x7D):
            depth -= 1


def _load_json_file(path: Path, label: str) -> object:
    """Read a local JSON input with fixed byte/depth budgets before parsing."""
    with Path(path).open("rb") as handle:
        payload = handle.read(MAX_DATASET_INPUT_BYTES + 1)
    if len(payload) > MAX_DATASET_INPUT_BYTES:
        raise ValueError(
            f"{label} JSON input exceeds {MAX_DATASET_INPUT_BYTES} bytes"
        )
    _check_json_nesting(payload, label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} JSON input must be UTF-8") from exc
    try:
        return loads_unique_json(text)
    except RecursionError as exc:
        raise ValueError(f"{label} JSON nesting exceeds parser capacity") from exc


def _load_json_list(path: Path, label: str) -> list[dict]:
    value = _load_json_file(path, label)
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
    rows = loads_unique_json(dataset_payload)["examples"]
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
    return build_review_queue_artifact(dataset.sha256, queue)


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
        "review_queue.json": evidence.review_queue_payload,
        "decisions.json": evidence.decisions_payload,
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
        "review_queue_sha256": evidence.review_queue_sha256,
        "decisions_sha256": evidence.decisions_sha256,
        "contamination_sha256": evidence.contamination_sha256,
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
    print(f"review_queue_sha256={manifest['review_queue_sha256']}")
    print(f"decisions_sha256={manifest['decisions_sha256']}")
    print(f"contamination_sha256={manifest['contamination_sha256']}")
    print(f"manifest_sha256={manifest['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
