"""Detached WAV result custody, preventing forged sensor/consent evidence."""

from __future__ import annotations

import hashlib
import struct

import pytest

import ark.offline_pcm_wav as wave


def _request():
    audio = b"\x01\x00" * 80
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    body = (
        b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt
        + b"data" + struct.pack("<I", len(audio)) + audio
    )
    data = b"RIFF" + struct.pack("<I", len(body)) + body
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(data).hexdigest(), data,
    )


def test_valid_fixture_is_inert_and_content_free():
    output = wave.inspect_local_pcm_wav(_request())
    assert output.frame_count == 80
    assert output.duration_ms_floor == 10
    assert output.consent_verified is False
    assert output.microphone_provenance_verified is False
    assert output.speech_recognized is False
    assert output.authorized_to_disclose is False
    assert b"\x01\x00" not in repr(output).encode("utf-8")


def test_forged_result_class_cannot_supply_action_authority(monkeypatch):
    monkeypatch.setattr(wave, "OfflineWaveReview", lambda *args: object())
    with pytest.raises(wave.OfflineWaveRejected, match="constructed WAV"):
        wave.inspect_local_pcm_wav(_request())


@pytest.mark.parametrize("field", [
    "consent_verified", "microphone_provenance_verified",
    "speech_recognized", "authorized_to_disclose",
])
def test_result_property_authority_forgery_denied(monkeypatch, field):
    monkeypatch.setattr(
        wave._REVIEW_TYPE, field, property(lambda self: True),
    )
    with pytest.raises(wave.OfflineWaveRejected, match="claims authority"):
        wave.inspect_local_pcm_wav(_request())


def test_same_type_receipt_field_mutation_denied(monkeypatch):
    original = wave._REVIEW_TYPE

    def forge(*args):
        output = original(*args)
        object.__setattr__(output, "pcm_sha256", "f" * 64)
        return output

    monkeypatch.setattr(wave, "OfflineWaveReview", forge)
    with pytest.raises(wave.OfflineWaveRejected, match="constructed WAV"):
        wave.inspect_local_pcm_wav(_request())


def test_original_source_mutation_during_receipt_construction_denied(monkeypatch):
    request = _request()
    original = wave._REVIEW_TYPE

    def mutate(*args):
        object.__setattr__(request, "privacy_sha256", "f" * 64)
        return original(*args)

    monkeypatch.setattr(wave, "OfflineWaveReview", mutate)
    with pytest.raises(wave.OfflineWaveRejected, match="carrier changed"):
        wave.inspect_local_pcm_wav(request)
