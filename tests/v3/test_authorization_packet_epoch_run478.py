"""No paid compute: V3 human-review packet snapshot-custody regressions."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import authorization as mod

_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _unapproved_snapshot():
    value = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    value["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    value["base"].update({
        "revision": "2" * 40, "file_sha256_manifest": "a" * 64,
    })
    value["tokenizer"].update({
        "file_sha256_manifest": "b" * 64,
        "chat_template_probe_sha256": "c" * 64,
    })
    value["dataset"].update({
        "canonical_sha256": "d" * 64,
        "provenance_manifest_sha256": "e" * 64,
        "contamination_report_sha256": "f" * 64,
    })
    value["environment"].update({
        "os_or_image_digest": "image@sha256:abc",
        "python": "3.12.10", "torch": "pinned",
        "transformers": "pinned", "peft": "pinned",
        "accelerate": "pinned", "cuda_runtime": "pinned",
    })
    value["hardware"].update({
        "device": "proposed-only", "vram_gib": 24, "driver": "pinned",
    })
    value["budget"].update({
        "max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60,
    })
    value["export"].update({
        "llama_cpp_revision": "3" * 40,
        "converter_identity": "4" * 64,
        "quantizer_identity": "5" * 64,
    })
    return value


def test_packet_is_deterministic_and_never_authorizes_compute():
    source = _unapproved_snapshot()
    first = mod.build_preflight_authorization_packet(source)
    assert first == mod.build_preflight_authorization_packet(source)
    assert first["preflight"]["candidate_created"] is False
    assert first["hard_stops_after_preflight"]["main_merge_authorized"] is False
    assert first["hard_stops_after_preflight"][
        "full_candidate_training_requires_new_explicit_authorization"
    ] is True
    for name in ("method", "environment", "export", "evaluation", "privacy"):
        assert first[name] == source[name]
        assert first[name] is not source[name]


def test_core_hash_callback_cannot_change_budget_after_validation(monkeypatch):
    source = _unapproved_snapshot()
    before = mod.execution_core_sha256

    def tamper(snapshot):
        digest = before(snapshot)
        source["budget"]["max_cost_jpy"] = 1
        return digest

    monkeypatch.setattr(mod, "execution_core_sha256", tamper)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_authorization_packet(source)


def test_core_hash_callback_cannot_swap_equal_value_field(monkeypatch):
    source = _unapproved_snapshot()
    old = source["environment"]["python"]
    replacement = bytes(old, "ascii").decode("ascii")
    assert replacement == old and replacement is not old
    before = mod.execution_core_sha256

    def tamper(snapshot):
        digest = before(snapshot)
        source["environment"]["python"] = replacement
        return digest

    monkeypatch.setattr(mod, "execution_core_sha256", tamper)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_authorization_packet(source)


def test_nested_copy_callback_cannot_retarget_export_identity(monkeypatch):
    source = _unapproved_snapshot()
    original = mod.deepcopy
    calls = []

    def tamper(value):
        result = original(value)
        calls.append(True)
        if len(calls) == 2:
            source["export"]["quantizer_identity"] = "9" * 64
        return result

    monkeypatch.setattr(mod, "deepcopy", tamper)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_authorization_packet(source)


def test_final_json_hash_callback_cannot_retarget_review_packet(monkeypatch):
    source = _unapproved_snapshot()
    original = mod.canonical_json

    def tamper(packet):
        encoded = original(packet)
        source["authorization"]["real_training_authorized"] = True
        return encoded

    monkeypatch.setattr(mod, "canonical_json", tamper)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_authorization_packet(source)


def test_subclass_mapping_cannot_supply_packet():
    class FauxDict(dict):
        pass

    with pytest.raises(ValueError, match="exact"):
        mod.build_preflight_authorization_packet(FauxDict(_unapproved_snapshot()))


def test_packet_serializer_cannot_retarget_review_scope_after_bytes(monkeypatch):
    source = _unapproved_snapshot()
    original = mod.canonical_json

    def corrupt_packet_after_encoding(value):
        encoded = original(value)
        if type(value) is dict and value.get("request_scope") == (
            "EXTERNAL_COMPUTE_PLUS_NON_CANDIDATE_PREFLIGHT_ONLY"
        ):
            value["request_scope"] = "UNAUTHORIZED_FULL_TRAINING"
        return encoded

    monkeypatch.setattr(mod, "canonical_json", corrupt_packet_after_encoding)
    with pytest.raises(ValueError, match="changed"):
        mod.build_preflight_authorization_packet(source)


def test_packet_digest_callback_cannot_rewrite_detached_method(monkeypatch):
    source = _unapproved_snapshot()
    captured = []
    original_copy = mod.deepcopy
    original_sha = mod.sha256_bytes

    def capture_copy(value):
        output = original_copy(value)
        captured.append(output)
        return output

    def tamper_after_hash(value):
        digest = original_sha(value)
        assert captured
        captured[0]["unexpected_runtime_permission"] = True
        return digest

    monkeypatch.setattr(mod, "deepcopy", capture_copy)
    monkeypatch.setattr(mod, "sha256_bytes", tamper_after_hash)
    with pytest.raises(ValueError, match="changed"):
        mod.build_preflight_authorization_packet(source)


def test_packet_digest_still_binds_unmodified_review_fields():
    packet = mod.build_preflight_authorization_packet(_unapproved_snapshot())
    digest = packet.pop("packet_sha256")
    assert digest == mod.sha256_bytes(mod.canonical_json(packet))
    assert packet["hard_stops_after_preflight"]["main_merge_authorized"] is False
