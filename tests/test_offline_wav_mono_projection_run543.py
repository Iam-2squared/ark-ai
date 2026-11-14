"""WAV pipeline must bind claimed PCM conversion to original sample bytes."""

from __future__ import annotations

import hashlib
import json
import struct
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark import offline_wave_energy_pipeline as pipeline
from ark.offline_pcm_wav import OfflineWaveRequest


def _wave(raw: bytes, *, channels: int = 1, bits: int = 16) -> OfflineWaveRequest:
    rate = 16_000
    frame_width = channels * bits // 8
    fmt = struct.pack(
        "<HHIIHH", 1, channels, rate, rate * frame_width,
        frame_width, bits,
    )
    body = b"fmt " + struct.pack("<I", 16) + fmt
    body += b"data" + struct.pack("<I", len(raw)) + raw
    if len(raw) % 2:
        body += b"\0"
    container = b"RIFF" + struct.pack("<I", 4 + len(body)) + b"WAVE" + body
    return OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(container).hexdigest(), container,
    )


def _forged_mono(result, *, manifest_also_forged: bool):
    original = result.pcm16_mono
    wrong = b"\0" * len(original)
    assert wrong != original
    digest = hashlib.sha256(wrong).hexdigest()
    inventory = result.inventory_sha256
    if manifest_also_forged:
        payload = {
            "owner": result.owner_sha256,
            "privacy": result.privacy_sha256,
            "source": result.source_sha256,
            "output": digest,
            "frames": result.frame_count,
            "channels": result.source_channels,
            "rate": result.sample_rate_hz,
            "bits": result.source_bits_per_sample,
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
        inventory = hashlib.sha256(
            b"ARK-offline-pcm-mono16-v1\0" + canonical
        ).hexdigest()
    return replace(
        result, pcm16_mono=wrong,
        output_sha256=digest, inventory_sha256=inventory,
    )


@pytest.mark.parametrize("manifest_also_forged", (True, False))
@pytest.mark.parametrize(
    "channels,bits,raw",
    (
        (1, 16, struct.pack("<320h", *([2000] * 320))),
        (2, 8, bytes([140, 140] * 320)),
        (1, 24, b"\0\x10\0" * 320),
    ),
)
def test_digest_consistent_but_wrong_mono_samples_are_rejected(
    monkeypatch, channels, bits, raw, manifest_also_forged,
):
    request = _wave(raw, channels=channels, bits=bits)
    original = pipeline.convert_offline_pcm_mono16

    def forged_conversion(req):
        return _forged_mono(
            original(req), manifest_also_forged=manifest_also_forged,
        )

    monkeypatch.setattr(pipeline, "convert_offline_pcm_mono16", forged_conversion)
    with pytest.raises(
        pipeline.OfflineWavePipelineRejected,
        match="mono PCM conversion inconsistent",
    ):
        pipeline.preview_offline_wav_energy(request)


def test_duck_typed_converter_receipt_is_not_accepted(monkeypatch):
    request = _wave(struct.pack("<320h", *([2000] * 320)))
    original = pipeline.convert_offline_pcm_mono16

    def forged_conversion(req):
        result = original(req)
        return SimpleNamespace(
            **{
                name: getattr(result, name)
                for name in (
                    "owner_sha256", "privacy_sha256", "source_sha256",
                    "output_sha256", "inventory_sha256", "sample_rate_hz",
                    "source_channels", "source_bits_per_sample",
                    "frame_count", "pcm16_mono",
                )
            }
        )

    monkeypatch.setattr(pipeline, "convert_offline_pcm_mono16", forged_conversion)
    with pytest.raises(
        pipeline.OfflineWavePipelineRejected,
        match="mono PCM conversion inconsistent",
    ):
        pipeline.preview_offline_wav_energy(request)


@pytest.mark.parametrize(
    "channels,bits,raw",
    (
        (1, 16, struct.pack("<320h", *([2000] * 320))),
        (2, 8, bytes([140, 140] * 320)),
        (1, 24, b"\0\x10\0" * 320),
    ),
)
def test_normal_offline_samples_still_preview_without_authority(
    channels, bits, raw,
):
    result = pipeline.preview_offline_wav_energy(
        _wave(raw, channels=channels, bits=bits),
    )
    assert result.target_rate_hz == 16_000
    assert result.normalized_samples == 320
    assert result.audio_disclosure_authorized is False
    assert result.tool_execution_authorized is False
