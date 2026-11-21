"""Disconnected WAV energy pipeline rechecks format from original source bytes."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import replace

import pytest

from ark import offline_wave_energy_pipeline as pipeline
from ark.offline_pcm_wav import OfflineWaveRequest


def _request(*, rate=16_000, bits=16, channels=1, frames=640):
    frame_width = channels * (bits // 8)
    pcm = bytes([128] * frames * frame_width) if bits == 8 else bytes(
        [0] * frames * frame_width
    )
    fmt = struct.pack(
        "<HHIIHH", 1, channels, rate, rate * frame_width, frame_width, bits,
    )
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(pcm)) + pcm
    if len(pcm) & 1:
        chunks += bytes((0,))
    wave = b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks
    return OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(wave).hexdigest(), wave,
    )


@pytest.mark.parametrize("rate,bits,channels,frames", (
    (16_000, 16, 1, 640),
    (8_000, 8, 2, 320),
    (48_000, 16, 1, 960),
    (16_000, 8, 1, 641),
))
def test_original_canonical_pcm_headers_still_pass(rate, bits, channels, frames):
    request = _request(rate=rate, bits=bits, channels=channels, frames=frames)
    report = pipeline.preview_offline_wav_energy(request)
    assert report.wav_sha256 == request.wav_sha256
    assert report.target_rate_hz == 16_000
    assert report.microphone_authorized is False
    assert report.speech_recognized is False


@pytest.mark.parametrize("field,value", (
    ("sample_rate_hz", 8000),
    ("duration_ms_floor", 999),
    ("duration_ms_remainder", 999),
    ("bits_per_sample", 8),
    ("channel_count", 2),
))
def test_exact_wave_callback_cannot_relabel_format_with_valid_wav_hash(
    monkeypatch, field, value,
):
    request = _request()
    native = pipeline.inspect_local_pcm_wav

    def forged(source):
        original = native(source)
        return replace(original, **{field: value})

    monkeypatch.setattr(pipeline, "inspect_local_pcm_wav", forged)
    with pytest.raises(pipeline.OfflineWavePipelineRejected, match="format disagrees"):
        pipeline.preview_offline_wav_energy(request)
    assert hashlib.sha256(request.wav_bytes).hexdigest() == request.wav_sha256
