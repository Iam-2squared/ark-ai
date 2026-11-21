"""Disconnected image+audio fixture join: metadata only, never authorization."""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import replace

import pytest

from ark import offline_observation_pair as mod
from ark.offline_pcm_wav import OfflineWaveRequest
from ark.offline_png_inventory import OfflinePngRequest

OWNER = "a" * 64
PRIVACY = "b" * 64


def _chunk(name: bytes, payload: bytes) -> bytes:
    header = struct.pack(">I", len(payload)) + name
    crc = struct.pack(">I", zlib.crc32(name + payload))
    return header + payload + crc


def _png() -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    data = zlib.compress(b"\x00\x00\x00\x00")
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", data)
        + _chunk(b"IEND", b"")
    )


def _wav() -> bytes:
    fmt = struct.pack("<HHIIHH", 1, 1, 16000, 32000, 2, 16)
    pcm = b"\x00\x00" * 16
    chunks = (
        b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(pcm)) + pcm
    )
    return b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks


def _case():
    png = _png()
    wav = _wav()
    image = OfflinePngRequest(OWNER, PRIVACY, hashlib.sha256(png).hexdigest(), png)
    audio = OfflineWaveRequest(OWNER, PRIVACY, hashlib.sha256(wav).hexdigest(), wav)
    pins = {
        "retained_owner_sha256": OWNER,
        "retained_privacy_sha256": PRIVACY,
        "retained_png_sha256": image.source_sha256,
        "retained_wav_sha256": audio.wav_sha256,
    }
    return image, audio, pins


def _inspect(image, audio, pins):
    return mod.inspect_disconnected_observation_pair(image, audio, **pins)


def test_local_png_wav_pair_has_metadata_and_no_authority():
    image, audio, pins = _case()
    pair = _inspect(image, audio, pins)
    assert type(pair) is mod.OfflineObservationPair
    assert (pair.width, pair.height, pair.sample_rate_hz, pair.audio_frames) == (
        1, 1, 16000, 16,
    )
    assert pair.png_sha256 == image.source_sha256
    assert pair.wav_sha256 == audio.wav_sha256
    assert len(pair.image_idat_sha256) == 64
    assert len(pair.pcm_sha256) == 64
    assert len(pair.pair_sha256) == 64
    assert all(getattr(pair, name) is False for name in mod._DENIALS)


@pytest.mark.parametrize("mismatch", (
    "png_owner", "audio_privacy", "retained_png", "retained_wav",
    "retained_owner", "retained_privacy",
))
def test_pair_rejects_foreign_or_stale_identity(mismatch):
    image, audio, pins = _case()
    if mismatch == "png_owner":
        image = replace(image, owner_sha256="f" * 64)
    elif mismatch == "audio_privacy":
        audio = replace(audio, privacy_sha256="f" * 64)
    else:
        pins["retained_" + mismatch.removeprefix("retained_") + "_sha256"] = "f" * 64
    with pytest.raises(mod.OfflineObservationPairRejected, match="differs"):
        _inspect(image, audio, pins)


@pytest.mark.parametrize("kind", ("png", "wav"))
def test_corrupt_media_bytes_do_not_produce_a_pair(kind):
    image, audio, pins = _case()
    if kind == "png":
        image = replace(image, png_bytes=image.png_bytes[:-1] + b"\x01")
    else:
        audio = replace(audio, wav_bytes=audio.wav_bytes[:-1] + b"\x01")
    with pytest.raises(mod.OfflineObservationPairRejected, match="media inventory"):
        _inspect(image, audio, pins)


@pytest.mark.parametrize("name", (
    "camera_provenance_verified", "microphone_provenance_verified",
    "consent_verified", "external_disclosure_authorized",
    "tool_execution_authorized",
))
def test_false_only_authority_substitute_rejected_before_media_read(
    monkeypatch, name,
):
    image, audio, pins = _case()

    def forbidden(_image):
        raise AssertionError("bad authority must not inspect image bytes")

    monkeypatch.setattr(mod, "inspect_disconnected_png", forbidden)
    monkeypatch.setattr(mod.OfflineObservationPair, name, property(lambda _: False))
    with pytest.raises(mod.OfflineObservationPairRejected, match="descriptor replaced"):
        _inspect(image, audio, pins)


def test_png_callback_cannot_mutate_audio_scope_during_join(monkeypatch):
    image, audio, pins = _case()
    original = mod.inspect_disconnected_png

    def mutate(req):
        result = original(req)
        object.__setattr__(audio, "privacy_sha256", "f" * 64)
        return result

    monkeypatch.setattr(mod, "inspect_disconnected_png", mutate)
    with pytest.raises(mod.OfflineObservationPairRejected, match="carrier changed"):
        _inspect(image, audio, pins)


def test_second_media_observation_must_match_first(monkeypatch):
    image, audio, pins = _case()
    original = mod.inspect_disconnected_png
    calls = 0

    def drifting(req):
        nonlocal calls
        calls += 1
        inventory = original(req)
        if calls == 2:
            object.__setattr__(inventory, "width", 2)
        return inventory

    monkeypatch.setattr(mod, "inspect_disconnected_png", drifting)
    with pytest.raises(mod.OfflineObservationPairRejected, match="drifted"):
        _inspect(image, audio, pins)
    assert calls == 2
