import copy
import json
from pathlib import Path

import pytest

from ark.learning.execution import canonical_json, sha256_bytes, validate_experiment_001
from ark.learning.run_manifest import (
    CandidateRunManifestError,
    build_candidate_run_manifest,
    verify_candidate_run_manifest,
    write_candidate_run_manifest,
)

TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def resolved_training_snapshot():
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    value["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    value["base"].update({"revision": "2" * 40, "file_sha256_manifest": "a" * 64})
    value["tokenizer"].update(
        {
            "file_sha256_manifest": "b" * 64,
            "chat_template_probe_sha256": "c" * 64,
        }
    )
    value["dataset"].update(
        {
            "canonical_sha256": "d" * 64,
            "provenance_manifest_sha256": "e" * 64,
            "contamination_report_sha256": "f" * 64,
        }
    )
    value["environment"].update(
        {
            "os_or_image_digest": "image@sha256:abc",
            "python": "3.12.10",
            "torch": "2.6.0+cu124",
            "transformers": "4.51.0",
            "peft": "0.15.2",
            "accelerate": "1.6.0",
            "cuda_runtime": "12.4",
        }
    )
    value["hardware"].update(
        {
            "device": "NVIDIA GPU",
            "vram_gib": 24.0,
            "driver": "570.00",
            "preflight_report_sha256": "9" * 64,
        }
    )
    value["budget"].update({"max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60})
    value["export"].update(
        {
            "llama_cpp_revision": "3" * 40,
            "converter_identity": "4" * 64,
            "quantizer_identity": "5" * 64,
        }
    )
    value["authorization"].update(
        {
            "external_compute_authorized": True,
            "preflight_authorized": True,
            "real_training_authorized": True,
        }
    )
    validate_experiment_001(value, authorization_scope="training")
    return value


def write_completed_run(root: Path, snapshot: dict) -> None:
    (root / "adapter").mkdir(parents=True)
    (root / "adapter" / "adapter_config.json").write_text("{}", encoding="utf-8")
    (root / "adapter" / "adapter_model.safetensors").write_bytes(b"adapter")
    (root / "tokenizer").mkdir()
    (root / "tokenizer" / "tokenizer.json").write_text("{}", encoding="utf-8")
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="training")
    metrics = {
        "execution_snapshot_sha256": snapshot_sha,
        "dataset_sha256": snapshot["dataset"]["canonical_sha256"],
    }
    (root / "training-metrics.json").write_bytes(canonical_json(metrics))
    (root / "execution-snapshot.json").write_bytes(canonical_json(snapshot))


def test_candidate_run_manifest_inventory_is_sorted_and_hashable(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)

    manifest = build_candidate_run_manifest(snapshot, root)
    paths = [row["path"] for row in manifest["files"]]
    assert paths == sorted(paths)
    assert "adapter/adapter_model.safetensors" in paths
    assert "run-manifest.json" not in paths
    assert manifest["candidate_created"] is True
    assert manifest["historical_v2_opened"] is False

    path, digest = write_candidate_run_manifest(snapshot, root)
    assert path == root / "run-manifest.json"
    assert digest == sha256_bytes(path.read_bytes())
    assert verify_candidate_run_manifest(
        snapshot,
        root,
        expected_manifest_sha256=digest,
    ) == manifest
    with pytest.raises(CandidateRunManifestError, match="must not already exist"):
        write_candidate_run_manifest(snapshot, root)


def test_candidate_run_manifest_rejects_tampered_saved_snapshot(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    changed = copy.deepcopy(snapshot)
    changed["dataset"]["canonical_sha256"] = "8" * 64
    (root / "execution-snapshot.json").write_bytes(canonical_json(changed))

    with pytest.raises(CandidateRunManifestError, match="authorized snapshot"):
        build_candidate_run_manifest(snapshot, root)


def test_candidate_run_manifest_rejects_metrics_from_other_dataset(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    metrics = json.loads((root / "training-metrics.json").read_text(encoding="utf-8"))
    metrics["dataset_sha256"] = "8" * 64
    (root / "training-metrics.json").write_bytes(canonical_json(metrics))

    with pytest.raises(CandidateRunManifestError, match="dataset identity mismatch"):
        build_candidate_run_manifest(snapshot, root)


def test_candidate_run_verifier_detects_post_freeze_file_tampering(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    _, digest = write_candidate_run_manifest(snapshot, root)

    (root / "adapter" / "adapter_model.safetensors").write_bytes(b"tampered")
    with pytest.raises(CandidateRunManifestError, match="current evidence bytes"):
        verify_candidate_run_manifest(snapshot, root, expected_manifest_sha256=digest)


def test_candidate_run_verifier_rejects_noncanonical_manifest_json(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    path, _ = write_candidate_run_manifest(snapshot, root)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    with pytest.raises(CandidateRunManifestError, match="valid canonical JSON"):
        verify_candidate_run_manifest(snapshot, root)


def test_candidate_run_verifier_requires_exact_manifest_digest(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    write_candidate_run_manifest(snapshot, root)

    with pytest.raises(CandidateRunManifestError, match="SHA-256 mismatch"):
        verify_candidate_run_manifest(
            snapshot,
            root,
            expected_manifest_sha256="0" * 64,
        )
