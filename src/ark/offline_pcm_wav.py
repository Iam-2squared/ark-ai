"""Strict read-only RIFF/WAVE PCM inspection on caller-provided fixture bytes.

Only canonical two-chunk RIFF PCM (fmt then data) is accepted. The result
contains no audio samples, cannot verify consent/source identity, and grants
no microphone, ASR, speaker identification, or external-action permission.
"""

from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_WAV_BYTES = 8 * 1024 * 1024
_MAX_DURATION_SECONDS = 120


class OfflineWaveRejected(ValueError):
    """The untrusted fixture is malformed, oversized, or unsupported."""


@dataclass(frozen=True, slots=True)
class OfflineWaveRequest:
    owner_sha256: str
    privacy_sha256: str
    wav_sha256: str
    wav_bytes: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class OfflineWaveReview:
    owner_sha256: str
    privacy_sha256: str
    wav_sha256: str
    pcm_sha256: str
    channel_count: int
    sample_rate_hz: int
    bits_per_sample: int
    frame_count: int
    duration_ms_floor: int
    duration_ms_remainder: int

    @property
    def microphone_provenance_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def speech_recognized(self) -> bool:
        return False

    @property
    def authorized_to_disclose(self) -> bool:
        return False


_REVIEW_TYPE = OfflineWaveReview
_ORIGINAL_REVIEW_INIT = vars(_REVIEW_TYPE)["__init__"]

# The WAV request contains untrusted private audio bytes. Verify its
# import-original dataclass field and lookup machinery before ANY access,
# including the initial four-field capture ahead of digest validation.
_REQUEST_TYPE = OfflineWaveRequest
_ORIGINAL_REQUEST_INIT = vars(_REQUEST_TYPE)["__init__"]
_REQUEST_FIELDS = ("owner_sha256", "privacy_sha256", "wav_sha256", "wav_bytes")
_REVIEW_FIELDS = (
    "owner_sha256", "privacy_sha256", "wav_sha256", "pcm_sha256",
    "channel_count", "sample_rate_hz", "bits_per_sample", "frame_count",
    "duration_ms_floor", "duration_ms_remainder",
)
_WAVE_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REQUEST_FIELDS = tuple(
    vars(_REQUEST_TYPE)[name] for name in _REQUEST_FIELDS
)
_ORIGINAL_REVIEW_FIELDS = tuple(
    vars(_REVIEW_TYPE)[name] for name in _REVIEW_FIELDS
)
_ORIGINAL_REQUEST_HOOKS = tuple(
    vars(_REQUEST_TYPE).get(name) for name in _WAVE_HOOKS
)
_ORIGINAL_REVIEW_HOOKS = tuple(
    vars(_REVIEW_TYPE).get(name) for name in _WAVE_HOOKS
)
_DENIAL_NAMES = (
    "microphone_provenance_verified", "consent_verified",
    "speech_recognized", "authorized_to_disclose",
)
_ORIGINAL_DENIALS = tuple(vars(_REVIEW_TYPE)[key] for key in _DENIAL_NAMES)

# The WAV parser handles private caller-provided audio, so validate original
# hashing, binary codec and framing limits BEFORE any request field access.
# These checks are in-process fail-closed fixtures, not sensor attestation.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_STRUCT = struct
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_UNPACK_FROM = struct.unpack_from
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_MAX_WAV_BYTES = _MAX_WAV_BYTES
_ORIGINAL_MAX_DURATION_SECONDS = _MAX_DURATION_SECONDS


def _require_original_wave_authority() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or struct is not _ORIGINAL_STRUCT
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or struct.unpack_from is not _ORIGINAL_UNPACK_FROM
        or _SHA is not _ORIGINAL_SHA_PATTERN
        # The SHA helper sees private owner/privacy digests. Refuse a
        # substituted callable before any request field is read.
        or _sha is not _ORIGINAL_SHA_HELPER
        or _MAX_WAV_BYTES is not _ORIGINAL_MAX_WAV_BYTES
        or _MAX_DURATION_SECONDS is not _ORIGINAL_MAX_DURATION_SECONDS
    ):
        raise OfflineWaveRejected(
            "WAV codec or digest implementation changed before private bytes"
        )
    if (
        OfflineWaveRequest is not _REQUEST_TYPE
        or vars(_REQUEST_TYPE).get("__init__") is not _ORIGINAL_REQUEST_INIT
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(
                _REQUEST_FIELDS, _ORIGINAL_REQUEST_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(
                _WAVE_HOOKS, _ORIGINAL_REQUEST_HOOKS, strict=True,
            )
        )
    ):
        raise OfflineWaveRejected("WAV request identity descriptor changed")
    if (
        any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _REVIEW_FIELDS, _ORIGINAL_REVIEW_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _WAVE_HOOKS, _ORIGINAL_REVIEW_HOOKS, strict=True,
            )
        )
    ):
        raise OfflineWaveRejected("constructed WAV review changed: field epoch")
    if (
        OfflineWaveReview is not _REVIEW_TYPE
        or vars(_REVIEW_TYPE).get("__init__") is not _ORIGINAL_REVIEW_INIT
    ):
        raise OfflineWaveRejected("constructed WAV review changed: initializer identity")
    if any(
        vars(_REVIEW_TYPE).get(name) is not original
        for name, original in zip(
            _DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True,
        )
    ):
        raise OfflineWaveRejected(
            "WAV denial authority descriptors changed or claims authority"
        )


def _sha(value: object) -> bool:
    # Fixed-width ASCII before regex: caller-supplied digest labels may be
    # enormous even when the WAV bytes themselves fit the source budget.
    return type(value) is str and len(value) == 64 and _SHA.fullmatch(value) is not None


_ORIGINAL_SHA_HELPER = _sha


def inspect_local_pcm_wav(request: OfflineWaveRequest) -> OfflineWaveReview:
    """Inspect exact in-memory PCM bytes without retaining or exporting samples.

    Strict subset: little-endian RIFF/WAVE; 16-byte format chunk and one PCM
    data chunk, 1-2 channels, 8/16/24/32-bit, 8-48 kHz, at most 120 seconds.
    Unknown metadata chunks (potential PII) and container padding beyond RIFF
    length are rejected instead of being silently ignored.
    """
    if type(request) is not OfflineWaveRequest:
        raise OfflineWaveRejected("exact Wave request required")
    _require_original_wave_authority()
    original = (
        request.owner_sha256, request.privacy_sha256,
        request.wav_sha256, request.wav_bytes,
    )

    def check_epoch() -> None:
        _require_original_wave_authority()
        now = (
            request.owner_sha256, request.privacy_sha256,
            request.wav_sha256, request.wav_bytes,
        )
        if any(a is not b for a, b in zip(now, original, strict=True)):
            raise OfflineWaveRejected("untrusted WAV request carrier changed")

    check_epoch()
    owner, privacy, expected_hash, data = original
    if not all(_sha(x) for x in (owner, privacy, expected_hash)):
        raise OfflineWaveRejected("invalid WAV owner, scope or checksum shape")
    if type(data) is not bytes or not 44 <= len(data) <= _MAX_WAV_BYTES:
        raise OfflineWaveRejected("WAV must be bounded exact bytes")
    if data[:4] != b"RIFF" or data[8:12] != b"WAVE":
        raise OfflineWaveRejected("only little-endian RIFF/WAVE allowed")
    riff_length = struct.unpack_from("<I", data, 4)[0]
    if riff_length != len(data) - 8:
        raise OfflineWaveRejected("RIFF declared length disagrees with bytes")
    if hashlib.sha256(data).hexdigest() != expected_hash:
        raise OfflineWaveRejected("declared WAV checksum mismatch")
    check_epoch()
    cursor = 12
    fmt: tuple[int, int, int] | None = None
    pcm_sha = None
    frame_count = None
    for expected_chunk in (b"fmt ", b"data"):
        if cursor + 8 > len(data):
            raise OfflineWaveRejected("missing canonical PCM chunk")
        chunk_id, chunk_bytes = struct.unpack_from("<4sI", data, cursor)
        cursor += 8
        end = cursor + chunk_bytes
        if chunk_id != expected_chunk or end > len(data):
            raise OfflineWaveRejected("unknown, reordered or oversized chunk")
        if chunk_id == b"fmt ":
            if chunk_bytes != 16:
                raise OfflineWaveRejected("only 16-byte PCM format chunk allowed")
            encoding, channels, sample_rate, byte_rate, frame_width, bits = struct.unpack_from(
                "<HHIIHH", data, cursor,
            )
            if (
                encoding != 1
                or channels not in (1, 2)
                or not 8_000 <= sample_rate <= 48_000
                or bits not in (8, 16, 24, 32)
                or frame_width != channels * bits // 8
                or byte_rate != sample_rate * frame_width
            ):
                raise OfflineWaveRejected("inconsistent or unsupported PCM format")
            fmt = (channels, sample_rate, bits)
        else:
            if fmt is None:
                raise OfflineWaveRejected("PCM format not yet validated")
            channels, sample_rate, bits = fmt
            frame_width = channels * bits // 8
            if chunk_bytes == 0 or chunk_bytes % frame_width:
                raise OfflineWaveRejected("partial or empty PCM frames")
            frame_count = chunk_bytes // frame_width
            if frame_count > _MAX_DURATION_SECONDS * sample_rate:
                raise OfflineWaveRejected("audio duration budget exceeded")
            pcm_sha = hashlib.sha256(memoryview(data)[cursor:end]).hexdigest()
        cursor = end
        if chunk_bytes & 1:
            if cursor >= len(data) or data[cursor] != 0:
                raise OfflineWaveRejected("missing or noncanonical RIFF pad byte")
            cursor += 1
        check_epoch()
    if cursor != len(data):
        raise OfflineWaveRejected("trailing or unreviewed RIFF content")
    if fmt is None or pcm_sha is None or frame_count is None:
        raise OfflineWaveRejected("incomplete PCM inventory")
    channels, sample_rate, bits = fmt
    milliseconds, remainder = divmod(frame_count * 1000, sample_rate)
    check_epoch()
    _require_original_wave_authority()
    result = OfflineWaveReview(
        owner, privacy, expected_hash, pcm_sha, channels, sample_rate,
        bits, frame_count, milliseconds, remainder,
    )
    check_epoch()
    # Pin all denied-authority descriptors BEFORE any potentially reentrant
    # property getter. A getter that returns False can still replace another
    # class property with a later authority-granting implementation.
    _require_original_wave_authority()
    if (
        type(result) is not _REVIEW_TYPE
        or result.owner_sha256 is not owner
        or result.privacy_sha256 is not privacy
        or result.wav_sha256 is not expected_hash
        or result.pcm_sha256 is not pcm_sha
        or result.channel_count is not channels
        or result.sample_rate_hz is not sample_rate
        or result.bits_per_sample is not bits
        or result.frame_count is not frame_count
        or result.duration_ms_floor is not milliseconds
        or result.duration_ms_remainder is not remainder
        or result.microphone_provenance_verified is not False
        or result.consent_verified is not False
        or result.speech_recognized is not False
        or result.authorized_to_disclose is not False
    ):
        raise OfflineWaveRejected("constructed WAV review changed or claims authority")
    check_epoch()
    # A False-returning property may still mutate the exact frozen result
    # through object.__setattr__. The first field checks preceded those
    # authority probes, so repeat them after the final authority getter.
    if (
        type(result) is not _REVIEW_TYPE
        or result.owner_sha256 is not owner
        or result.privacy_sha256 is not privacy
        or result.wav_sha256 is not expected_hash
        or result.pcm_sha256 is not pcm_sha
        or result.channel_count is not channels
        or result.sample_rate_hz is not sample_rate
        or result.bits_per_sample is not bits
        or result.frame_count is not frame_count
        or result.duration_ms_floor is not milliseconds
        or result.duration_ms_remainder is not remainder
    ):
        raise OfflineWaveRejected("constructed WAV review changed after authority review")
    check_epoch()
    _require_original_wave_authority()
    return result
