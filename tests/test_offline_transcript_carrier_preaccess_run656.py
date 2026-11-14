"""Disconnected private-transcript carrier preaccess and reentrancy cases.

Only synthetic in-memory text and audio metadata are used; neither real ASR
nor microphone/camera capture, consent, identity or tool dispatch is implied.
"""

import hashlib
from contextlib import contextmanager

import pytest

import ark.offline_transcript_binding as module
from ark.offline_transcript_binding import (
    AudioMetadataClaim,
    TranscriptBindingPreview,
    TranscriptBindingRejected,
    TranscriptSegmentClaim,
    review_audio_transcript_binding,
)


def _case():
    audio = AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, 16000, 16000)
    text = "fixture text"
    segment = TranscriptSegmentClaim(
        0, 100, "en", hashlib.sha256(text.encode("utf-8")).hexdigest(), text,
    )
    return audio, (segment,)


@contextmanager
def _poison(cls, name, calls):
    missing = object()
    old = vars(cls).get(name, missing)

    def hostile(*_args, **_kwargs):
        calls.append(name)
        raise AssertionError("private transcript accessor executed")

    descriptor = (
        property(hostile)
        if name not in ("__init__", "__getattribute__", "__getattr__")
        else hostile
    )
    setattr(cls, name, descriptor)
    try:
        yield
    finally:
        # Restoring a class dictionary entry avoids inherited descriptor
        # leaks into unrelated test modules. Do not mutate __new__ in pytest.
        if old is missing:
            delattr(cls, name)
        else:
            setattr(cls, name, old)


_MEMBERS = (
    (AudioMetadataClaim, "owner_sha256"),
    (AudioMetadataClaim, "scope_sha256"),
    (AudioMetadataClaim, "audio_sha256"),
    (AudioMetadataClaim, "sample_rate_hz"),
    (AudioMetadataClaim, "frame_count"),
    (TranscriptSegmentClaim, "start_frame"),
    (TranscriptSegmentClaim, "end_frame"),
    (TranscriptSegmentClaim, "language"),
    (TranscriptSegmentClaim, "text_sha256"),
    (TranscriptSegmentClaim, "text"),
    (TranscriptBindingPreview, "fingerprint"),
    (TranscriptBindingPreview, "segment_count"),
    (TranscriptBindingPreview, "total_text_bytes"),
    (TranscriptBindingPreview, "first_frame"),
    (TranscriptBindingPreview, "final_frame"),
    (TranscriptBindingPreview, "audio_sha256"),
) + tuple(
    (cls, name)
    for cls in (
        AudioMetadataClaim, TranscriptSegmentClaim, TranscriptBindingPreview,
    )
    for name in ("__init__", "__getattribute__", "__getattr__")
)


@pytest.mark.parametrize(("cls", "member"), _MEMBERS)
def test_private_transcript_carrier_poison_rejected_before_first_read(
    cls, member,
):
    audio, segments = _case()
    touched = []
    with _poison(cls, member, touched):
        with pytest.raises(
            TranscriptBindingRejected,
            match="transcript carrier definition changed",
        ):
            review_audio_transcript_binding(audio, segments)
    assert touched == []


@pytest.mark.parametrize(
    ("cls", "member"),
    (
        (AudioMetadataClaim, "owner_sha256"),
        (TranscriptSegmentClaim, "text"),
        (TranscriptBindingPreview, "fingerprint"),
    ),
)
def test_reentrant_text_hash_cannot_install_forged_carrier(
    monkeypatch, cls, member,
):
    audio, segments = _case()
    original = module._safe_text
    touched = []

    def hooked(text):
        raw = original(text)
        monkeypatch.setattr(cls, member, property(
            lambda *_args: touched.append("hostile"),
        ))
        return raw

    monkeypatch.setattr(module, "_safe_text", hooked)
    with pytest.raises(
        TranscriptBindingRejected, match="transcript carrier definition changed",
    ):
        review_audio_transcript_binding(audio, segments)
    assert touched == []


def test_original_transcript_bindings_remain_non_authoritative():
    audio, segments = _case()
    result = review_audio_transcript_binding(audio, segments)
    assert result.segment_count == 1
    assert result.audio_sha256 == audio.audio_sha256
    assert result.user_consent_proven is False
    assert result.tool_execution_authorized is False
    assert segments[0].text not in repr(result)
