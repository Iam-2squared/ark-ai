"""WAV metadata may not mint authority by replacing a denied class property.

Only explicit synthetic local RIFF bytes are parsed. These tests do not use
microphones, identify speakers, persist audio, or authorize disclosure.
"""

from __future__ import annotations

import hashlib
import struct

import pytest

from ark import offline_pcm_wav as wave


def _fixture() -> wave.OfflineWaveRequest:
    samples = bytes(160)
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    chunks = (
        b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(samples)) + samples
    )
    raw = b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


def test_canonical_local_wav_remains_denied_and_unexported():
    source = _fixture()
    review = wave.inspect_local_pcm_wav(source)
    assert review.frame_count == 80
    assert review.channel_count == 1
    assert review.sample_rate_hz == 8000
    assert review.microphone_provenance_verified is False
    assert review.consent_verified is False
    assert review.speech_recognized is False
    assert review.authorized_to_disclose is False


@pytest.mark.parametrize(
    "getter,target,retargeted_value",
    (
        ("authorized_to_disclose", "microphone_provenance_verified", True),
        ("authorized_to_disclose", "consent_verified", False),
        ("speech_recognized", "consent_verified", True),
        ("speech_recognized", "microphone_provenance_verified", False),
    ),
)
def test_late_false_denial_getter_cannot_rebind_earlier_authority(
    monkeypatch, getter, target, retargeted_value,
):
    cls = wave._REVIEW_TYPE
    read_count = []

    def mutate(self):
        read_count.append(getter)
        # Even another False-valued property is a different descriptor epoch.
        monkeypatch.setattr(cls, target, property(lambda self: retargeted_value))
        return False

    monkeypatch.setattr(cls, getter, property(mutate))
    with pytest.raises(
        wave.OfflineWaveRejected, match="denial authority descriptors changed",
    ):
        wave.inspect_local_pcm_wav(_fixture())
    assert read_count == []  # Forged getter is rejected before any callback.


def test_unchanged_denial_descriptors_allow_repeated_passive_review():
    source = _fixture()
    first = wave.inspect_local_pcm_wav(source)
    second = wave.inspect_local_pcm_wav(source)
    assert first == second
    assert first.wav_sha256 == second.wav_sha256
    assert source.wav_bytes.startswith(b"RIFF")
