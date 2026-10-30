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


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def inspect_local_pcm_wav(request: OfflineWaveRequest) -> OfflineWaveReview:
    """Inspect exact in-memory PCM bytes without retaining or exporting samples.

    Strict subset: little-endian RIFF/WAVE; 16-byte format chunk and one PCM
    data chunk, 1-2 channels, 8/16/24/32-bit, 8-48 kHz, at most 120 seconds.
    Unknown metadata chunks (potential PII) and container padding beyond RIFF
    length are rejected instead of being silently ignored.
    """
    if type(request) is not OfflineWaveRequest:
        raise OfflineWaveRejected("exact Wave request required")
    original = (
        request.owner_sha256, request.privacy_sha256,
        request.wav_sha256, request.wav_bytes,
    )

    def check_epoch() -> None:
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
    result = OfflineWaveReview(
        owner, privacy, expected_hash, pcm_sha, channels, sample_rate,
        bits, frame_count, milliseconds, remainder,
    )
    check_epoch()
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
    return result
