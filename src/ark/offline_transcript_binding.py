"""Detached, non-authoritative transcript-to-audio metadata binding.

Synthetic caller-supplied transcript text and audio checksums are untrusted.
This does not read audio, run ASR, identify speakers, grant Tool permission, or
establish user consent. Returned metadata never contains transcript text.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_INT = 2**63 - 1
_MAX_SEGMENTS = 64
_MAX_SEGMENT_BYTES = 2048
_MAX_TOTAL_BYTES = 8192
_MAX_DURATION_SECONDS = 120
_RATES = frozenset((8000, 16000, 22050, 32000, 44100, 48000))
_LANGUAGES = frozenset(("ja", "en", "und"))
_DOMAIN = b"ARK-detached-audio-transcript-binding-v1\0"


class TranscriptBindingRejected(ValueError):
    """Malformed or temporally inconsistent synthetic transcript claim."""


@dataclass(frozen=True, slots=True)
class AudioMetadataClaim:
    owner_sha256: str
    scope_sha256: str
    audio_sha256: str
    sample_rate_hz: int
    frame_count: int


@dataclass(frozen=True, slots=True)
class TranscriptSegmentClaim:
    start_frame: int
    end_frame: int
    language: str
    text_sha256: str
    text: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class TranscriptBindingPreview:
    fingerprint: str
    segment_count: int
    total_text_bytes: int
    first_frame: int
    final_frame: int
    audio_sha256: str

    @property
    def audio_or_transcript_authenticated(self) -> bool:
        return False

    @property
    def user_consent_proven(self) -> bool:
        return False

    @property
    def asr_verified(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


def _hash(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _safe_text(value: object) -> bytes:
    if type(value) is not str or not value or value != value.strip():
        raise TranscriptBindingRejected("empty or untrimmed transcript")
    if unicodedata.normalize("NFC", value) != value:
        raise TranscriptBindingRejected("transcript must already be canonical NFC")
    # Reject hidden format controls, bidi overrides, lone surrogates and C0/C1 controls.
    if any(unicodedata.category(char) in ("Cc", "Cf", "Cs") for char in value):
        raise TranscriptBindingRejected("unsafe transcript control character")
    data = value.encode("utf-8")
    if len(data) > _MAX_SEGMENT_BYTES:
        raise TranscriptBindingRejected("transcript segment budget exceeded")
    return data


def review_audio_transcript_binding(
    audio: AudioMetadataClaim, segments: tuple[TranscriptSegmentClaim, ...],
) -> TranscriptBindingPreview:
    """Bind bounded synthetic text to frame intervals without any side effects."""
    if type(audio) is not AudioMetadataClaim or type(segments) is not tuple:
        raise TranscriptBindingRejected("exact audio and segment carrier types required")
    if not 1 <= len(segments) <= _MAX_SEGMENTS:
        raise TranscriptBindingRejected("empty or over-budget transcript")
    if any(type(item) is not TranscriptSegmentClaim for item in segments):
        raise TranscriptBindingRejected("exact transcript segment type required")
    audio_fields = (
        audio.owner_sha256, audio.scope_sha256, audio.audio_sha256,
        audio.sample_rate_hz, audio.frame_count,
    )
    if (
        not all(_hash(digest) for digest in audio_fields[:3])
        or type(audio_fields[3]) is not int or audio_fields[3] not in _RATES
        or type(audio_fields[4]) is not int
        or not 1 <= audio_fields[4] <= min(_MAX_INT, audio_fields[3] * _MAX_DURATION_SECONDS)
    ):
        raise TranscriptBindingRejected("malformed claimed audio metadata")
    original_segments = tuple(segments)
    saved = tuple((item, item.start_frame, item.end_frame, item.language,
                   item.text_sha256, item.text) for item in original_segments)

    def assert_epoch() -> None:
        current_audio = (
            audio.owner_sha256, audio.scope_sha256, audio.audio_sha256,
            audio.sample_rate_hz, audio.frame_count,
        )
        if any(a is not b for a, b in zip(current_audio, audio_fields, strict=True)):
            raise TranscriptBindingRejected("audio carrier changed during review")
        if len(segments) != len(saved) or any(
            segments[i] is not saved[i][0]
            or any(now is not pinned for now, pinned in zip(
                (saved[i][0].start_frame, saved[i][0].end_frame,
                 saved[i][0].language, saved[i][0].text_sha256, saved[i][0].text),
                saved[i][1:], strict=True,
            )) for i in range(len(saved))
        ):
            raise TranscriptBindingRejected("transcript carrier changed during review")

    assert_epoch()
    previous_end = 0
    total_bytes = 0
    envelope: list[tuple[int, int, str, str]] = []
    for _, start, end, lang, digest, text in saved:
        if (
            type(start) is not int or type(end) is not int
            or not previous_end <= start < end <= audio_fields[4]
            or type(lang) is not str or lang not in _LANGUAGES
            or not _hash(digest)
        ):
            raise TranscriptBindingRejected("invalid transcript interval or language")
        raw = _safe_text(text)
        assert_epoch()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise TranscriptBindingRejected("transcript checksum mismatch")
        total_bytes += len(raw)
        if total_bytes > _MAX_TOTAL_BYTES:
            raise TranscriptBindingRejected("total transcript budget exceeded")
        envelope.append((start, end, lang, digest))
        previous_end = end
    assert_epoch()
    payload = json.dumps(
        [audio_fields, envelope], ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    fingerprint = hashlib.sha256(_DOMAIN + payload).hexdigest()
    assert_epoch()
    return TranscriptBindingPreview(
        fingerprint, len(saved), total_bytes, saved[0][1], previous_end, audio_fields[2],
    )
