"""End-to-end disconnected WAV fixture -> mono16 -> 16k energy regions."""

from __future__ import annotations

import hashlib
import struct

import pytest

from ark import offline_wave_energy_pipeline as pipeline
from ark.offline_pcm_wav import OfflineWaveRequest


def _wave(samples: bytes, *, rate: int = 16_000, channels: int = 1, bits: int = 16):
    frame_width = channels * bits // 8
    padding = b"\0" if len(samples) % 2 else b""
    fmt = struct.pack(
        "<HHIIHH", 1, channels, rate, rate * frame_width, frame_width, bits,
    )
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(samples)) + samples + padding
    return b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks


def _request(wav: bytes) -> OfflineWaveRequest:
    return OfflineWaveRequest(
        "1" * 64, "2" * 64, hashlib.sha256(wav).hexdigest(), wav,
    )


def _mono_frames():
    silence = struct.pack("<320h", *([0] * 320))
    tone = struct.pack("<320h", *([2000] * 320))
    return silence + tone + silence + tone


def test_end_to_end_mono16_energy_regions_without_sample_disclosure():
    wav = _wave(_mono_frames())
    preview = pipeline.preview_offline_wav_energy(_request(wav))
    assert preview.target_rate_hz == 16_000
    assert preview.normalized_samples == 1280
    assert preview.active_frame_count == 2
    assert len(preview.regions) == 1
    region = preview.regions[0]
    assert (region.start_frame, region.end_frame) == (1, 4)
    assert (region.start_sample, region.end_sample) == (320, 1280)
    assert region.active_frames == 2
    assert preview.microphone_authorized is False
    assert preview.speaker_authenticated is False
    assert preview.speech_recognized is False
    assert preview.audio_disclosure_authorized is False
    assert preview.tool_execution_authorized is False
    assert "pcm16_mono" not in repr(preview)
    assert "2000" not in repr(preview)


def test_stereo_8bit_8khz_fixture_normalizes_to_16khz_without_audio_output():
    silence = bytes((128, 128)) * 160
    tone = bytes((140, 140)) * 160
    preview = pipeline.preview_offline_wav_energy(
        _request(_wave(silence + tone, rate=8_000, channels=2, bits=8)),
    )
    assert preview.target_rate_hz == 16_000
    assert preview.normalized_samples == 640
    assert preview.active_frame_count == 1
    assert len(preview.regions) == 1
    assert preview.regions[0].start_frame == 1


@pytest.mark.parametrize("threshold,expected", ((0, 2), (512, 2), (3000, 0)))
def test_energy_threshold_does_not_claim_voice_detection(threshold, expected):
    wav = _wave(_mono_frames())
    preview = pipeline.preview_offline_wav_energy(
        _request(wav), rms_threshold=threshold,
    )
    assert preview.active_frame_count == expected
    assert preview.speech_recognized is False


@pytest.mark.parametrize("bad", (True, 512.0, -1, 32769, "512"))
def test_noncanonical_threshold_rejected(bad):
    with pytest.raises(pipeline.OfflineWavePipelineRejected, match="exact"):
        pipeline.preview_offline_wav_energy(
            _request(_wave(_mono_frames())), rms_threshold=bad,
        )


def test_same_fixture_and_params_yield_repeatable_digest():
    request = _request(_wave(_mono_frames()))
    first = pipeline.preview_offline_wav_energy(request)
    second = pipeline.preview_offline_wav_energy(request)
    assert first == second
    assert len(first.preview_sha256) == 64


def test_wav_checksum_mismatch_rejected_before_conversion():
    request = _request(_wave(_mono_frames()))
    object.__setattr__(request, "wav_sha256", "0" * 64)
    with pytest.raises(pipeline.OfflineWavePipelineRejected):
        pipeline.preview_offline_wav_energy(request)


def test_truncated_data_chunk_rejected():
    wav = _wave(_mono_frames())
    damaged = wav[:-2]
    with pytest.raises(pipeline.OfflineWavePipelineRejected):
        pipeline.preview_offline_wav_energy(_request(damaged))


def test_pcm_conversion_budget_rejects_large_valid_wave():
    pcm = b"\0\0" * (1024 * 1024 + 1)
    wav = _wave(pcm)
    with pytest.raises(pipeline.OfflineWavePipelineRejected):
        pipeline.preview_offline_wav_energy(_request(wav))


def test_reflective_input_mutation_mid_pipeline_rejected(monkeypatch):
    request = _request(_wave(_mono_frames()))
    original = pipeline.convert_offline_pcm_mono16

    def retarget(req):
        result = original(req)
        object.__setattr__(request, "privacy_sha256", "f" * 64)
        return result

    monkeypatch.setattr(pipeline, "convert_offline_pcm_mono16", retarget)
    with pytest.raises(pipeline.OfflineWavePipelineRejected, match="carrier"):
        pipeline.preview_offline_wav_energy(request)


def test_false_authority_getter_cannot_mutate_energy_preview(monkeypatch):
    original = pipeline.OfflineWaveEnergyPreview.tool_execution_authorized

    def malicious_false(self):
        object.__setattr__(self, "normalized_samples", 0)
        return False

    monkeypatch.setattr(
        pipeline.OfflineWaveEnergyPreview,
        "tool_execution_authorized",
        property(malicious_false),
    )
    with pytest.raises(pipeline.OfflineWavePipelineRejected, match="changed"):
        pipeline.preview_offline_wav_energy(_request(_wave(_mono_frames())))
    monkeypatch.setattr(
        pipeline.OfflineWaveEnergyPreview, "tool_execution_authorized", original,
    )
