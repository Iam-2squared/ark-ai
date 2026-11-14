"""Bounded detached transcript timeline coverage from local PNG/WAV fixtures.

This is interval accounting, NOT speech recognition, consent, device origin,
a trustworthy clock, or an authorization to act. No text, pixels or samples
appear in the result. All retained hashes are caller claims.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import offline_observation_pair as pair_module
from . import offline_observation_transcript as transcript_module
from . import offline_pcm_wav as wave_module
from . import offline_png_inventory as png_module
from . import offline_transcript_binding as binding_module
from .offline_pcm_wav import OfflineWaveRequest
from .offline_png_inventory import OfflinePngRequest
from .offline_transcript_binding import TranscriptSegmentClaim

_JOIN = transcript_module.review_disconnected_observation_transcript
_PAIR = pair_module.inspect_disconnected_observation_pair
_PAIR_TYPE = pair_module.OfflineObservationPair
_JOIN_TYPE = transcript_module.OfflineObservationTranscript
_DOMAIN = b"ARK-disconnected-transcript-coverage-v2\0"
_DENIALS = (
    "speech_verified", "user_consent_verified", "camera_authenticated",
    "microphone_authenticated", "external_disclosure_authorized",
    "tool_execution_authorized",
)


class OfflineCoverageRejected(ValueError):
    """Coverage cannot be established from these exact detached claims."""


@dataclass(frozen=True, slots=True)
class OfflineTranscriptCoverage:
    observation_sha256: str
    transcript_fingerprint: str
    audio_frames: int
    covered_frames: int
    leading_gap_frames: int
    interior_gap_frames: int
    trailing_gap_frames: int
    coverage_ppm: int
    uncovered_run_count: int
    longest_uncovered_run_frames: int
    coverage_sha256: str

    @property
    def speech_verified(self) -> bool:
        return False

    @property
    def user_consent_verified(self) -> bool:
        return False

    @property
    def camera_authenticated(self) -> bool:
        return False

    @property
    def microphone_authenticated(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT = OfflineTranscriptCoverage
_RESULT_DENIALS = tuple(getattr(_RESULT, name) for name in _DENIALS)
_PAIR_DENIALS = (
    "camera_provenance_verified", "microphone_provenance_verified",
    "consent_verified", "external_disclosure_authorized",
    "tool_execution_authorized",
)
_JOIN_DENIALS = (
    "source_authenticated", "consent_verified", "asr_verified",
    "external_disclosure_authorized", "tool_execution_authorized",
)
_PAIR_PROPS = tuple(getattr(_PAIR_TYPE, name) for name in _PAIR_DENIALS)
_JOIN_PROPS = tuple(getattr(_JOIN_TYPE, name) for name in _JOIN_DENIALS)


_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_PNG_GUARD = png_module._require_original_png_authority
_ORIGINAL_WAVE_GUARD = wave_module._require_original_wave_authority
_ORIGINAL_SEGMENT_GUARD = binding_module._assert_original_binding_carriers


def _require_original_coverage_ingress() -> None:
    """Guard private image/audio/text carriers BEFORE reading any fields.

    The underlying parsers already pin their input class slots at import
    time. Invoke those original guards rather than capturing a potentially
    poisoned new baseline in this higher-level coverage adapter.
    """
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or png_module._require_original_png_authority is not _ORIGINAL_PNG_GUARD
        or wave_module._require_original_wave_authority is not _ORIGINAL_WAVE_GUARD
        or binding_module._assert_original_binding_carriers is not _ORIGINAL_SEGMENT_GUARD
    ):
        raise OfflineCoverageRejected("coverage private ingress dependencies changed")
    try:
        _ORIGINAL_PNG_GUARD()
        _ORIGINAL_WAVE_GUARD()
        _ORIGINAL_SEGMENT_GUARD()
    except (
        png_module.OfflinePngRejected,
        wave_module.OfflineWaveRejected,
        binding_module.TranscriptBindingRejected,
    ) as exc:
        raise OfflineCoverageRejected("coverage private ingress carriers changed") from exc


def review_disconnected_transcript_coverage(
    image: OfflinePngRequest,
    audio: OfflineWaveRequest,
    segments: tuple[TranscriptSegmentClaim, ...],
    *,
    retained_owner_sha256: str,
    retained_privacy_sha256: str,
    retained_png_sha256: str,
    retained_wav_sha256: str,
    retained_transcript_fingerprint: str,
) -> OfflineTranscriptCoverage:
    """Account for non-overlapping claimed frame spans after strict media review.

    Total/covered/gap frames refer only to a caller-provided WAV fixture.
    Coverage says nothing about whether audio actually contains speech.
    """
    if (
        type(image) is not OfflinePngRequest
        or type(audio) is not OfflineWaveRequest
        or type(segments) is not tuple
        or not 1 <= len(segments) <= 64
        or any(type(span) is not TranscriptSegmentClaim for span in segments)
    ):
        raise OfflineCoverageRejected("exact bounded coverage fixture required")
    _require_original_coverage_ingress()
    retained = (
        retained_owner_sha256, retained_privacy_sha256, retained_png_sha256,
        retained_wav_sha256, retained_transcript_fingerprint,
    )
    image_fields = (
        image.owner_sha256, image.privacy_sha256, image.source_sha256,
        image.png_bytes,
    )
    audio_fields = (
        audio.owner_sha256, audio.privacy_sha256, audio.wav_sha256,
        audio.wav_bytes,
    )
    spans = tuple((
        span, span.start_frame, span.end_frame, span.language,
        span.text_sha256, span.text,
    ) for span in segments)

    def stable() -> None:
        _require_original_coverage_ingress()
        if (
            transcript_module.review_disconnected_observation_transcript is not _JOIN
            or pair_module.inspect_disconnected_observation_pair is not _PAIR
            or any(getattr(_RESULT, name) is not old for name, old in zip(
                _DENIALS, _RESULT_DENIALS, strict=True,
            ))
            or any(getattr(_PAIR_TYPE, name) is not old for name, old in zip(
                _PAIR_DENIALS, _PAIR_PROPS, strict=True,
            ))
            or any(getattr(_JOIN_TYPE, name) is not old for name, old in zip(
                _JOIN_DENIALS, _JOIN_PROPS, strict=True,
            ))
        ):
            raise OfflineCoverageRejected("coverage authority implementation changed")
        if (
            type(image) is not OfflinePngRequest
            or type(audio) is not OfflineWaveRequest
            or len(segments) != len(spans)
            or any(now is not old for now, old in zip(
                (
                    image.owner_sha256, image.privacy_sha256, image.source_sha256,
                    image.png_bytes,
                ), image_fields, strict=True,
            ))
            or any(now is not old for now, old in zip(
                (
                    audio.owner_sha256, audio.privacy_sha256, audio.wav_sha256,
                    audio.wav_bytes,
                ), audio_fields, strict=True,
            ))
            or any(
                segments[i] is not saved[0]
                or any(now is not old for now, old in zip((
                    saved[0].start_frame, saved[0].end_frame,
                    saved[0].language, saved[0].text_sha256, saved[0].text,
                ), saved[1:], strict=True))
                for i, saved in enumerate(spans)
            )
        ):
            raise OfflineCoverageRejected("coverage fixture changed during review")

    def measure() -> tuple[str, str, int, int, int, int, int, int, int, int]:
        stable()
        try:
            joined = _JOIN(
                image, audio, segments, retained_owner_sha256=retained[0],
                retained_privacy_sha256=retained[1],
                retained_png_sha256=retained[2],
                retained_wav_sha256=retained[3],
                retained_transcript_fingerprint=retained[4],
            )
            stable()
            pair = _PAIR(
                image, audio, retained_owner_sha256=retained[0],
                retained_privacy_sha256=retained[1],
                retained_png_sha256=retained[2],
                retained_wav_sha256=retained[3],
            )
            stable()
        except (
            transcript_module.OfflineObservationTranscriptRejected,
            pair_module.OfflineObservationPairRejected,
        ) as exc:
            raise OfflineCoverageRejected("underlying media claim rejected") from exc
        if type(joined) is not _JOIN_TYPE or type(pair) is not _PAIR_TYPE:
            raise OfflineCoverageRejected("invalid exact coverage inputs")
        pair_values = (
            pair.pair_sha256, pair.wav_sha256, pair.audio_frames,
        )
        join_values = (
            joined.pair_sha256, joined.transcript_fingerprint,
            joined.segment_count, joined.first_frame, joined.final_frame,
            joined.envelope_sha256,
        )
        if (
            pair_values[0] != join_values[0]
            or pair_values[1] != retained[3]
            or join_values[1] != retained[4]
            or join_values[2] != len(spans)
        ):
            raise OfflineCoverageRejected("cross-layer receipt mismatch")
        for report, names in ((joined, _JOIN_DENIALS), (pair, _PAIR_DENIALS)):
            for name in names:
                if getattr(report, name) is not False:
                    raise OfflineCoverageRejected("coverage input gained authority")
                stable()
        if (
            tuple((pair.pair_sha256, pair.wav_sha256, pair.audio_frames))
            != pair_values
            or (
                joined.pair_sha256, joined.transcript_fingerprint,
                joined.segment_count, joined.first_frame, joined.final_frame,
                joined.envelope_sha256,
            ) != join_values
        ):
            raise OfflineCoverageRejected("coverage report drifted")
        total = pair_values[2]
        if type(total) is not int or total <= 0:
            raise OfflineCoverageRejected("invalid audio frame count")
        starts = [saved[1] for saved in spans]
        ends = [saved[2] for saved in spans]
        if (
            any(type(n) is not int for n in (*starts, *ends))
            or starts[0] != join_values[3] or ends[-1] != join_values[4]
            or not 0 <= starts[0] < ends[0] <= total
            or any(not ends[i - 1] <= starts[i] < ends[i] <= total
                   for i in range(1, len(spans)))
        ):
            raise OfflineCoverageRejected("invalid frame coverage intervals")
        covered = sum(end - start for start, end in zip(starts, ends, strict=True))
        leading = starts[0]
        interior = sum(starts[i] - ends[i - 1] for i in range(1, len(spans)))
        trailing = total - ends[-1]
        gaps = (leading, *(starts[i] - ends[i - 1]
                           for i in range(1, len(spans))), trailing)
        uncovered_runs = sum(gap > 0 for gap in gaps)
        longest_gap = max(gaps)
        if covered + leading + interior + trailing != total:
            raise OfflineCoverageRejected("inconsistent frame accounting")
        stable()
        return (
            join_values[5], join_values[1], total, covered, leading,
            interior, trailing, covered * 1_000_000 // total,
            uncovered_runs, longest_gap,
        )

    first = measure()
    if measure() != first:
        raise OfflineCoverageRejected("coverage drifted between inspections")
    stable()
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(first, separators=(",", ":"), ensure_ascii=True)
        .encode("ascii")
    ).hexdigest()
    stable()
    result = _RESULT(*first, digest)
    expected = (*first, digest)
    names = (
        "observation_sha256", "transcript_fingerprint", "audio_frames",
        "covered_frames", "leading_gap_frames", "interior_gap_frames",
        "trailing_gap_frames", "coverage_ppm", "uncovered_run_count",
        "longest_uncovered_run_frames", "coverage_sha256",
    )
    for denial in _DENIALS:
        if (
            type(result) is not _RESULT
            or any(now is not old for now, old in zip(
                tuple(getattr(result, name) for name in names),
                expected, strict=True,
            ))
            or getattr(result, denial) is not False
        ):
            raise OfflineCoverageRejected("coverage output gained authority")
        stable()
    return result
