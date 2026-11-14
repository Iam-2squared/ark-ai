"""Disconnected multimodal metadata/transcript bridge (no ASR or permissions)."""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import replace

import pytest

from ark import offline_observation_pair as pair_mod
from ark import offline_observation_transcript as mod
from ark import offline_transcript_binding as transcript_mod
from ark.offline_pcm_wav import OfflineWaveRequest
from ark.offline_png_inventory import OfflinePngRequest

OWNER = "a" * 64
PRIVACY = "b" * 64


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload)) + kind + payload
        + struct.pack(">I", zlib.crc32(kind + payload))
    )


def _case():
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + _chunk(b"IEND", b"")
    )
    fmt = struct.pack("<HHIIHH", 1, 1, 16000, 32000, 2, 16)
    pcm = b"\x00\x00" * 16
    wave_data = (
        b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(pcm)) + pcm
    )
    wav = b"RIFF" + struct.pack("<I", len(wave_data) + 4) + b"WAVE" + wave_data
    image = OfflinePngRequest(OWNER, PRIVACY, hashlib.sha256(png).hexdigest(), png)
    audio = OfflineWaveRequest(OWNER, PRIVACY, hashlib.sha256(wav).hexdigest(), wav)
    raw_text = "hello"
    segments = (transcript_mod.TranscriptSegmentClaim(
        0, 8, "en", hashlib.sha256(raw_text.encode()).hexdigest(), raw_text,
    ),)
    claim = transcript_mod.AudioMetadataClaim(
        OWNER, PRIVACY, audio.wav_sha256, 16000, 16,
    )
    fingerprint = transcript_mod.review_audio_transcript_binding(
        claim, segments,
    ).fingerprint
    retained = {
        "retained_owner_sha256": OWNER,
        "retained_privacy_sha256": PRIVACY,
        "retained_png_sha256": image.source_sha256,
        "retained_wav_sha256": audio.wav_sha256,
        "retained_transcript_fingerprint": fingerprint,
    }
    return image, audio, segments, retained


def _join(image, audio, segments, retained):
    return mod.review_disconnected_observation_transcript(
        image, audio, segments, **retained,
    )


def test_metadata_only_transcript_binding_is_deterministic_and_denied():
    image, audio, segments, retained = _case()
    first = _join(image, audio, segments, retained)
    second = _join(image, audio, segments, retained)
    assert type(first) is mod.OfflineObservationTranscript
    assert first == second
    assert (first.segment_count, first.first_frame, first.final_frame) == (1, 0, 8)
    assert first.transcript_fingerprint == retained["retained_transcript_fingerprint"]
    assert len(first.pair_sha256) == len(first.envelope_sha256) == 64
    assert all(getattr(first, name) is False for name in mod._DENIAL_NAMES)
    assert segments[0].text not in repr(first)


@pytest.mark.parametrize("field", (
    "retained_owner_sha256", "retained_privacy_sha256",
    "retained_png_sha256", "retained_wav_sha256",
    "retained_transcript_fingerprint",
))
def test_stale_or_foreign_claim_fails_closed(field):
    image, audio, segments, retained = _case()
    retained[field] = "f" * 64
    with pytest.raises(mod.OfflineObservationTranscriptRejected):
        _join(image, audio, segments, retained)


@pytest.mark.parametrize("kind", ("list", "missing", "bad_text", "bad_audio"))
def test_invalid_or_undeclared_carriers_rejected(kind):
    image, audio, segments, retained = _case()
    if kind == "list":
        segments = list(segments)
    elif kind == "missing":
        segments = ()
    elif kind == "bad_text":
        segments = (replace(segments[0], text="other"),)
    else:
        audio = replace(audio, wav_bytes=audio.wav_bytes[:-1] + b"\x01")
    with pytest.raises(mod.OfflineObservationTranscriptRejected):
        _join(image, audio, segments, retained)


@pytest.mark.parametrize("name", mod._DENIAL_NAMES)
def test_result_false_only_authority_replacement_rejected_before_read(
    monkeypatch, name,
):
    image, audio, segments, retained = _case()
    monkeypatch.setattr(mod.OfflineObservationTranscript, name, property(lambda _: False))

    def forbidden(*args, **kwargs):
        raise AssertionError("substituted authority must reject before reading media")

    monkeypatch.setattr(mod, "_PAIR_FN", forbidden)
    with pytest.raises(mod.OfflineObservationTranscriptRejected, match="replaced"):
        _join(image, audio, segments, retained)


@pytest.mark.parametrize("name", mod._TRANSCRIPT_DENIALS)
def test_transcript_false_only_authority_replacement_is_rejected(
    monkeypatch, name,
):
    image, audio, segments, retained = _case()
    monkeypatch.setattr(
        transcript_mod.TranscriptBindingPreview, name, property(lambda _: False),
    )
    with pytest.raises(mod.OfflineObservationTranscriptRejected, match="replaced"):
        _join(image, audio, segments, retained)


def test_transcript_callable_replacement_rejected_before_media_callback(monkeypatch):
    image, audio, segments, retained = _case()
    original = mod._TRANSCRIPT_FN

    def mutate(claim, spans):
        result = original(claim, spans)
        object.__setattr__(image, "privacy_sha256", "f" * 64)
        return result

    monkeypatch.setattr(mod, "_TRANSCRIPT_FN", mutate)
    # Rebinding this function is rejected *before* it may mutate the image.
    with pytest.raises(mod.OfflineObservationTranscriptRejected, match="replaced"):
        _join(image, audio, segments, retained)


def test_transcript_callable_swap_rejects_before_any_second_pass(monkeypatch):
    image, audio, segments, retained = _case()
    original = mod._TRANSCRIPT_FN
    calls = 0

    def drift(claim, spans):
        nonlocal calls
        calls += 1
        result = original(claim, spans)
        if calls == 2:
            object.__setattr__(result, "final_frame", 9)
        return result

    monkeypatch.setattr(mod, "_TRANSCRIPT_FN", drift)
    with pytest.raises(mod.OfflineObservationTranscriptRejected, match="replaced"):
        _join(image, audio, segments, retained)
    assert calls == 0


def test_original_pair_inspector_swap_is_rejected(monkeypatch):
    image, audio, segments, retained = _case()
    monkeypatch.setattr(
        pair_mod, "inspect_disconnected_observation_pair", lambda *a, **kw: None,
    )
    with pytest.raises(mod.OfflineObservationTranscriptRejected, match="replaced"):
        _join(image, audio, segments, retained)
