"""Offline WAV fixtures reject forged SHA helpers before private byte access."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import replace

import pytest

import ark.offline_pcm_wav as wave


def _request() -> wave.OfflineWaveRequest:
    pcm = b"\x02\x00" * 80
    fmt = struct.pack("<HHIIHH", 1, 1, 8000, 16000, 2, 16)
    body = (
        b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(pcm)) + pcm
    )
    raw = b"RIFF" + struct.pack("<I", len(body)) + body
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


def test_rebound_sha_helper_never_receives_private_digest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    seen = []

    def attacker(value: object) -> bool:
        seen.append(value)
        raise AssertionError("substituted WAV SHA helper ran")

    monkeypatch.setattr(wave, "_sha", attacker)
    with pytest.raises(wave.OfflineWaveRejected, match="codec or digest"):
        wave.inspect_local_pcm_wav(request)
    assert seen == []


@pytest.mark.parametrize("field,bad", (
    ("owner_sha256", "a" * 63),
    ("owner_sha256", "a" * 65),
    ("privacy_sha256", "b" * 200_000),
    ("wav_sha256", "c" * 65),
    ("wav_sha256", "f" * 63 + "\ud800"),
))
def test_noncanonical_digest_width_and_unicode_refused(field: str, bad: str) -> None:
    with pytest.raises(wave.OfflineWaveRejected, match="shape"):
        wave.inspect_local_pcm_wav(replace(_request(), **{field: bad}))


def test_unchanged_wav_fixture_still_denies_all_authority() -> None:
    report = wave.inspect_local_pcm_wav(_request())
    assert report.frame_count == 80
    assert report.duration_ms_floor == 10
    assert report.microphone_provenance_verified is False
    assert report.consent_verified is False
    assert report.speech_recognized is False
    assert report.authorized_to_disclose is False
