"""Disconnected WAV metadata must not execute injected authority or initializer code."""

import hashlib
import struct
from types import SimpleNamespace

import pytest

import ark.offline_pcm_wav as wave


def _request():
    pcm = b"\x01\x00" * 80
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    body = (
        b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt
        + b"data" + struct.pack("<I", len(pcm)) + pcm
    )
    raw = b"RIFF" + struct.pack("<I", len(body)) + body
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


@pytest.mark.parametrize("phase", ("preinstalled", "during_source_sha"))
def test_substituted_wav_initializer_is_never_run(monkeypatch, phase):
    request = _request()
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append(True)
        raise AssertionError("forged WAV initializer executed")

    with monkeypatch.context() as patch:
        if phase == "preinstalled":
            patch.setattr(wave.OfflineWaveReview, "__init__", forbidden)
        else:
            original = hashlib.sha256

            def after_source_digest(data=b"", *args, **kwargs):
                result = original(data, *args, **kwargs)
                if data == request.wav_bytes:
                    patch.setattr(wave.OfflineWaveReview, "__init__", forbidden)
                return result

            patch.setattr(wave, "hashlib", SimpleNamespace(sha256=after_source_digest))
        # A preinstalled forged constructor is refused directly; when the
        # digest module is substituted, the new preaccess fence refuses that
        # callback before it can install the constructor at all.
        expected = "constructed WAV" if phase == "preinstalled" else "codec or digest"
        with pytest.raises(wave.OfflineWaveRejected, match=expected):
            wave.inspect_local_pcm_wav(request)
    assert invoked == []


@pytest.mark.parametrize("denial", (
    "microphone_provenance_verified", "consent_verified",
    "speech_recognized", "authorized_to_disclose",
))
def test_preinstalled_false_wave_getter_is_not_executed(monkeypatch, denial):
    request = _request()
    invoked = []

    def unsafe(_self):
        invoked.append(True)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(wave.OfflineWaveReview, denial, property(unsafe))
        with pytest.raises(wave.OfflineWaveRejected, match="denial authority"):
            wave.inspect_local_pcm_wav(request)
    assert invoked == []


def test_valid_disconnected_pcm_receipt_stays_inert():
    report = wave.inspect_local_pcm_wav(_request())
    assert report.channel_count == 1
    assert report.frame_count == 80
    assert report.duration_ms_floor == 10
    assert report.microphone_provenance_verified is False
    assert report.consent_verified is False
    assert report.speech_recognized is False
    assert report.authorized_to_disclose is False
