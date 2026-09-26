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


def training_metrics(snapshot: dict) -> dict:
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="training")
    return {
        "schema_version": 1,
        "experiment_id": snapshot["experiment_id"],
        "execution_snapshot_sha256": snapshot_sha,
        "dataset_sha256": snapshot["dataset"]["canonical_sha256"],
        "optimizer_steps": 15,
        "microbatches": 120,
        "mean_training_loss": 1.25,
        "peak_vram_mib": 12000.0,
        "peak_reserved_vram_mib": 13000.0,
        "wall_seconds": 120.0,
        "trainable_parameters": 1024,
        "method": dict(snapshot["method"]),
    }


def write_completed_run(root: Path, snapshot: dict) -> None:
    (root / "adapter").mkdir(parents=True)
    (root / "adapter" / "adapter_config.json").write_text("{}", encoding="utf-8")
    (root / "adapter" / "adapter_model.safetensors").write_bytes(b"adapter")
    (root / "tokenizer").mkdir()
    (root / "tokenizer" / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "training-metrics.json").write_bytes(canonical_json(training_metrics(snapshot)))
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
    metrics = training_metrics(snapshot)
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


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("optimizer_steps", True, "positive integer"),
        ("microbatches", 119, "frozen value 120"),
        ("wall_seconds", 0.0, "finite positive"),
        ("trainable_parameters", 0, "positive integer"),
    ],
)
def test_candidate_run_manifest_rejects_invalid_training_metric_types(
    tmp_path,
    field,
    value,
    match,
):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    metrics = training_metrics(snapshot)
    metrics[field] = value
    (root / "training-metrics.json").write_bytes(canonical_json(metrics))

    with pytest.raises(CandidateRunManifestError, match=match):
        build_candidate_run_manifest(snapshot, root)


def test_candidate_run_manifest_rejects_training_method_drift(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    metrics = training_metrics(snapshot)
    metrics["method"]["rank"] = 16
    (root / "training-metrics.json").write_bytes(canonical_json(metrics))

    with pytest.raises(CandidateRunManifestError, match="frozen recipe"):
        build_candidate_run_manifest(snapshot, root)


def test_candidate_run_manifest_rejects_extra_training_metric_fields(tmp_path):
    snapshot = resolved_training_snapshot()
    root = tmp_path / "candidate"
    write_completed_run(root, snapshot)
    metrics = training_metrics(snapshot)
    metrics["posthoc_note"] = "unexpected"
    (root / "training-metrics.json").write_bytes(canonical_json(metrics))

    with pytest.raises(CandidateRunManifestError, match="schema mismatch"):
        build_candidate_run_manifest(snapshot, root)
