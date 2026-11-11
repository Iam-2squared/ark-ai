"""Offline alignment of verified PCM region spans and synthetic transcript spans.

Region spans can include bridged silence; their overlap with claimed text
intervals is NOT speech recognition, consent, audio provenance or authority.
All inputs are caller fixtures. No audio samples or transcript text are returned.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import offline_pcm_activity_regions as activity_module
from . import offline_transcript_binding as binding_module

_ACTIVITY_VERIFY = activity_module.verify_activity_regions
_TRANSCRIPT_REVIEW = binding_module.review_audio_transcript_binding
_ACTIVITY_TYPE = activity_module.ActivityRegions
_REGION_TYPE = activity_module.ActivityRegion
_AUDIO_TYPE = binding_module.AudioMetadataClaim
_SEGMENT_TYPE = binding_module.TranscriptSegmentClaim
_PREVIEW_TYPE = binding_module.TranscriptBindingPreview
_DOMAIN = b"ARK-offline-activity-transcript-overlap-v1\0"
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


class OfflineAlignmentRejected(ValueError):
    """The local, non-authoritative alignment is not reproducible."""


@dataclass(frozen=True, slots=True)
class OfflineActivityTranscriptOverlap:
    pcm_sha256: str
    transcript_fingerprint: str
    activity_region_count: int
    transcript_segment_count: int
    region_span_samples: int
    transcript_overlap_samples: int
    uncovered_region_span_samples: int
    regions_with_overlap: int
    overlap_ppm: int
    alignment_sha256: str

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def speech_verified(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT_TYPE = OfflineActivityTranscriptOverlap
_DENIALS = (
    "source_authenticated", "consent_verified", "speech_verified",
    "tool_execution_authorized",
)
_RESULT_PROPS = tuple(vars(_RESULT_TYPE)[name] for name in _DENIALS)
_PREVIEW_DENIALS = (
    "audio_or_transcript_authenticated", "user_consent_proven",
    "asr_verified", "tool_execution_authorized",
)
_PREVIEW_PROPS = tuple(vars(_PREVIEW_TYPE)[name] for name in _PREVIEW_DENIALS)
# A frozen result's slots/constructor are still mutable at class level.
_RESULT_FIELDS = (
    "pcm_sha256", "transcript_fingerprint", "activity_region_count",
    "transcript_segment_count", "region_span_samples",
    "transcript_overlap_samples", "uncovered_region_span_samples",
    "regions_with_overlap", "overlap_ppm", "alignment_sha256",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_ORIGINAL_RESULT_FIELDS = tuple(
    vars(_RESULT_TYPE).get(name) for name in _RESULT_FIELDS
)


def _originals() -> None:
    # Before any PCM byte reaches an activity verifier or a digest callback,
    # reject substituted serialization, domain, verifier and result carriers.
    # This is local fault-injection protection, not audio/source attestation.
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or OfflineActivityTranscriptOverlap is not _RESULT_TYPE
        or activity_module.verify_activity_regions is not _ACTIVITY_VERIFY
        or binding_module.review_audio_transcript_binding is not _TRANSCRIPT_REVIEW
        or activity_module.ActivityRegions is not _ACTIVITY_TYPE
        or activity_module.ActivityRegion is not _REGION_TYPE
        or binding_module.AudioMetadataClaim is not _AUDIO_TYPE
        or binding_module.TranscriptSegmentClaim is not _SEGMENT_TYPE
        or binding_module.TranscriptBindingPreview is not _PREVIEW_TYPE
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS, strict=True,
            )
        )
        or any(vars(_RESULT_TYPE).get(name) is not old for name, old in zip(
            _DENIALS, _RESULT_PROPS, strict=True,
        ))
        or any(vars(_PREVIEW_TYPE).get(name) is not old for name, old in zip(
            _PREVIEW_DENIALS, _PREVIEW_PROPS, strict=True,
        ))
    ):
        raise OfflineAlignmentRejected("original alignment authority changed")


def review_offline_activity_transcript_overlap(
    pcm: bytes,
    expected_pcm_sha256: str,
    activity: activity_module.ActivityRegions,
    audio: binding_module.AudioMetadataClaim,
    segments: tuple[binding_module.TranscriptSegmentClaim, ...],
    *,
    retained_transcript_fingerprint: str,
    frame_ms: int = 20,
    rms_threshold: int = 512,
    bridge_silence_frames: int = 1,
    min_active_frames: int = 1,
    max_regions: int = 32,
) -> OfflineActivityTranscriptOverlap:
    """Recompute activity and transcript claims, then intersect their spans.

    Activity regions include bridged silent frames; the overlap percentage
    describes these spans, not verified speech or the truth of any transcript.
    Retained fingerprints must originate outside the caller's current fixture
    to detect coordinated rewrites. This is read-only and cannot dispatch.
    """
    _originals()
    if (
        type(pcm) is not bytes
        or type(activity) is not _ACTIVITY_TYPE
        or type(audio) is not _AUDIO_TYPE
        or type(segments) is not tuple
        or not 1 <= len(segments) <= 64
        or any(type(item) is not _SEGMENT_TYPE for item in segments)
        or type(expected_pcm_sha256) is not str
        or type(retained_transcript_fingerprint) is not str
    ):
        raise OfflineAlignmentRejected("exact local alignment inputs required")
    activity_fields = (
        activity.source_sha256, activity.sample_rate, activity.frame_samples,
        activity.total_samples, activity.active_frame_count, activity.regions,
    )
    audio_fields = (
        audio.owner_sha256, audio.scope_sha256, audio.audio_sha256,
        audio.sample_rate_hz, audio.frame_count,
    )
    # Retain every nested region's exact carrier and fields, not just the
    # immutable outer tuple. Frozen dataclasses can be reflected through
    # object.__setattr__, including during independent verifier callbacks.
    if type(activity_fields[5]) is not tuple or any(
        type(region) is not _REGION_TYPE for region in activity_fields[5]
    ):
        raise OfflineAlignmentRejected("exact activity region carriers required")
    region_epoch = tuple((
        region, region.start_frame, region.end_frame, region.start_sample,
        region.end_sample, region.active_frames,
    ) for region in activity_fields[5])
    segments_epoch = tuple((
        item, item.start_frame, item.end_frame, item.language,
        item.text_sha256, item.text,
    ) for item in segments)
    config = (
        frame_ms, rms_threshold, bridge_silence_frames,
        min_active_frames, max_regions,
    )

    def stable() -> None:
        _originals()
        if (
            activity_module.verify_activity_regions is not _ACTIVITY_VERIFY
            or binding_module.review_audio_transcript_binding is not _TRANSCRIPT_REVIEW
            or activity_module.ActivityRegions is not _ACTIVITY_TYPE
            or activity_module.ActivityRegion is not _REGION_TYPE
            or binding_module.AudioMetadataClaim is not _AUDIO_TYPE
            or binding_module.TranscriptSegmentClaim is not _SEGMENT_TYPE
            or binding_module.TranscriptBindingPreview is not _PREVIEW_TYPE
            or any(vars(_RESULT_TYPE).get(n) is not old for n, old in zip(
                _DENIALS, _RESULT_PROPS, strict=True,
            ))
            or any(vars(_PREVIEW_TYPE).get(n) is not old for n, old in zip(
                _PREVIEW_DENIALS, _PREVIEW_PROPS, strict=True,
            ))
        ):
            raise OfflineAlignmentRejected("original alignment authority changed")
        if (
            type(activity) is not _ACTIVITY_TYPE
            or type(audio) is not _AUDIO_TYPE
            or type(segments) is not tuple
            or len(segments) != len(segments_epoch)
            or any(now is not old for now, old in zip((
                activity.source_sha256, activity.sample_rate, activity.frame_samples,
                activity.total_samples, activity.active_frame_count, activity.regions,
            ), activity_fields, strict=True))
            or type(activity.regions) is not tuple
            or len(activity.regions) != len(region_epoch)
            or any(
                type(activity.regions[i]) is not _REGION_TYPE
                or activity.regions[i] is not pinned[0]
                or any(now is not old for now, old in zip((
                    pinned[0].start_frame, pinned[0].end_frame,
                    pinned[0].start_sample, pinned[0].end_sample,
                    pinned[0].active_frames,
                ), pinned[1:], strict=True))
                for i, pinned in enumerate(region_epoch)
            )
            or any(now is not old for now, old in zip((
                audio.owner_sha256, audio.scope_sha256, audio.audio_sha256,
                audio.sample_rate_hz, audio.frame_count,
            ), audio_fields, strict=True))
            or any(
                segments[i] is not fields[0]
                or any(now is not old for now, old in zip((
                    fields[0].start_frame, fields[0].end_frame, fields[0].language,
                    fields[0].text_sha256, fields[0].text,
                ), fields[1:], strict=True))
                for i, fields in enumerate(segments_epoch)
            )
        ):
            raise OfflineAlignmentRejected("alignment input changed during review")

    def verify() -> str:
        stable()
        try:
            _ACTIVITY_VERIFY(
                activity, pcm, expected_pcm_sha256, audio_fields[3],
                frame_ms=config[0], rms_threshold=config[1],
                bridge_silence_frames=config[2],
                min_active_frames=config[3], max_regions=config[4],
            )
            stable()
            bound = _TRANSCRIPT_REVIEW(audio, segments)
            stable()
        except (
            activity_module.OfflineActivityRejected,
            binding_module.TranscriptBindingRejected,
        ) as exc:
            raise OfflineAlignmentRejected("alignment input verification failed") from exc
        if (
            type(bound) is not _PREVIEW_TYPE
            or any(getattr(bound, name) is not False for name in _PREVIEW_DENIALS)
            or type(bound.fingerprint) is not str
            or bound.fingerprint != retained_transcript_fingerprint
            or bound.audio_sha256 != expected_pcm_sha256
            or bound.segment_count != len(segments)
            or activity_fields[0] != expected_pcm_sha256
            or activity_fields[1] != audio_fields[3]
            or activity_fields[3] != audio_fields[4]
        ):
            raise OfflineAlignmentRejected("PCM/transcript retained identity mismatch")
        stable()
        return bound.fingerprint

    fingerprint = verify()
    # Audio frames refer to mono PCM *samples*, not analysis-window indices.
    # Region spans include deliberately bridged silence and must not be
    # reported as proven speech or ASR coverage.
    region_spans = tuple(
        (item.start_sample, item.end_sample) for item in activity_fields[5]
    )
    text_spans = tuple((fields[1], fields[2]) for fields in segments_epoch)
    total = sum(stop - start for start, stop in region_spans)
    overlap_per_region = tuple(
        sum(max(0, min(stop, t_stop) - max(start, t_start))
            for t_start, t_stop in text_spans)
        for start, stop in region_spans
    )
    overlap = sum(overlap_per_region)
    if not 0 <= overlap <= total or not 0 <= total <= activity_fields[3]:
        raise OfflineAlignmentRejected("invalid region-span accounting")
    result_fields = (
        expected_pcm_sha256, fingerprint, len(region_spans),
        len(text_spans), total, overlap, total - overlap,
        sum(value > 0 for value in overlap_per_region),
        overlap * 1_000_000 // total if total else 0,
    )
    stable()
    if verify() != fingerprint:
        raise OfflineAlignmentRejected("alignment receipts drifted")
    stable()
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(
            (result_fields, region_spans, text_spans, config),
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()
    stable()
    result = _RESULT_TYPE(*result_fields, digest)
    expected = (*result_fields, digest)
    for denial in _DENIALS:
        if (
            type(result) is not _RESULT_TYPE
            or tuple(getattr(result, name) for name in (
                "pcm_sha256", "transcript_fingerprint", "activity_region_count",
                "transcript_segment_count", "region_span_samples",
                "transcript_overlap_samples", "uncovered_region_span_samples",
                "regions_with_overlap", "overlap_ppm", "alignment_sha256",
            )) != expected
            or getattr(result, denial) is not False
        ):
            raise OfflineAlignmentRejected("alignment result gained authority")
        stable()
    return result
