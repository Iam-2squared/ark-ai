"""Bind detached WAV energy normalization to actual source PCM, not only hash."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark import offline_wave_energy_pipeline as pipeline
from ark.offline_pcm_wav import OfflineWaveRequest


def _request(rate: int) -> OfflineWaveRequest:
    frames = rate // 50
    pcm = struct.pack("<" + "h" * frames, *(
        ([0] * (frames // 2)) + ([2000] * (frames - frames // 2))
    ))
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate * 2, 2, 16)
    chunks = b"fmt " + struct.pack("<I", 16) + fmt
    chunks += b"data" + struct.pack("<I", len(pcm)) + pcm
    wav = b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks
    return OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(wav).hexdigest(), wav,
    )


@pytest.mark.parametrize("rate", [8000, 16000, 22050, 32000, 44100, 48000])
def test_valid_rates_preserve_offline_energy_without_authority(rate):
    preview = pipeline.preview_offline_wav_energy(_request(rate))
    assert preview.normalized_samples == 320
    assert preview.target_rate_hz == 16000
    assert preview.tool_execution_authorized is False
    assert preview.audio_disclosure_authorized is False


@pytest.mark.parametrize(
    "forgery",
    ["correct_digest_wrong_pcm", "wrong_source_rate", "wrong_source_count",
     "wrong_target_rate", "wrong_output_count", "duck_type"],
)
@pytest.mark.parametrize("rate", [8000, 16000, 48000])
def test_self_consistent_forged_resampler_cannot_retarget_activity(
    monkeypatch, rate, forgery,
):
    original = pipeline.resample_pcm16

    def forged(*args):
        actual = original(*args)
        if forgery == "duck_type":
            return SimpleNamespace(**{
                key: getattr(actual, key)
                for key in (
                    "source_sha256", "output_sha256", "source_rate",
                    "target_rate", "source_samples", "output_samples", "pcm",
                )
            })
        if forgery == "correct_digest_wrong_pcm":
            tampered = b"\0" * len(actual.pcm)
            assert tampered != actual.pcm
            return replace(
                actual, pcm=tampered,
                output_sha256=hashlib.sha256(tampered).hexdigest(),
            )
        if forgery == "wrong_source_rate":
            return replace(actual, source_rate=8001)
        if forgery == "wrong_source_count":
            return replace(actual, source_samples=actual.source_samples + 1)
        if forgery == "wrong_target_rate":
            return replace(actual, target_rate=8000)
        return replace(actual, output_samples=actual.output_samples + 1)

    monkeypatch.setattr(pipeline, "resample_pcm16", forged)
    with pytest.raises(
        pipeline.OfflineWavePipelineRejected, match="normalized PCM identity mismatch",
    ):
        pipeline.preview_offline_wav_energy(_request(rate))


def test_resample_projection_rejects_wrong_length_or_non_pcm():
    source = struct.pack("<2h", -1, 1)
    assert pipeline._verify_resample_projection(
        source, 8000, 16000, struct.pack("<4h", -1, 0, 1, 1),
    )
    assert not pipeline._verify_resample_projection(source, 8000, 16000, b"\0")
    assert not pipeline._verify_resample_projection(source, 8000, 16000, b"\0" * 8)
    assert not pipeline._verify_resample_projection(source, 8000, 16000, bytearray(8))
