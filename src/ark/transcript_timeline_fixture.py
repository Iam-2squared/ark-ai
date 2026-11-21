"""Metadata-only, disconnected transcript timing and diarization review.

The rows come from untrusted fixtures: this does not recognize speech, record
microphones, identify real speakers, calibrate confidence, or authorize reuse.
No transcript text or raw audio is consumed or returned.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SESSION = re.compile(r"session_[0-9a-f]{16}\Z")
_SPEAKER = re.compile(r"speaker_[0-9a-f]{8}\Z")
_DOMAIN = b"ARK-detached-transcript-timeline-v1\0"
_MAX_DURATION_MS = 7_200_000
_MAX_SPANS = 512
_MAX_TIME = 2**63 - 1


class TranscriptTimelineRejected(ValueError):
    """Synthetic transcript timing, identity or duration is inconsistent."""


@dataclass(frozen=True, slots=True)
class TranscriptSpan:
    start_ms: int
    end_ms: int
    confidence_ppm: int
    speaker_id: str | None
    text_sha256: str


@dataclass(frozen=True, slots=True)
class TranscriptTimelineFixture:
    session_id: str
    owner_sha256: str
    privacy_sha256: str
    audio_sha256: str
    clip_duration_ms: int
    expected_span_count: int
    spans: tuple[TranscriptSpan, ...]


@dataclass(frozen=True, slots=True)
class TranscriptTimelineReview:
    span_count: int
    speech_duration_ms: int
    gap_duration_ms: int
    reported_speaker_count: int
    timeline_sha256: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def audio_source_authenticated(self) -> bool:
        return False

    @property
    def speaker_identity_verified(self) -> bool:
        return False

    @property
    def external_action_authorized(self) -> bool:
        return False


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def review_transcript_timeline(
    fixture: TranscriptTimelineFixture,
) -> TranscriptTimelineReview:
    """Reject overlapping, missing and impossible time-coded transcript rows."""
    if type(fixture) is not TranscriptTimelineFixture:
        raise TranscriptTimelineRejected("exact fixture required")
    original = (
        fixture.session_id, fixture.owner_sha256, fixture.privacy_sha256,
        fixture.audio_sha256, fixture.clip_duration_ms,
        fixture.expected_span_count, fixture.spans,
    )
    if type(fixture.spans) is not tuple or len(fixture.spans) > _MAX_SPANS:
        raise TranscriptTimelineRejected("unbounded transcript spans")
    rows = tuple(fixture.spans)
    pinned = tuple(
        (row.start_ms, row.end_ms, row.confidence_ppm,
         row.speaker_id, row.text_sha256)
        if type(row) is TranscriptSpan else None
        for row in rows
    )

    def check_epoch() -> None:
        values = (
            fixture.session_id, fixture.owner_sha256, fixture.privacy_sha256,
            fixture.audio_sha256, fixture.clip_duration_ms,
            fixture.expected_span_count, fixture.spans,
        )
        if (
            any(a is not b for a, b in zip(values, original, strict=True))
            or any(row is not fixture.spans[index] for index, row in enumerate(rows))
            or any(
                type(row) is not TranscriptSpan
                or any(a is not b for a, b in zip(
                    (row.start_ms, row.end_ms, row.confidence_ppm,
                     row.speaker_id, row.text_sha256), pinned[index], strict=True,
                ))
                for index, row in enumerate(rows)
            )
        ):
            raise TranscriptTimelineRejected("transcript carrier changed during review")

    check_epoch()
    session, owner, privacy, audio, duration, expected, _ = original
    if (
        type(session) is not str or _SESSION.fullmatch(session) is None
        or not all(_sha(x) for x in (owner, privacy, audio))
        or type(duration) is not int or not 0 <= duration <= _MAX_DURATION_MS
        or type(expected) is not int or expected != len(rows)
    ):
        raise TranscriptTimelineRejected("invalid clip identity or complete row count")
    elapsed = 0
    previous_end = 0
    speakers: set[str] = set()
    for start, end, confidence, speaker, digest in pinned:
        check_epoch()
        if (
            type(start) is not int or type(end) is not int
            or not 0 <= previous_end <= start < end <= duration <= _MAX_TIME
            or type(confidence) is not int or not 0 <= confidence <= 1_000_000
            or (speaker is not None and (
                type(speaker) is not str or _SPEAKER.fullmatch(speaker) is None
            ))
            or not _sha(digest)
        ):
            raise TranscriptTimelineRejected("invalid, overlapping or forged span")
        elapsed += end - start
        previous_end = end
        if speaker is not None:
            speakers.add(speaker)
        check_epoch()
    payload = json.dumps(
        {
            "session": session, "owner": owner, "privacy": privacy,
            "audio": audio, "duration": duration, "expected": expected,
            "spans": pinned,
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    if len(payload) > 90_000:
        raise TranscriptTimelineRejected("bounded timeline manifest exceeded")
    check_epoch()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    check_epoch()
    review = TranscriptTimelineReview(
        len(rows), elapsed, duration - elapsed, len(speakers), digest,
    )
    check_epoch()
    if (
        type(review) is not TranscriptTimelineReview
        or type(review.span_count) is not int or review.span_count != len(rows)
        or review.speech_duration_ms != elapsed
        or review.gap_duration_ms != duration - elapsed
        or review.reported_speaker_count != len(speakers)
        or review.timeline_sha256 != digest
    ):
        raise TranscriptTimelineRejected("timeline result changed during construction")
    return review
