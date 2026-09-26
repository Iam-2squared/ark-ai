"""Deterministic authorization packet generation for the pre-paid-compute STOP."""

from __future__ import annotations

import argparse
from pathlib import Path

from .execution import (
    canonical_json,
    execution_core_sha256,
    load_snapshot,
    sha256_bytes,
    validate_experiment_001,
)


def build_preflight_authorization_packet(snapshot: dict) -> dict:
    """Build a user-review packet without authorizing or starting external compute."""
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="none")
    auth = snapshot["authorization"]
    if any(
        auth[key]
        for key in (
            "external_compute_authorized",
            "preflight_authorized",
            "real_training_authorized",
        )
    ):
        raise ValueError("authorization packet must be generated from an unapproved snapshot")

    packet = {
        "schema_version": 1,
        "experiment_id": snapshot["experiment_id"],
        "request_scope": "EXTERNAL_COMPUTE_PLUS_NON_CANDIDATE_PREFLIGHT_ONLY",
        "execution_snapshot_sha256": snapshot_sha,
        "execution_core_sha256": execution_core_sha256(snapshot),
        "code_git_sha": snapshot["code"]["git_sha"],
        "code_manifest_sha256": snapshot["code"]["manifest_sha256"],
        "base": {
            "model_id": snapshot["base"]["model_id"],
            "revision": snapshot["base"]["revision"],
            "manifest_sha256": snapshot["base"]["file_sha256_manifest"],
        },
        "tokenizer": {
            "revision": snapshot["tokenizer"]["revision"],
            "manifest_sha256": snapshot["tokenizer"]["file_sha256_manifest"],
            "chat_template_probe_sha256": snapshot["tokenizer"]["chat_template_probe_sha256"],
        },
        "dataset": {
            "canonical_sha256": snapshot["dataset"]["canonical_sha256"],
            "provenance_manifest_sha256": snapshot["dataset"]["provenance_manifest_sha256"],
            "contamination_report_sha256": snapshot["dataset"]["contamination_report_sha256"],
            "train_count": 120,
            "validation_count": 30,
        },
        "method": dict(snapshot["method"]),
        "environment": dict(snapshot["environment"]),
        "proposed_hardware": {
            "device": snapshot["hardware"]["device"],
            "vram_gib": snapshot["hardware"]["vram_gib"],
            "driver": snapshot["hardware"]["driver"],
        },
        "budget": {
            "max_cost_jpy": snapshot["budget"]["max_cost_jpy"],
            "wall_clock_timeout_minutes": snapshot["budget"]["wall_clock_timeout_minutes"],
        },
        "export": dict(snapshot["export"]),
        "evaluation": dict(snapshot["evaluation"]),
        "privacy": dict(snapshot["privacy"]),
        "preflight": {
            "candidate_created": False,
            "validation_opened": False,
            "historical_v2_opened": False,
            "expected_outputs": [
                "base_load_success",
                "tokenizer_chat_template_probe_digest",
                "one_forward_backward_optimizer_step",
                "peak_vram_measurement",
                "wall_time",
                "dependency_hardware_manifest",
                "runtime_error_or_success",
            ],
        },
        "hard_stops_after_preflight": {
            "full_candidate_training_requires_new_explicit_authorization": True,
            "historical_v2_opening_requires_later_explicit_authorization": True,
            "promotion_requires_later_explicit_authorization": True,
            "main_merge_authorized": False,
        },
    }
    packet["packet_sha256"] = sha256_bytes(canonical_json(packet))
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build ARK V3 preflight authorization packet")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    output = Path(args.output)
    if output.exists() or output.is_symlink() or not output.parent.is_dir():
        raise ValueError("authorization packet output must be a new file")
    packet = build_preflight_authorization_packet(load_snapshot(args.snapshot))
    with output.open("xb") as handle:
        handle.write(canonical_json(packet))
    print(f"packet_sha256={packet['packet_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
