"""Run1019: offline V3 preflight evidence must cross-bind to one frozen snapshot."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.learning.preflight as preflight
from ark.learning.runtime_guard import RuntimeIdentity, RuntimeIdentityMismatch


def _snapshot() -> dict:
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


def _identity() -> RuntimeIdentity:
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


def _evidence() -> preflight.PreflightEvidence:
    return preflight.PreflightEvidence(
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
    ("evidence", "message"),
    [
        (replace(_evidence(), device="OTHER GPU"), "device"),
        (replace(_evidence(), vram_gib=15.0), "VRAM"),
        (replace(_evidence(), tokenizer_probe_sha256="d" * 64), "tokenizer"),
        (replace(_evidence(), peak_vram_mib=6000.0), "allocated VRAM"),
        (replace(_evidence(), peak_reserved_vram_mib=17_000.0), "reserved VRAM"),
        (replace(_evidence(), wall_seconds=3601.0), "wall time"),
    ],
)
def test_evidence_must_match_measured_runtime_and_frozen_snapshot(
    evidence: preflight.PreflightEvidence,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        preflight.verify_preflight_measurements(
            _snapshot(),
            evidence,
            _identity(),
        )


@pytest.mark.parametrize(
    "field",
    ("vram_gib", "peak_vram_mib", "peak_reserved_vram_mib", "wall_seconds"),
)
@pytest.mark.parametrize("bad", (True, float("nan"), float("inf"), 0.0, -1.0))
def test_evidence_measurements_reject_bool_nonfinite_and_nonpositive_values(
    field: str,
    bad: object,
) -> None:
    evidence = replace(_evidence(), **{field: bad})
    with pytest.raises(ValueError, match="finite positive"):
        evidence.validate()


@pytest.mark.parametrize("bad", (True, float("nan"), float("inf"), 0.0, -1.0))
def test_measured_runtime_vram_rejects_bool_nonfinite_and_nonpositive_values(
    bad: object,
) -> None:
    actual = replace(_identity(), vram_gib=bad)
    with pytest.raises(RuntimeIdentityMismatch, match="VRAM"):
        preflight.verify_preflight_measurements(
            _snapshot(),
            _evidence(),
            actual,
        )


@pytest.mark.parametrize("bad", (True, float("nan"), float("inf"), 0.0, -1.0))
def test_frozen_snapshot_vram_rejects_bool_nonfinite_and_nonpositive_values(
    bad: object,
) -> None:
    snapshot = _snapshot()
    snapshot["hardware"]["vram_gib"] = bad
    with pytest.raises(RuntimeIdentityMismatch, match="VRAM"):
        preflight.verify_preflight_measurements(
            snapshot,
            _evidence(),
            _identity(),
        )


@pytest.mark.parametrize("bad", (True, float("nan"), float("inf"), 0.0, -1.0))
def test_frozen_wall_budget_rejects_bool_nonfinite_and_nonpositive_values(
    bad: object,
) -> None:
    snapshot = _snapshot()
    snapshot["budget"]["wall_clock_timeout_minutes"] = bad
    with pytest.raises(ValueError, match="budget"):
        preflight.verify_preflight_measurements(
            snapshot,
            _evidence(),
            _identity(),
        )
