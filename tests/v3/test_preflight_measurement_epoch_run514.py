"""V3 non-Candidate measurement review is exact-type, epoch-bound and inert."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.learning.preflight as mod
from ark.learning.runtime_guard import RuntimeIdentity


def _snapshot():
    return {
        "environment": {
            "os_or_image_digest": "fixture-image",
            "python": "3.12.10",
            "torch": "fixture-torch",
            "transformers": "fixture-transformers",
            "peft": "fixture-peft",
            "accelerate": "fixture-accelerate",
            "cuda_runtime": "fixture-cuda",
        },
        "hardware": {
            "device": "SYNTHETIC GPU", "vram_gib": 16.0, "driver": "fixture-driver",
        },
        "tokenizer": {"chat_template_probe_sha256": "c" * 64},
        "budget": {"wall_clock_timeout_minutes": 60},
    }


def _identity():
    return RuntimeIdentity(
        "fixture-image", "3.12.10", "fixture-torch", "fixture-transformers",
        "fixture-peft", "fixture-accelerate", "fixture-cuda",
        "SYNTHETIC GPU", 16.0, "fixture-driver",
    )


def _evidence():
    return mod.PreflightEvidence(
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


def _verify(snapshot=None, evidence=None, actual=None):
    return mod.verify_preflight_measurements(
        _snapshot() if snapshot is None else snapshot,
        _evidence() if evidence is None else evidence,
        _identity() if actual is None else actual,
    )


def test_synthetic_measurement_binding_is_repeatable_without_gpu():
    data, evidence, identity = _snapshot(), _evidence(), _identity()
    assert _verify(data, evidence, identity) is None
    assert _verify(data, evidence, identity) is None
    assert data["hardware"]["device"] == "SYNTHETIC GPU"


def test_forged_evidence_subclass_cannot_bypass_mechanics_validation():
    class Forged(mod.PreflightEvidence):
        def validate(self):
            return None

    original = _evidence()
    forged = Forged(**{
        name: getattr(original, name)
        for name in mod.PreflightEvidence.__dataclass_fields__
    })
    with pytest.raises(ValueError, match="exact non-Candidate"):
        _verify(evidence=forged)


@pytest.mark.parametrize("bad", (object(), {}, 1, True))
def test_unrecognized_evidence_carrier_fails_closed(bad):
    with pytest.raises(ValueError, match="exact non-Candidate"):
        _verify(evidence=bad)


def test_evidence_validation_callback_cannot_change_a_field(monkeypatch):
    evidence = _evidence()
    original = mod.PreflightEvidence.validate

    def mutate(self):
        original(self)
        object.__setattr__(evidence, "wall_seconds", 11.0)

    monkeypatch.setattr(mod.PreflightEvidence, "validate", mutate)
    with pytest.raises(ValueError, match="measurement input epoch changed"):
        _verify(evidence=evidence)


def test_evidence_callback_cannot_swap_equal_value_snapshot_carrier(monkeypatch):
    snapshot = _snapshot()
    original = mod.PreflightEvidence.validate

    def mutate(self):
        original(self)
        text = snapshot["tokenizer"]["chat_template_probe_sha256"]
        replacement = (" " + text)[1:]
        assert replacement == text and replacement is not text
        snapshot["tokenizer"]["chat_template_probe_sha256"] = replacement

    monkeypatch.setattr(mod.PreflightEvidence, "validate", mutate)
    with pytest.raises(ValueError, match="snapshot changed"):
        _verify(snapshot=snapshot)


def test_runtime_validation_callback_cannot_rebind_evidence(monkeypatch):
    evidence = _evidence()
    original = RuntimeIdentity.validate

    def mutate(self):
        original(self)
        object.__setattr__(evidence, "peak_reserved_vram_mib", 5100.0)

    monkeypatch.setattr(RuntimeIdentity, "validate", mutate)
    with pytest.raises(ValueError, match="measurement input epoch changed"):
        _verify(evidence=evidence)


def test_runtime_check_callback_cannot_replace_identity_carrier(monkeypatch):
    identity = _identity()
    original = mod.verify_runtime_identity

    def mutate(snapshot, actual):
        original(snapshot, actual)
        old = identity.device
        replacement = (" " + old)[1:]
        assert replacement == old and replacement is not old
        object.__setattr__(identity, "device", replacement)

    monkeypatch.setattr(mod, "verify_runtime_identity", mutate)
    with pytest.raises(ValueError, match="measurement input epoch changed"):
        _verify(actual=identity)


@pytest.mark.parametrize("missing", ("tokenizer", "budget"))
def test_missing_direct_measurement_sections_are_explicit_denials(missing):
    snapshot = _snapshot()
    snapshot.pop(missing)
    with pytest.raises(ValueError, match="measurement bindings missing"):
        _verify(snapshot=snapshot)


@pytest.mark.parametrize("bad", (0, -1, True, "60", float("nan")))
def test_direct_frozen_wall_time_budget_requires_finite_positive_number(bad):
    snapshot = _snapshot()
    snapshot["budget"]["wall_clock_timeout_minutes"] = bad
    with pytest.raises(ValueError, match="preflight.*budget"):
        _verify(snapshot=snapshot)


def test_direct_measurement_mismatch_still_denied():
    evidence = replace(_evidence(), peak_reserved_vram_mib=17_000.0)
    with pytest.raises(ValueError, match="reserved VRAM exceeds"):
        _verify(evidence=evidence)


def test_direct_evidence_report_is_not_an_authorization():
    evidence = _evidence()
    snapshot = _snapshot()
    identity = _identity()
    assert mod.verify_preflight_measurements(snapshot, evidence, identity) is None
    assert "authorization" not in snapshot
    assert "candidate" not in repr(evidence).lower()
