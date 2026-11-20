"""Run1032: preflight evidence text carriers must be exact built-in strings.

Synthetic-only validation. No GPU, model, subprocess, billing or Candidate is used.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.learning.preflight import PreflightEvidence


class HostileText(str):
    def strip(self):
        raise AssertionError("hostile strip callback must not run")

    def encode(self, *args, **kwargs):
        raise AssertionError("hostile encode callback must not run")

    def __len__(self):
        raise AssertionError("hostile length callback must not run")


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


def test_device_string_subclass_is_rejected_before_strip_callback():
    evidence = replace(_evidence(), device=HostileText("SYNTHETIC GPU"))
    with pytest.raises(ValueError, match="valid accelerator identity"):
        evidence.validate()


def test_tokenizer_digest_string_subclass_is_rejected_before_regex_or_encode():
    evidence = replace(_evidence(), tokenizer_probe_sha256=HostileText("c" * 64))
    with pytest.raises(ValueError, match="tokenizer probe SHA-256"):
        evidence.validate()


def test_exact_builtin_text_carriers_remain_valid():
    evidence = _evidence()
    assert evidence.validate() is None
