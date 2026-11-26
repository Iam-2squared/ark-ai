"""Offline WAV activity previews require independently recomputed full regions."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import replace

import pytest

from ark import offline_wave_energy_pipeline as pipeline
from ark.offline_pcm_activity_regions import ActivityRegion
from ark.offline_pcm_wav import OfflineWaveRequest


def _wav(*, silence: bool = False):
    samples = [0] * 320 + ([0] if silence else [2000]) * 320
    pcm = struct.pack("<640h", *samples)
    fmt = struct.pack("<HHIIHH", 1, 1, 16000, 32000, 2, 16)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
    chunks += b"data" + struct.pack("<I", len(pcm)) + pcm
    raw = b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks
    return OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


def test_valid_offline_region_derived_without_audio_exposure():
    preview = pipeline.preview_offline_wav_energy(_wav())
    assert preview.target_rate_hz == 16000
    assert preview.active_frame_count == 1
    assert preview.normalized_samples == 640
    assert preview.regions == (ActivityRegion(1, 2, 320, 640, 1),)
    assert preview.microphone_authorized is False
    assert preview.audio_disclosure_authorized is False
    assert preview.speech_recognized is False
    assert preview.tool_execution_authorized is False


def test_silence_remains_a_valid_non_authenticating_preview():
    preview = pipeline.preview_offline_wav_energy(_wav(silence=True))
    assert preview.active_frame_count == 0
    assert preview.regions == ()
    assert preview.microphone_authorized is False


@pytest.mark.parametrize("field,forged", (
    ("source_sha256", "f" * 64),
    ("sample_rate", 8000),
    ("frame_samples", 160),
    ("total_samples", 320),
    ("active_frame_count", 2),
    ("regions", ()),
    ("regions", (ActivityRegion(1, 2, 320, 640, 2),)),
    ("regions", (ActivityRegion(0, 2, 0, 640, 1),)),
))
def test_child_report_field_spoofing_rejected_by_parent(
    monkeypatch, field, forged,
):
    actual = pipeline.detect_activity_regions

    def forged_result(*args, **kwargs):
        child = actual(*args, **kwargs)
        return replace(child, **{field: forged})

    monkeypatch.setattr(pipeline, "detect_activity_regions", forged_result)
    with pytest.raises(pipeline.OfflineWavePipelineRejected):
        pipeline.preview_offline_wav_energy(_wav())


def test_wrong_child_report_type_is_rejected(monkeypatch):
    monkeypatch.setattr(
        pipeline, "detect_activity_regions", lambda *args, **kwargs: object(),
    )
    with pytest.raises(pipeline.OfflineWavePipelineRejected, match="exact"):
        pipeline.preview_offline_wav_energy(_wav())


def test_false_final_authority_getter_cannot_rewrite_activity(monkeypatch):
    actual = pipeline.detect_activity_regions
    retained = []

    def detect(*args, **kwargs):
        report = actual(*args, **kwargs)
        retained.append(report)
        return report

    def malicious_false(self):
        object.__setattr__(retained[0], "active_frame_count", 0)
        return False

    monkeypatch.setattr(pipeline, "detect_activity_regions", detect)
    monkeypatch.setattr(
        pipeline.OfflineWaveEnergyPreview,
        "tool_execution_authorized",
        property(malicious_false),
    )
    with pytest.raises(pipeline.OfflineWavePipelineRejected):
        pipeline.preview_offline_wav_energy(_wav())
