import copy
import json
from pathlib import Path

import pytest

from ark.learning.execution import ExecutionBlocked, load_snapshot, validate_experiment_001

TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def snapshot():
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def resolved_snapshot(*, preflight_measured=True):
    value = copy.deepcopy(snapshot())
    value["code"]["git_sha"] = "1" * 40
    value["code"]["manifest_sha256"] = "0" * 64
    value["base"]["revision"] = "2" * 40
    value["base"]["file_sha256_manifest"] = "a" * 64
    value["tokenizer"]["file_sha256_manifest"] = "b" * 64
    value["tokenizer"]["chat_template_probe_sha256"] = "c" * 64
    value["dataset"]["canonical_sha256"] = "d" * 64
    value["dataset"]["provenance_manifest_sha256"] = "e" * 64
    value["dataset"]["contamination_report_sha256"] = "f" * 64
    value["environment"].update(
        {
            "os_or_image_digest": "linux-image@sha256:abc",
            "python": "3.12.10",
            "torch": "2.x-pinned",
            "transformers": "pinned",
            "peft": "pinned",
            "accelerate": "pinned",
            "cuda_runtime": "pinned",
        }
    )
    value["hardware"].update(
        {
            "device": "approved-gpu",
            "vram_gib": 24,
            "driver": "pinned-driver",
            "preflight_report_sha256": "1" * 64 if preflight_measured else "UNRESOLVED",
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
    return value


def test_template_is_intentionally_blocked():
    with pytest.raises(ExecutionBlocked, match="unresolved execution identities"):
        validate_experiment_001(snapshot())


def test_unknown_top_level_snapshot_section_is_rejected():
    value = resolved_snapshot()
    value["future_override"] = {"allow": True}
    with pytest.raises(ExecutionBlocked, match="unknown sections: future_override"):
        validate_experiment_001(value)


def test_contract_dataset_size_cannot_drift():
    value = snapshot()
    value["dataset"]["train_count"] = 50
    with pytest.raises(ExecutionBlocked, match="120 train / 30 validation"):
        validate_experiment_001(value)


def test_lora_precommit_cannot_drift():
    value = snapshot()
    value["method"]["rank"] = 16
    with pytest.raises(ExecutionBlocked, match="method.rank"):
        validate_experiment_001(value)


def test_v2_opening_budget_cannot_drift():
    value = snapshot()
    value["evaluation"]["v2_candidate_runs"] = 1
    with pytest.raises(ExecutionBlocked, match="2 Current . 2 Candidate"):
        validate_experiment_001(value)


def test_v2_opening_must_remain_explicitly_authorized():
    value = resolved_snapshot()
    value["evaluation"]["v2_opening_requires_explicit_authorization"] = False
    with pytest.raises(ExecutionBlocked, match="explicit authorization"):
        validate_experiment_001(value)


def test_privacy_cannot_be_relaxed():
    value = snapshot()
    value["privacy"]["personal_memory_allowed"] = True
    with pytest.raises(ExecutionBlocked, match="privacy policy"):
        validate_experiment_001(value)


def test_snapshot_loader_requires_object(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        load_snapshot(path)


def test_exact_hash_shapes_are_required():
    value = resolved_snapshot()
    value["dataset"]["canonical_sha256"] = "frozen"
    with pytest.raises(ExecutionBlocked, match="dataset.canonical_sha256"):
        validate_experiment_001(value)


def test_preflight_report_is_output_not_preflight_input():
    value = resolved_snapshot(preflight_measured=False)
    digest = validate_experiment_001(value)
    assert len(digest) == 64

    value["authorization"]["external_compute_authorized"] = True
    value["authorization"]["preflight_authorized"] = True
    digest = validate_experiment_001(value, authorization_scope="preflight")
    assert len(digest) == 64

    value["authorization"]["real_training_authorized"] = True
    with pytest.raises(ExecutionBlocked, match="hardware.preflight_report_sha256"):
        validate_experiment_001(value, authorization_scope="training")


def test_identity_closure_is_separate_from_authorization():
    value = resolved_snapshot()
    digest = validate_experiment_001(value)
    assert len(digest) == 64

    with pytest.raises(ExecutionBlocked, match="preflight authorization"):
        validate_experiment_001(value, authorization_scope="preflight")

    value["authorization"]["external_compute_authorized"] = True
    value["authorization"]["preflight_authorized"] = True
    digest = validate_experiment_001(value, authorization_scope="preflight")
    assert len(digest) == 64

    with pytest.raises(ExecutionBlocked, match="real-training authorization"):
        validate_experiment_001(value, authorization_scope="training")

    value["authorization"]["real_training_authorized"] = True
    digest = validate_experiment_001(value, authorization_scope="training")
    assert len(digest) == 64


def test_preflight_scope_cannot_imply_full_training():
    value = resolved_snapshot()
    value["authorization"].update(
        {
            "external_compute_authorized": True,
            "preflight_authorized": True,
            "real_training_authorized": True,
        }
    )
    with pytest.raises(ExecutionBlocked, match="must not imply full training"):
        validate_experiment_001(value, authorization_scope="preflight")


def test_v2_and_promotion_cannot_be_pre_authorized():
    value = resolved_snapshot()
    value["authorization"]["v2_opening_authorized"] = True
    with pytest.raises(ExecutionBlocked, match="may not pre-authorize"):
        validate_experiment_001(value)
