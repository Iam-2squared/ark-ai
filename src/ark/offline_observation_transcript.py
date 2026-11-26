"""Detached PNG/WAV and transcript claim join; no device, consent, ASR or dispatch.

Every digest/identity is an untrusted caller assertion unless an independent
retained witness has authenticated it. This module processes only explicit
bounded in-memory fixtures; it returns hashes and counts, never text/media.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import offline_observation_pair as pair_module
from . import offline_transcript_binding as transcript_module
from .offline_pcm_wav import OfflineWaveRequest
from .offline_png_inventory import OfflinePngRequest
from .offline_transcript_binding import TranscriptSegmentClaim

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-observation-transcript-v1\0"
_PAIR_FN = pair_module.inspect_disconnected_observation_pair
_TRANSCRIPT_FN = transcript_module.review_audio_transcript_binding
_PAIR_DENIALS = (
    "camera_provenance_verified", "microphone_provenance_verified",
    "consent_verified", "external_disclosure_authorized",
    "tool_execution_authorized",
)
_TRANSCRIPT_DENIALS = (
    "audio_or_transcript_authenticated", "user_consent_proven",
    "asr_verified", "tool_execution_authorized",
)
_PAIR_PROPERTIES = tuple(
    getattr(pair_module.OfflineObservationPair, x) for x in _PAIR_DENIALS
)
_TRANSCRIPT_PROPERTIES = tuple(
    getattr(transcript_module.TranscriptBindingPreview, x)
    for x in _TRANSCRIPT_DENIALS
)


class OfflineObservationTranscriptRejected(ValueError):
    """Untrusted disconnected multimodal claims cannot be bound safely."""


@dataclass(frozen=True, slots=True)
class OfflineObservationTranscript:
    pair_sha256: str
    transcript_fingerprint: str
    segment_count: int
    first_frame: int
    final_frame: int
    envelope_sha256: str

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def asr_verified(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_execution_authorized(self) -> bool:
        return False


_RESULT = OfflineObservationTranscript
_DENIAL_NAMES = (
    "source_authenticated", "consent_verified", "asr_verified",
    "external_disclosure_authorized", "tool_execution_authorized",
)
_RESULT_PROPERTIES = tuple(getattr(_RESULT, x) for x in _DENIAL_NAMES)

# A disconnected fixture still carries private image/audio/transcript bytes.
# Frozen dataclasses do not protect their *class-level* slotted descriptors.
# Refuse replaced getters before the first request field read, rather than
# relying only on rechecking an input after it has already been accessed.
_SOURCE_TYPES = (OfflinePngRequest, OfflineWaveRequest, TranscriptSegmentClaim)
_SOURCE_FIELDS = (
    ("owner_sha256", "privacy_sha256", "source_sha256", "png_bytes"),
    ("owner_sha256", "privacy_sha256", "wav_sha256", "wav_bytes"),
    ("start_frame", "end_frame", "language", "text_sha256", "text"),
)
_LOOKUP_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_SOURCE_ORIGINALS = tuple(
    tuple(vars(cls).get(key) for key in (*names, *_LOOKUP_HOOKS))
    for cls, names in zip(_SOURCE_TYPES, _SOURCE_FIELDS, strict=True)
)
_RESULT_FIELDS = (
    "pair_sha256", "transcript_fingerprint", "segment_count",
    "first_frame", "final_frame", "envelope_sha256",
)
_RESULT_HOOKS = ("__init__", *_LOOKUP_HOOKS)
_RESULT_ORIGINALS = tuple(
    vars(_RESULT).get(key)
    for key in (*_RESULT_FIELDS, *_DENIAL_NAMES, *_RESULT_HOOKS)
)
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA_GRAMMAR = _SHA
_ORIGINAL_PAIR_FN = _PAIR_FN
_ORIGINAL_TRANSCRIPT_FN = _TRANSCRIPT_FN


def _require_original_observation_carriers() -> None:
    # This is local callback custody only, not sensor/source attestation.
    if (
        (OfflinePngRequest, OfflineWaveRequest, TranscriptSegmentClaim)
        != _SOURCE_TYPES
        or any(
            any(
                vars(cls).get(key) is not descriptor
                for key, descriptor in zip(
                    (*names, *_LOOKUP_HOOKS), originals, strict=True,
                )
            )
            for cls, names, originals in zip(
                _SOURCE_TYPES, _SOURCE_FIELDS, _SOURCE_ORIGINALS, strict=True,
            )
        )
        or OfflineObservationTranscript is not _RESULT
        or any(
            vars(_RESULT).get(key) is not descriptor
            for key, descriptor in zip(
                (*_RESULT_FIELDS, *_DENIAL_NAMES, *_RESULT_HOOKS),
                _RESULT_ORIGINALS, strict=True,
            )
        )
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA_GRAMMAR
        or _PAIR_FN is not _ORIGINAL_PAIR_FN
        or _TRANSCRIPT_FN is not _ORIGINAL_TRANSCRIPT_FN
    ):
        raise OfflineObservationTranscriptRejected(
            "observation fixture carrier or digest callback replaced"
        )


def review_disconnected_observation_transcript(
    image: OfflinePngRequest,
    audio: OfflineWaveRequest,
    segments: tuple[TranscriptSegmentClaim, ...],
    *,
    retained_owner_sha256: str,
    retained_privacy_sha256: str,
    retained_png_sha256: str,
    retained_wav_sha256: str,
    retained_transcript_fingerprint: str,
) -> OfflineObservationTranscript:
    """Review an exact image/audio/transcript fixture without granting authority.

    The transcript fingerprint must be independently retained to detect a
    historical transcript substitution. This function cannot prove that the
    declared text came from the declared audio or any real sensor.
    """
    if (
        type(image) is not OfflinePngRequest
        or type(audio) is not OfflineWaveRequest
        or type(segments) is not tuple
        or not 1 <= len(segments) <= 64
        or any(type(s) is not TranscriptSegmentClaim for s in segments)
    ):
        raise OfflineObservationTranscriptRejected("exact bounded fixture inputs required")
    _require_original_observation_carriers()
    retained = (
        retained_owner_sha256, retained_privacy_sha256,
        retained_png_sha256, retained_wav_sha256,
        retained_transcript_fingerprint,
    )
    if any(type(v) is not str or _SHA.fullmatch(v) is None for v in retained):
        raise OfflineObservationTranscriptRejected("exact retained digest claims required")

    image_fields = (
        image.owner_sha256, image.privacy_sha256,
        image.source_sha256, image.png_bytes,
    )
    audio_fields = (
        audio.owner_sha256, audio.privacy_sha256,
        audio.wav_sha256, audio.wav_bytes,
    )
    pinned = tuple((
        s, s.start_frame, s.end_frame, s.language, s.text_sha256, s.text,
    ) for s in segments)

    def epoch() -> None:
        _require_original_observation_carriers()
        if (
            pair_module.inspect_disconnected_observation_pair is not _PAIR_FN
            or transcript_module.review_audio_transcript_binding is not _TRANSCRIPT_FN
            or any(
                getattr(pair_module.OfflineObservationPair, n) is not p
                for n, p in zip(_PAIR_DENIALS, _PAIR_PROPERTIES, strict=True)
            )
            or any(
                getattr(transcript_module.TranscriptBindingPreview, n) is not p
                for n, p in zip(
                    _TRANSCRIPT_DENIALS, _TRANSCRIPT_PROPERTIES, strict=True,
                )
            )
            or any(
                getattr(_RESULT, n) is not p
                for n, p in zip(_DENIAL_NAMES, _RESULT_PROPERTIES, strict=True)
            )
        ):
            raise OfflineObservationTranscriptRejected(
                "observation/transcript authority implementation replaced"
            )
        if (
            type(image) is not OfflinePngRequest
            or type(audio) is not OfflineWaveRequest
            or any(a is not b for a, b in zip(
                (
                    image.owner_sha256, image.privacy_sha256,
                    image.source_sha256, image.png_bytes,
                ),
                image_fields, strict=True,
            ))
            or any(a is not b for a, b in zip(
                (
                    audio.owner_sha256, audio.privacy_sha256,
                    audio.wav_sha256, audio.wav_bytes,
                ),
                audio_fields, strict=True,
            ))
            or len(segments) != len(pinned)
            or any(
                segments[i] is not item[0]
                or any(a is not b for a, b in zip(
                    (
                        item[0].start_frame, item[0].end_frame,
                        item[0].language, item[0].text_sha256, item[0].text,
                    ),
                    item[1:], strict=True,
                ))
                for i, item in enumerate(pinned)
            )
        ):
            raise OfflineObservationTranscriptRejected(
                "observation/transcript input epoch changed"
            )

    def measure() -> tuple[str, str, int, int, int]:
        epoch()
        try:
            pair = _PAIR_FN(
                image, audio, retained_owner_sha256=retained[0],
                retained_privacy_sha256=retained[1],
                retained_png_sha256=retained[2],
                retained_wav_sha256=retained[3],
            )
            epoch()
            if type(pair) is not pair_module.OfflineObservationPair:
                raise OfflineObservationTranscriptRejected("invalid media pair result")
            if (
                pair.owner_sha256 != retained[0]
                or pair.privacy_sha256 != retained[1]
                or pair.png_sha256 != retained[2]
                or pair.wav_sha256 != retained[3]
            ):
                raise OfflineObservationTranscriptRejected("media pair identity mismatch")
            claim = transcript_module.AudioMetadataClaim(
                pair.owner_sha256, pair.privacy_sha256, pair.wav_sha256,
                pair.sample_rate_hz, pair.audio_frames,
            )
            transcript = _TRANSCRIPT_FN(claim, segments)
            epoch()
        except (
            pair_module.OfflineObservationPairRejected,
            transcript_module.TranscriptBindingRejected,
        ) as exc:
            raise OfflineObservationTranscriptRejected(
                "disconnected media or transcript review rejected"
            ) from exc
        if type(transcript) is not transcript_module.TranscriptBindingPreview:
            raise OfflineObservationTranscriptRejected("invalid transcript review result")
        if (
            transcript.audio_sha256 != retained[3]
            or transcript.fingerprint != retained[4]
        ):
            raise OfflineObservationTranscriptRejected(
                "retained transcript or audio identity mismatch"
            )
        for result, names in (
            (pair, _PAIR_DENIALS), (transcript, _TRANSCRIPT_DENIALS),
        ):
            for name in names:
                if getattr(result, name) is not False:
                    raise OfflineObservationTranscriptRejected(
                        "disconnected review gained authority"
                    )
                epoch()
        data = (
            pair.pair_sha256, transcript.fingerprint,
            transcript.segment_count, transcript.first_frame,
            transcript.final_frame,
        )
        if (
            any(type(value) is not str or _SHA.fullmatch(value) is None
                for value in data[:2])
            or any(type(value) is not int for value in data[2:])
            or data[2] != len(pinned)
            or not 0 <= data[3] < data[4] <= pair.audio_frames
        ):
            raise OfflineObservationTranscriptRejected("invalid bound metadata")
        epoch()
        return data

    first = measure()
    if measure() != first:
        raise OfflineObservationTranscriptRejected("multimodal review drifted")
    epoch()
    canonical = json.dumps(
        [retained, first], ensure_ascii=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + canonical).hexdigest()
    epoch()
    result = _RESULT(*first, digest)
    expected = (*first, digest)
    for name in _DENIAL_NAMES:
        if (
            type(result) is not _RESULT
            or any(a is not b for a, b in zip(
                (
                    result.pair_sha256, result.transcript_fingerprint,
                    result.segment_count, result.first_frame,
                    result.final_frame, result.envelope_sha256,
                ),
                expected, strict=True,
            ))
            or getattr(result, name) is not False
        ):
            raise OfflineObservationTranscriptRejected(
                "multimodal report changed or gained authority"
            )
        epoch()
    return result
