"""WAV fixture inputs and denial-only outputs reject reflected getters.

Only generated PCM bytes are inspected, with no device or network access.
"""

from __future__ import annotations

import hashlib
import struct
from types import SimpleNamespace

import pytest

import ark.offline_pcm_wav as wave


def _request():
    samples = b"\x01\x00" * 80
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    body = (
        b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(samples)) + samples
    )
    raw = b"RIFF" + struct.pack("<I", len(body)) + body
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


@pytest.mark.parametrize(
    "target,field",
    (
        ("request", "wav_bytes"),
        ("request", "wav_sha256"),
        ("request", "privacy_sha256"),
        ("request", "__getattribute__"),
        ("request", "__getattr__"),
        ("review", "pcm_sha256"),
        ("review", "frame_count"),
        ("review", "__getattribute__"),
    ),
)
def test_wav_forged_field_never_executes_preflight(
    monkeypatch, target, field,
):
    request = _request()
    cls = (
        wave.OfflineWaveRequest if target == "request"
        else wave.OfflineWaveReview
    )
    invoked = []

    def hostile(*_args, **_kwargs):
        invoked.append(True)
        raise AssertionError("forged WAV getter executed")

    replacement = hostile if field.startswith("__") else property(hostile)
    with monkeypatch.context() as patch:
        patch.setattr(cls, field, replacement, raising=False)
        with pytest.raises(
            wave.OfflineWaveRejected,
            match="request identity|constructed WAV",
        ):
            wave.inspect_local_pcm_wav(request)
    assert invoked == []


@pytest.mark.parametrize("target", ("request", "review"))
def test_wav_digest_callback_cannot_install_late_forged_getter(
    monkeypatch, target,
):
    request = _request()
    klass, field = (
        (wave.OfflineWaveRequest, "wav_bytes")
        if target == "request"
        else (wave.OfflineWaveReview, "pcm_sha256")
    )
    invoked = []
    digest_invocations = []
    original_sha = hashlib.sha256

    def hostile(*_args, **_kwargs):
        invoked.append(True)
        raise AssertionError("late WAV getter executed")

    with monkeypatch.context() as patch:
        def digest(data=b"", *args, **kwargs):
            digest_invocations.append(True)
            answer = original_sha(data, *args, **kwargs)
            if data == request.wav_bytes:
                patch.setattr(klass, field, property(hostile))
            return answer

        patch.setattr(wave, "hashlib", SimpleNamespace(sha256=digest))
        with pytest.raises(
            wave.OfflineWaveRejected,
            match="WAV codec or digest implementation changed before private bytes",
        ):
            wave.inspect_local_pcm_wav(request)
    assert invoked == []
    assert digest_invocations == []


def test_unmodified_wav_stays_inert_and_content_free():
    report = wave.inspect_local_pcm_wav(_request())
    assert report.channel_count == 1
    assert report.sample_rate_hz == 8000
    assert report.frame_count == 80
    assert report.duration_ms_floor == 10
    assert report.microphone_provenance_verified is False
    assert report.consent_verified is False
    assert report.speech_recognized is False
    assert report.authorized_to_disclose is False
