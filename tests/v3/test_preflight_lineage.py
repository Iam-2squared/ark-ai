import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from ark.learning.dataset import digest
from ark.learning.execution import execution_core_sha256
from ark.learning.preflight import PreflightEvidence, build_preflight_report
from ark.learning.runtime_guard import RuntimeIdentity
from ark.learning.training_cli import _verify_preflight_report

TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def resolved_preflight_snapshot():
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
            "real_training_authorized": False,
        }
    )
    return value


def evidence():
    return PreflightEvidence(
        device="NVIDIA GPU",
        vram_gib=24.0,
        base_loaded=True,
        tokenizer_probe_sha256="c" * 64,
        forward_backward_ok=True,
        optimizer_step_ok=True,
        peak_vram_mib=12000.0,
        wall_seconds=12.5,
        runtime_error=None,
    )


def runtime_identity():
    return RuntimeIdentity(
        os_or_image_digest="image@sha256:abc",
        python="3.12.10",
        torch="2.6.0+cu124",
        transformers="4.51.0",
        peft="0.15.2",
        accelerate="1.6.0",
        cuda_runtime="12.4",
        device="NVIDIA GPU",
        vram_gib=24.0,
        driver="570.00",
    )


def test_authorization_and_preflight_hash_do_not_change_execution_core():
    preflight = resolved_preflight_snapshot()
    training = copy.deepcopy(preflight)
    training["authorization"]["real_training_authorized"] = True
    training["hardware"]["preflight_report_sha256"] = "9" * 64
    assert execution_core_sha256(preflight) == execution_core_sha256(training)


def test_training_accepts_only_preflight_from_same_execution_core(tmp_path):
    preflight = resolved_preflight_snapshot()
    payload = build_preflight_report(preflight, evidence(), runtime_identity())
    report = tmp_path / "preflight.json"
    report.write_bytes(payload)

    training = copy.deepcopy(preflight)
    training["authorization"]["real_training_authorized"] = True
    training["hardware"]["preflight_report_sha256"] = digest(payload)
    _verify_preflight_report(report, training)

    changed = copy.deepcopy(training)
    changed["dataset"]["canonical_sha256"] = "8" * 64
    with pytest.raises(RuntimeError, match="different execution core"):
        _verify_preflight_report(report, changed)


@pytest.mark.parametrize(
    "changes,match",
    [
        ({"vram_gib": float("nan")}, "finite positive preflight measurements"),
        ({"wall_seconds": True}, "finite positive preflight measurements"),
        ({"base_loaded": 1}, "preflight mechanics did not complete"),
        ({"tokenizer_probe_sha256": "z" * 64}, "tokenizer probe SHA-256 required"),
    ],
)
def test_preflight_evidence_rejects_noncanonical_values(changes, match):
    with pytest.raises(ValueError, match=match):
        replace(evidence(), **changes).validate()
