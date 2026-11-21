"""Run1020: V3 preflight rejects numeric subclasses before conversion callbacks.

Validation-only fixtures; no Candidate, model load, GPU, converter or training.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.learning.preflight as preflight
from ark.learning.preflight import PreflightEvidence
from ark.learning.runtime_guard import (
    RuntimeIdentity,
    RuntimeIdentityMismatch,
    verify_runtime_identity,
)


class FloatCarrier(float):
    def __float__(self):
        raise AssertionError("untrusted float subclass conversion must not run")


class IntCarrier(int):
    def __float__(self):
        raise AssertionError("untrusted int subclass conversion must not run")


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
            "device": "SYNTHETIC GPU",
            "vram_gib": 16.0,
            "driver": "fixture-driver",
        },
        "tokenizer": {"chat_template_probe_sha256": "c" * 64},
        "budget": {"wall_clock_timeout_minutes": 60},
    }


def _identity():
    return RuntimeIdentity(
        "fixture-image",
        "3.12.10",
        "fixture-torch",
        "fixture-transformers",
        "fixture-peft",
        "fixture-accelerate",
        "fixture-cuda",
        "SYNTHETIC GPU",
        16.0,
        "fixture-driver",
    )


def _evidence():
    return PreflightEvidence(
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


@pytest.mark.parametrize(
    "field",
    ("vram_gib", "peak_vram_mib", "peak_reserved_vram_mib", "wall_seconds"),
)
@pytest.mark.parametrize(
    "carrier",
    (FloatCarrier(16.0), IntCarrier(16)),
    ids=("float-subclass", "int-subclass"),
)
def test_preflight_evidence_rejects_numeric_subclass_before_float(
    field: str, carrier: object,
) -> None:
    evidence = replace(_evidence(), **{field: carrier})
    with pytest.raises(ValueError, match="finite positive preflight"):
        evidence.validate()


@pytest.mark.parametrize(
    "carrier",
    (FloatCarrier(16.0), IntCarrier(16)),
    ids=("float-subclass", "int-subclass"),
)
def test_runtime_identity_rejects_vram_subclass_before_float(
    carrier: object,
) -> None:
    identity = replace(_identity(), vram_gib=carrier)
    with pytest.raises(
        RuntimeIdentityMismatch,
        match="invalid measured GPU VRAM identity",
    ):
        identity.validate()


@pytest.mark.parametrize(
    ("section", "field", "error", "message"),
    (
        (
            "hardware",
            "vram_gib",
            RuntimeIdentityMismatch,
            "invalid frozen GPU VRAM identity",
        ),
        (
            "budget",
            "wall_clock_timeout_minutes",
            ValueError,
            "finite positive frozen preflight wall-clock budget",
        ),
    ),
)
@pytest.mark.parametrize(
    "carrier",
    (FloatCarrier(16.0), IntCarrier(16)),
    ids=("float-subclass", "int-subclass"),
)
def test_direct_measurement_binding_rejects_snapshot_numeric_subclass(
    section: str,
    field: str,
    error: type[Exception],
    message: str,
    carrier: object,
) -> None:
    snapshot = _snapshot()
    snapshot[section][field] = carrier
    with pytest.raises(error, match=message):
        preflight.verify_preflight_measurements(
            snapshot,
            _evidence(),
            _identity(),
        )


@pytest.mark.parametrize(
    "carrier",
    (FloatCarrier(0.05), IntCarrier(0)),
    ids=("float-subclass", "int-subclass"),
)
def test_runtime_vram_tolerance_rejects_subclass_before_float(
    carrier: object,
) -> None:
    with pytest.raises(ValueError, match="finite non-negative VRAM tolerance"):
        verify_runtime_identity(
            _snapshot(),
            _identity(),
            vram_tolerance_gib=carrier,
        )


def test_exact_builtin_measurements_remain_validation_only() -> None:
    snapshot = _snapshot()
    evidence = _evidence()
    identity = _identity()
    assert preflight.verify_preflight_measurements(
        snapshot, evidence, identity,
    ) is None
    assert snapshot["hardware"]["device"] == "SYNTHETIC GPU"
