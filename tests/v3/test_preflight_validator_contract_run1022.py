"""Run1022: preflight evidence validation cannot be bypassed by class mutation."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.learning.preflight as preflight
from ark.learning.preflight import PreflightEvidence, verify_preflight_measurements
from ark.learning.runtime_guard import RuntimeIdentity


def _inputs() -> tuple[dict, PreflightEvidence, RuntimeIdentity]:
    environment = {
        "os_or_image_digest": "local:fixture",
        "python": "3.12",
        "torch": "torch-fixture",
        "transformers": "transformers-fixture",
        "peft": "peft-fixture",
        "accelerate": "accelerate-fixture",
        "cuda_runtime": "cuda-fixture",
    }
    snapshot = {
        "environment": dict(environment),
        "hardware": {
            "device": "SYNTHETIC GPU",
            "driver": "driver-fixture",
            "vram_gib": 16.0,
        },
        "tokenizer": {"chat_template_probe_sha256": "c" * 64},
        "budget": {"wall_clock_timeout_minutes": 1},
    }
    identity = RuntimeIdentity(
        "local:fixture", "3.12", "torch-fixture", "transformers-fixture",
        "peft-fixture", "accelerate-fixture", "cuda-fixture",
        "SYNTHETIC GPU", 16.0, "driver-fixture",
    )
    evidence = PreflightEvidence(
        device="SYNTHETIC GPU",
        vram_gib=16.0,
        base_loaded=True,
        tokenizer_probe_sha256="c" * 64,
        forward_backward_ok=True,
        optimizer_step_ok=True,
        peak_vram_mib=4000.0,
        peak_reserved_vram_mib=5000.0,
        wall_seconds=10.0,
    )
    return snapshot, evidence, identity


def test_replaced_public_validator_cannot_approve_invalid_evidence(monkeypatch):
    snapshot, evidence, identity = _inputs()
    calls: list[object] = []

    def no_op(self: object) -> None:
        calls.append(self)

    monkeypatch.setattr(PreflightEvidence, "validate", no_op)
    invalid = replace(evidence, base_loaded=False)
    with pytest.raises(ValueError, match="preflight mechanics did not complete"):
        verify_preflight_measurements(snapshot, invalid, identity)
    assert calls == [invalid]


def test_replaced_field_descriptor_is_rejected_before_getter(monkeypatch):
    snapshot, evidence, identity = _inputs()
    calls: list[object] = []

    def forbidden(_self: object) -> str:
        calls.append(_self)
        raise AssertionError("untrusted preflight field getter must not run")

    monkeypatch.setattr(
        PreflightEvidence, "device", property(forbidden), raising=False,
    )
    with pytest.raises(ValueError, match="preflight evidence contract changed"):
        verify_preflight_measurements(snapshot, evidence, identity)
    assert calls == []


def test_rebound_field_inventory_is_rejected_before_field_reads(monkeypatch):
    snapshot, evidence, identity = _inputs()
    monkeypatch.setattr(preflight, "_EVIDENCE_FIELDS", ("device",))
    with pytest.raises(ValueError, match="preflight evidence contract changed"):
        verify_preflight_measurements(snapshot, evidence, identity)


def test_mutated_dataclass_field_map_is_rejected(monkeypatch):
    snapshot, evidence, identity = _inputs()
    fields = PreflightEvidence.__dataclass_fields__
    monkeypatch.setitem(fields, "device", fields["vram_gib"])
    with pytest.raises(ValueError, match="preflight evidence contract changed"):
        verify_preflight_measurements(snapshot, evidence, identity)


def test_instance_validator_shadow_is_rejected_before_dispatch(monkeypatch):
    snapshot, evidence, identity = _inputs()
    calls: list[object] = []

    def no_op() -> None:
        calls.append("shadow")

    object.__setattr__(evidence, "validate", no_op)
    with pytest.raises(ValueError, match="instance validator shadowed"):
        verify_preflight_measurements(snapshot, evidence, identity)
    assert calls == []


def test_exact_synthetic_measurement_evidence_remains_valid():
    snapshot, evidence, identity = _inputs()
    assert verify_preflight_measurements(snapshot, evidence, identity) is None
