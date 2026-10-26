"""Metadata-only timeline fixture validation; no microphone or transcript text."""

from dataclasses import replace

import pytest

from ark import transcript_timeline_fixture as mod


SHA_A = "a" * 64
SHA_B = "b" * 64
SESSION = "session_" + "c" * 16
SPEAKER = "speaker_" + "d" * 8


def span(start=100, end=200, *, confidence=900_000, speaker=SPEAKER):
    return mod.TranscriptSpan(start, end, confidence, speaker, SHA_B)


def timeline(rows=None, *, duration=1_000, expected=None):
    if rows is None:
        rows = (span(), span(300, 500, speaker=None))
    return mod.TranscriptTimelineFixture(
        SESSION, SHA_A, SHA_B, SHA_A, duration,
        len(rows) if expected is None else expected, rows,
    )


def test_canonical_timeline_review():
    review = mod.review_transcript_timeline(timeline())
    assert review.span_count == 2
    assert review.speech_duration_ms == 300
    assert review.gap_duration_ms == 700
    assert review.reported_speaker_count == 1
    assert len(review.timeline_sha256) == 64
    assert not review.consent_verified
    assert not review.audio_source_authenticated
    assert not review.speaker_identity_verified
    assert not review.external_action_authorized


def test_empty_silent_clip_supported():
    result = mod.review_transcript_timeline(timeline((), duration=200))
    assert result.span_count == 0
    assert result.speech_duration_ms == 0
    assert result.gap_duration_ms == 200


def test_abutting_spans_and_zero_silence():
    result = mod.review_transcript_timeline(
        timeline((span(0, 500), span(500, 1_000)), duration=1_000)
    )
    assert result.speech_duration_ms == 1_000
    assert result.gap_duration_ms == 0


def test_deterministic_separation_of_owner():
    a = timeline()
    assert mod.review_transcript_timeline(a) == mod.review_transcript_timeline(a)
    other = replace(a, owner_sha256=SHA_B)
    assert mod.review_transcript_timeline(a).timeline_sha256 != (
        mod.review_transcript_timeline(other).timeline_sha256
    )


@pytest.mark.parametrize("rows", [
    (span(100, 500), span(400, 700)),
    (span(100, 500), span(50, 100)),
    (span(100, 100),),
    (span(-1, 100),),
    (span(0, 1_001),),
])
def test_invalid_temporal_boundaries_rejected(rows):
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(timeline(rows))


@pytest.mark.parametrize("confidence", [-1, 1_000_001, 1.0, True, "100", None])
def test_invalid_confidence_denied(confidence):
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(timeline((span(confidence=confidence),)))


def test_wrong_speaker_identity_shape_denied():
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(timeline((span(speaker="Jane"),)))


def test_exact_expected_span_count_required():
    with pytest.raises(mod.TranscriptTimelineRejected, match="count"):
        mod.review_transcript_timeline(timeline(expected=3))


def test_wrong_row_type_denied():
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(timeline(("not a span",)))


def test_non_tuple_rows_denied():
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(timeline([span()]))


def test_excessive_span_count_denied():
    with pytest.raises(mod.TranscriptTimelineRejected, match="unbounded"):
        mod.review_transcript_timeline(timeline((span(0, 1),) * 513))


def test_excessive_clip_duration_denied():
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(timeline((), duration=7_200_001))


@pytest.mark.parametrize("field", ["owner_sha256", "privacy_sha256", "audio_sha256"])
def test_invalid_owner_privacy_audio_digests(field):
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(replace(timeline(), **{field: "not_sha"}))


def test_wrong_session_id_denied():
    with pytest.raises(mod.TranscriptTimelineRejected):
        mod.review_transcript_timeline(replace(timeline(), session_id="invalid"))


def test_changed_row_during_hash_denied(monkeypatch):
    subject = timeline()
    original_hash = mod.hashlib.sha256
    triggered = False

    def tamper(data=b""):
        nonlocal triggered
        if not triggered:
            triggered = True
            object.__setattr__(subject.spans[0], "speaker_id", "speaker_" + "e" * 8)
        return original_hash(data)

    monkeypatch.setattr(mod.hashlib, "sha256", tamper)
    with pytest.raises(mod.TranscriptTimelineRejected, match="carrier changed"):
        mod.review_transcript_timeline(subject)


def test_no_raw_transcript_text_or_audio_in_result():
    review = mod.review_transcript_timeline(timeline())
    assert not hasattr(review, "raw_audio")
    assert not hasattr(review, "transcript")
    assert not hasattr(review, "dispatch")
