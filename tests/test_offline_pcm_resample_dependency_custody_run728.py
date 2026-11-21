"""Raw fixture PCM must never reach substituted codec/hash callbacks.

No media capture, microphone access, external ASR, dispatch or data upload.
"""

from __future__ import annotations

import hashlib
import re

import pytest

from ark import offline_pcm_resample16 as pcm


@pytest.mark.parametrize("target", (
    "sha256", "iter_unpack", "pack_into", "hashlib_module",
    "struct_module", "rates", "sha_pattern", "byte_budget",
    "rounding", "result_init", "result_pcm_field",
))
def test_preinstalled_private_pcm_callback_or_contract_drift_rejected(
    monkeypatch, target,
):
    raw = bytes((1, 0, 2, 0))
    expected = hashlib.sha256(raw).hexdigest()
    calls = []

    def hostile(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted PCM callback executed")

    if target == "sha256":
        monkeypatch.setattr(pcm.hashlib, "sha256", hostile)
    elif target == "iter_unpack":
        monkeypatch.setattr(pcm.struct, "iter_unpack", hostile)
    elif target == "pack_into":
        monkeypatch.setattr(pcm.struct, "pack_into", hostile)
    elif target == "hashlib_module":
        monkeypatch.setattr(pcm, "hashlib", object())
    elif target == "struct_module":
        monkeypatch.setattr(pcm, "struct", object())
    elif target == "rates":
        monkeypatch.setattr(pcm, "_RATES", frozenset((8000, 16000)))
    elif target == "sha_pattern":
        monkeypatch.setattr(pcm, "_SHA256", re.compile(r"[0-9a-fA-F]{64}\Z"))
    elif target == "byte_budget":
        monkeypatch.setattr(pcm, "MAX_PCM_BYTES", pcm.MAX_PCM_BYTES + 2)
    elif target == "rounding":
        monkeypatch.setattr(pcm, "_round_ratio_away_from_zero", hostile)
    elif target == "result_init":
        monkeypatch.setattr(pcm.ResampledPcm, "__init__", hostile)
    else:
        monkeypatch.setattr(pcm.ResampledPcm, "pcm", property(hostile))

    with pytest.raises(
        pcm.OfflineResampleRejected,
        match="PCM dependency or carrier authority changed",
    ):
        pcm.resample_pcm16(raw, expected, 8000, 16000)
    assert calls == []


def test_unmodified_resampler_keeps_deterministic_sensitive_output_private():
    raw = bytes((1, 0, 2, 0))
    expected = hashlib.sha256(raw).hexdigest()
    result = pcm.resample_pcm16(raw, expected, 8000, 16000)
    assert result.source_samples == 2
    assert result.output_samples == 4
    assert result.source_sha256 == expected
    assert result.output_sha256 == hashlib.sha256(result.pcm).hexdigest()
    assert "pcm=" not in repr(result)
