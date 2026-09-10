import json
from pathlib import Path

import pytest

from ark.learning.authorization import build_preflight_authorization_packet
from ark.learning.execution import ExecutionBlocked


TEMPLATE = Path("docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json")


def resolved_preflight_input_snapshot():
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    value["code"]["git_sha"] = "1" * 40
    value["code"]["manifest_sha256"] = "0" * 64
    value["base"]["revision"] = "2" * 40
    value["base"]["file_sha256_manifest"] = "a" * 64
    value["tokenizer"]["file_sha256_manifest"] = "b" * 64
    value["tokenizer"]["chat_template_probe_sha256"] = "c" * 64
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
            "torch": "pinned",
            "transformers": "pinned",
            "peft": "pinned",
            "accelerate": "pinned",
            "cuda_runtime": "pinned",
        }
    )
    value["hardware"].update(
        {
            "device": "proposed-gpu",
            "vram_gib": 24,
            "driver": "pinned-driver",
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


def test_packet_can_be_built_before_preflight_output_exists():
    packet = build_preflight_authorization_packet(resolved_preflight_input_snapshot())
    assert packet["request_scope"] == "EXTERNAL_COMPUTE_PLUS_NON_CANDIDATE_PREFLIGHT_ONLY"
    assert len(packet["execution_snapshot_sha256"]) == 64
    assert len(packet["execution_core_sha256"]) == 64
    assert packet["code_git_sha"] == "1" * 40
    assert packet["code_manifest_sha256"] == "0" * 64
    assert packet["preflight"]["candidate_created"] is False
    assert packet["preflight"]["historical_v2_opened"] is False
    assert packet["hard_stops_after_preflight"][
        "full_candidate_training_requires_new_explicit_authorization"
    ] is True
    assert len(packet["packet_sha256"]) == 64


def test_unresolved_snapshot_cannot_produce_authorization_packet():
    value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    with pytest.raises(ExecutionBlocked):
        build_preflight_authorization_packet(value)
