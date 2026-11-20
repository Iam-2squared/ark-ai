"""Run1021: preflight identity text fields reject str subclasses before callbacks."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.preflight import PreflightEvidence


class StripCallbackText(str):
    def strip(self, chars=None):
        raise AssertionError("untrusted device.strip callback must not run")


def _evidence() -> PreflightEvidence:
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


def test_preflight_device_rejects_str_subclass_before_strip_callback() -> None:
    evidence = replace(
        _evidence(),
        device=StripCallbackText("SYNTHETIC GPU"),
    )
    with pytest.raises(ValueError, match="valid accelerator identity"):
        evidence.validate()


def test_preflight_tokenizer_digest_rejects_str_subclass() -> None:
    evidence = replace(
        _evidence(),
        tokenizer_probe_sha256=StripCallbackText("c" * 64),
    )
    with pytest.raises(ValueError, match="tokenizer probe SHA-256 required"):
        evidence.validate()


def test_exact_builtin_preflight_text_fields_remain_valid() -> None:
    evidence = _evidence()
    assert type(evidence.device) is str
    assert type(evidence.tokenizer_probe_sha256) is str
    assert evidence.validate() is None
