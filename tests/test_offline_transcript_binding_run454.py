"""Frame-indexed transcript metadata must remain non-authoritative."""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError

import pytest

from ark.offline_transcript_binding import (
    AudioMetadataClaim,
    TranscriptBindingRejected,
    TranscriptSegmentClaim,
    review_audio_transcript_binding,
)


def audio(*, frames=16000, rate=16000):
    return AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, rate, frames)


def segment(text="こんにちは", *, start=0, end=100, language="ja"):
    return TranscriptSegmentClaim(
        start, end, language, hashlib.sha256(text.encode("utf-8")).hexdigest(), text,
    )


def test_bind_and_never_grant_permissions():
    item = segment()
    result = review_audio_transcript_binding(audio(), (item,))
    assert result.segment_count == 1
    assert result.total_text_bytes == len(item.text.encode("utf-8"))
    assert result.first_frame == 0 and result.final_frame == 100
    assert result.audio_sha256 == "c" * 64
    assert len(result.fingerprint) == 64
    assert not result.audio_or_transcript_authenticated
    assert not result.user_consent_proven
    assert not result.asr_verified
    assert not result.tool_execution_authorized
    assert item.text not in repr(item)
    assert item.text not in repr(result)
    with pytest.raises(FrozenInstanceError):
        result.fingerprint = "fake"


def test_input_order_and_text_changes_affect_digest():
    one = review_audio_transcript_binding(audio(), (segment("a"), segment("b", start=100, end=200)))
    two = review_audio_transcript_binding(audio(), (segment("b"), segment("a", start=100, end=200)))
    three = review_audio_transcript_binding(
        audio(frames=16001), (segment("a"), segment("b", start=100, end=200)),
    )
    assert one.fingerprint != two.fingerprint
    assert one.fingerprint != three.fingerprint
    assert one.fingerprint == review_audio_transcript_binding(
        audio(), (segment("a"), segment("b", start=100, end=200)),
    ).fingerprint


@pytest.mark.parametrize("bad", [
    AudioMetadataClaim("A" * 64, "b" * 64, "c" * 64, 16000, 100),
    AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, True, 100),
    AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, 1234, 100),
    AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, 16000, 0),
    AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, 16000, True),
    AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, 16000, 16000 * 121),
    AudioMetadataClaim("a" * 64, "b" * 64, "c" * 64, 16000, 2**63),
])
def test_invalid_audio_metadata(bad):
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(bad, (segment(),))


@pytest.mark.parametrize("bad", [
    TranscriptSegmentClaim(0, 10, "en", "x" * 64, "hello"),
    segment(start=10, end=10), segment(start=-1), segment(start=True),
    segment(end=16001), segment(end=False), segment(language="EN"),
    segment(text=" hello"), segment(text=" "), segment(text="\u202eB"),
    segment(text="\x00hello"), TranscriptSegmentClaim(0, 100, "ja", "a" * 64, "\ud800"),
    segment(text="e\u0301"), segment(text="x" * 2049),
])
def test_invalid_segments(bad):
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(audio(), (bad,))


def test_reorder_overlap_and_large_envelopes():
    with pytest.raises(TranscriptBindingRejected, match="interval"):
        review_audio_transcript_binding(
            audio(), (segment(start=100, end=200), segment(start=199, end=300)),
        )
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(audio(), ())
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(audio(), tuple(segment("x") for _ in range(65)))
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(
            audio(frames=10000), tuple(
                segment("あ" * 500, start=i * 100, end=i * 100 + 100)
                for i in range(6)
            ),
        )


def test_individual_boundaries_and_nested_carriers():
    result = review_audio_transcript_binding(
        audio(frames=32000),
        (segment("Hi", end=200, language="en"),
         segment("はい", start=200, end=32000, language="ja")),
    )
    assert result.final_frame == 32000
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(audio(), [segment()])
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(audio(), (object(),))
    with pytest.raises(TranscriptBindingRejected):
        review_audio_transcript_binding(None, (segment(),))
