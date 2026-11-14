"""Inert WAV parsing must not execute substituted digest/codec callbacks.

The caller-supplied audio remains local; these tests grant no capture,
authorization, disclosure, or independent provenance.
"""

import hashlib
import re
import struct
from types import SimpleNamespace

import pytest

from ark import offline_pcm_wav as wave


def _request():
    audio = bytes((1, 0)) * 80
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    body = b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt
    body += b"data" + struct.pack("<I", len(audio)) + audio
    wav = b"RIFF" + struct.pack("<I", len(body)) + body
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(wav).hexdigest(), wav,
    )


@pytest.mark.parametrize("surface", (
    "hash_module", "hash_function", "codec_module", "codec_function",
    "digest_pattern", "source_budget", "duration_budget",
))
def test_swapped_wav_codec_is_denied_before_audio_read(monkeypatch, surface):
    request = _request()
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append(True)
        raise AssertionError("untrusted WAV codec received private bytes")

    with monkeypatch.context() as patch:
        if surface == "hash_module":
            patch.setattr(wave, "hashlib", SimpleNamespace(sha256=forbidden))
        elif surface == "hash_function":
            patch.setattr(wave.hashlib, "sha256", forbidden)
        elif surface == "codec_module":
            patch.setattr(wave, "struct", SimpleNamespace(unpack_from=forbidden))
        elif surface == "codec_function":
            patch.setattr(wave.struct, "unpack_from", forbidden)
        elif surface == "digest_pattern":
            patch.setattr(wave, "_SHA", re.compile(".*"))
        elif surface == "source_budget":
            patch.setattr(wave, "_MAX_WAV_BYTES", wave._MAX_WAV_BYTES + 1)
        else:
            patch.setattr(wave, "_MAX_DURATION_SECONDS", 121)
        with pytest.raises(wave.OfflineWaveRejected, match="codec or digest"):
            wave.inspect_local_pcm_wav(request)
    assert invoked == []
    assert request.privacy_sha256 == "b" * 64


def test_canonical_wave_review_remains_local_and_non_authorizing():
    review = wave.inspect_local_pcm_wav(_request())
    assert review.frame_count == 80
    assert review.duration_ms_floor == 10
    assert review.microphone_provenance_verified is False
    assert review.consent_verified is False
    assert review.speech_recognized is False
    assert review.authorized_to_disclose is False
