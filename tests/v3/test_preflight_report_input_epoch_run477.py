"""Offline V3 non-Candidate preflight report input-epoch integrity.

No GPU, torch, model loading, cloud provider or Candidate is used.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ark.learning import preflight as mod
from ark.learning.runtime_guard import RuntimeIdentity


_TEMPLATE = Path(__file__).resolve().parents[2] / (
    "docs/v3/EXPERIMENT_001_EXECUTION_SNAPSHOT.template.json"
)


def _snapshot():
    value = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    value["code"].update({"git_sha": "1" * 40, "manifest_sha256": "0" * 64})
    value["base"].update({"revision": "2" * 40, "file_sha256_manifest": "a" * 64})
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
        "python": "3.12.10",
        "torch": "2.6.0+cu124",
        "transformers": "4.51.0",
        "peft": "0.15.2",
        "accelerate": "1.6.0",
        "cuda_runtime": "12.4",
    })
    value["hardware"].update({
        "device": "NVIDIA GPU", "vram_gib": 24.0, "driver": "570.00",
    })
    value["budget"].update({
        "max_cost_jpy": 1000, "wall_clock_timeout_minutes": 60,
    })
    value["export"].update({
        "llama_cpp_revision": "3" * 40,
        "converter_identity": "4" * 64,
        "quantizer_identity": "5" * 64,
    })
    value["authorization"].update({
        "external_compute_authorized": True,
        "preflight_authorized": True,
        "real_training_authorized": False,
    })
    return value


def _evidence():
    return mod.PreflightEvidence(
        device="NVIDIA GPU",
        vram_gib=24.0,
        base_loaded=True,
        tokenizer_probe_sha256="c" * 64,
        forward_backward_ok=True,
        optimizer_step_ok=True,
        peak_vram_mib=12000.0,
        peak_reserved_vram_mib=13000.0,
        wall_seconds=12.5,
    )


def _identity():
    return RuntimeIdentity(
        "image@sha256:abc", "3.12.10", "2.6.0+cu124", "4.51.0",
        "0.15.2", "1.6.0", "12.4", "NVIDIA GPU", 24.0, "570.00",
    )


def test_unchanged_preflight_report_is_deterministic_and_inert():
    snapshot, evidence, actual = _snapshot(), _evidence(), _identity()
    first = mod.build_preflight_report(snapshot, evidence, actual)
    assert first == mod.build_preflight_report(snapshot, evidence, actual)
    data = json.loads(first)
    assert data["candidate_created"] is False
    assert data["full_training_authorized"] is False


@pytest.mark.parametrize("field", (
    "real_training_authorized", "v2_opening_authorized",
    "promotion_authorized",
))
def test_evidence_callback_cannot_change_authorization_snapshot(
    monkeypatch, field,
):
    snapshot = _snapshot()
    evidence = _evidence()
    original = mod.PreflightEvidence.validate

    def changed(self):
        original(self)
        snapshot["authorization"][field] = True

    monkeypatch.setattr(mod.PreflightEvidence, "validate", changed)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_report(snapshot, evidence, _identity())


def test_equal_value_snapshot_carrier_swap_is_detected(monkeypatch):
    snapshot = _snapshot()
    old = snapshot["environment"]["python"]
    same = bytes(old, "ascii").decode("ascii")
    assert same == old and same is not old
    original = mod.PreflightEvidence.validate

    def changed(self):
        original(self)
        snapshot["environment"]["python"] = same

    monkeypatch.setattr(mod.PreflightEvidence, "validate", changed)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_report(snapshot, _evidence(), _identity())


def test_runtime_validation_cannot_rebind_preflight_evidence(monkeypatch):
    evidence = _evidence()
    original = RuntimeIdentity.validate

    def changed(self):
        original(self)
        object.__setattr__(evidence, "wall_seconds", 13.5)

    monkeypatch.setattr(RuntimeIdentity, "validate", changed)
    with pytest.raises(ValueError, match="result input epoch"):
        mod.build_preflight_report(_snapshot(), evidence, _identity())


def test_execution_core_hash_callback_cannot_rebind_runtime_identity(monkeypatch):
    actual = _identity()
    original = mod.execution_core_sha256

    def changed(snapshot):
        result = original(snapshot)
        old = actual.device
        replacement = bytes(old, "ascii").decode("ascii")
        assert replacement == old and replacement is not old
        object.__setattr__(actual, "device", replacement)
        return result

    monkeypatch.setattr(mod, "execution_core_sha256", changed)
    with pytest.raises(ValueError, match="result input epoch"):
        mod.build_preflight_report(_snapshot(), _evidence(), actual)


def test_asdict_callback_cannot_rebind_evidence_after_validation(monkeypatch):
    evidence = _evidence()
    original = mod.asdict
    calls = 0

    def changed(obj):
        nonlocal calls
        calls += 1
        result = original(obj)
        if calls == 1:
            object.__setattr__(evidence, "peak_vram_mib", 12001.0)
        return result

    monkeypatch.setattr(mod, "asdict", changed)
    with pytest.raises(ValueError, match="result input epoch"):
        mod.build_preflight_report(_snapshot(), evidence, _identity())


def test_last_json_encoding_callback_cannot_retarget_budget(monkeypatch):
    snapshot = _snapshot()
    original = mod.canonical_json

    def changed(value):
        result = original(value)
        snapshot["budget"]["max_cost_jpy"] = 1
        return result

    monkeypatch.setattr(mod, "canonical_json", changed)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod.build_preflight_report(snapshot, _evidence(), _identity())


def test_forged_preflight_evidence_subclass_cannot_supply_report():
    class MisleadingEvidence(mod.PreflightEvidence):
        def validate(self):
            return None

    original = _evidence()
    forged = MisleadingEvidence(**{
        name: getattr(original, name)
        for name in mod.PreflightEvidence.__dataclass_fields__
    })
    with pytest.raises(ValueError, match="exact preflight report"):
        mod.build_preflight_report(_snapshot(), forged, _identity())
