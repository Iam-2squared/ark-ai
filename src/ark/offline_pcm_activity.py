"""Deterministic PCM amplitude preview from explicit, untrusted in-memory fixtures.

No microphone, speech recognition, speaker identification or consent proof.
Frame statistics can themselves be sensitive and MUST remain local unless
separately authorized. This does not dispatch a ToolBackend or persist bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-pcm-activity-v1\0"
_MAX_BYTES = 2 * 1024 * 1024
_MAX_WINDOWS = 1024


class OfflinePcmActivityRejected(ValueError):
    """Audio fixture or amplitude inventory violates exact input bounds."""


@dataclass(frozen=True, slots=True)
class OfflinePcmActivityRequest:
    owner_sha256: str
    privacy_sha256: str
    pcm_sha256: str
    pcm_bytes: bytes = field(repr=False)
    channels: int
    sample_rate_hz: int
    bits_per_sample: int
    window_ms: int = 20


@dataclass(frozen=True, slots=True)
class OfflinePcmActivityWindow:
    index: int
    start_frame: int
    end_frame: int
    sample_count: int
    peak_absolute: int
    sum_squares: int


@dataclass(frozen=True, slots=True)
class OfflinePcmActivityReview:
    owner_sha256: str
    privacy_sha256: str
    pcm_sha256: str
    channels: int
    sample_rate_hz: int
    bits_per_sample: int
    frame_count: int
    window_ms: int
    windows: tuple[OfflinePcmActivityWindow, ...]
    inventory_sha256: str

    @property
    def microphone_provenance_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def speech_or_speaker_recognized(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False



# Fixture data and derived amplitude windows may reveal private audio. Freeze
# implementation and carrier identities before reading even the first request
# field. This is an in-process consistency check, NOT device provenance or
# an isolation boundary against arbitrary Python code in this interpreter.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_BYTES = _MAX_BYTES
_ORIGINAL_MAX_WINDOWS = _MAX_WINDOWS

_REQUEST_TYPE = OfflinePcmActivityRequest
_WINDOW_TYPE = OfflinePcmActivityWindow
_REVIEW_TYPE = OfflinePcmActivityReview
_REQUEST_FIELDS = (
    "owner_sha256", "privacy_sha256", "pcm_sha256", "pcm_bytes",
    "channels", "sample_rate_hz", "bits_per_sample", "window_ms",
)
_WINDOW_FIELDS = (
    "index", "start_frame", "end_frame", "sample_count",
    "peak_absolute", "sum_squares",
)
_REVIEW_FIELDS = (
    "owner_sha256", "privacy_sha256", "pcm_sha256", "channels",
    "sample_rate_hz", "bits_per_sample", "frame_count", "window_ms",
    "windows", "inventory_sha256",
)
_LOOKUP_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_DENIALS = (
    "microphone_provenance_verified", "consent_verified",
    "speech_or_speaker_recognized", "disclosure_authorized",
)
_ORIGINAL_CARRIERS = tuple(
    (cls, names, tuple(vars(cls).get(name) for name in names))
    for cls, names in (
        (_REQUEST_TYPE, _REQUEST_FIELDS + _LOOKUP_HOOKS),
        (_WINDOW_TYPE, _WINDOW_FIELDS + _LOOKUP_HOOKS),
        (_REVIEW_TYPE, _REVIEW_FIELDS + _LOOKUP_HOOKS + _DENIALS),
    )
)


def _require_original_pcm_activity_authority() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or type(_MAX_BYTES) is not int or _MAX_BYTES != _ORIGINAL_MAX_BYTES
        or type(_MAX_WINDOWS) is not int or _MAX_WINDOWS != _ORIGINAL_MAX_WINDOWS
        or OfflinePcmActivityRequest is not _REQUEST_TYPE
        or OfflinePcmActivityWindow is not _WINDOW_TYPE
        or OfflinePcmActivityReview is not _REVIEW_TYPE
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in _ORIGINAL_CARRIERS
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise OfflinePcmActivityRejected(
            "PCM activity codec, carrier or denial authority changed"
        )


def analyze_offline_pcm_activity(
    request: OfflinePcmActivityRequest,
) -> OfflinePcmActivityReview:
    """Return exact, integer-only amplitude windows with no raw sample output.

    Supports unsigned 8-bit and signed little-endian 16/24/32-bit PCM.
    Every complete frame belongs to exactly one window, including the tail.
    The caller-provided identity hashes are integrity claims, NOT authority.
    """
    _require_original_pcm_activity_authority()
    if type(request) is not OfflinePcmActivityRequest:
        raise OfflinePcmActivityRejected("exact PCM request required")
    pinned = (
        request.owner_sha256, request.privacy_sha256, request.pcm_sha256,
        request.pcm_bytes, request.channels, request.sample_rate_hz,
        request.bits_per_sample, request.window_ms,
    )

    def check_epoch() -> None:
        _require_original_pcm_activity_authority()
        now = (
            request.owner_sha256, request.privacy_sha256, request.pcm_sha256,
            request.pcm_bytes, request.channels, request.sample_rate_hz,
            request.bits_per_sample, request.window_ms,
        )
        if any(actual is not original for actual, original in zip(now, pinned, strict=True)):
            raise OfflinePcmActivityRejected("PCM source changed during review")

    check_epoch()
    owner, privacy, digest, pcm, channels, rate, bits, window_ms = pinned
    if (
        any(type(value) is not str or _SHA.fullmatch(value) is None
            for value in (owner, privacy, digest))
        or type(pcm) is not bytes or not 0 < len(pcm) <= _MAX_BYTES
        or type(channels) is not int or channels not in (1, 2)
        or type(rate) is not int or not 8000 <= rate <= 48000
        or type(bits) is not int or bits not in (8, 16, 24, 32)
        or type(window_ms) is not int or not 10 <= window_ms <= 100
        or window_ms % 10 != 0 or (rate * window_ms) % 1000 != 0
    ):
        raise OfflinePcmActivityRejected("unsupported PCM format or budget")
    bytes_per_sample = bits // 8
    frame_width = channels * bytes_per_sample
    if len(pcm) % frame_width:
        raise OfflinePcmActivityRejected("partial PCM frame")
    frames = len(pcm) // frame_width
    window_frames = rate * window_ms // 1000
    if frames > rate * 120 or (frames + window_frames - 1) // window_frames > _MAX_WINDOWS:
        raise OfflinePcmActivityRejected("PCM duration or window budget exceeded")
    if hashlib.sha256(pcm).hexdigest() != digest:
        raise OfflinePcmActivityRejected("PCM checksum mismatch")
    check_epoch()
    windows: list[OfflinePcmActivityWindow] = []
    view = memoryview(pcm)
    for start in range(0, frames, window_frames):
        end = min(start + window_frames, frames)
        peak = 0
        squares = 0
        for offset in range(start * frame_width, end * frame_width, bytes_per_sample):
            value = int.from_bytes(
                view[offset:offset + bytes_per_sample], "little", signed=bits != 8,
            )
            if bits == 8:
                value -= 128
            magnitude = abs(value)
            peak = max(peak, magnitude)
            squares += value * value
        windows.append(OfflinePcmActivityWindow(
            len(windows), start, end, (end - start) * channels, peak, squares,
        ))
        check_epoch()
    rows = tuple(windows)
    manifest = {
        "owner": owner, "privacy": privacy, "pcm": digest,
        "channels": channels, "rate": rate, "bits": bits,
        "frames": frames, "window_ms": window_ms,
        "windows": [(w.index, w.start_frame, w.end_frame, w.sample_count,
                     w.peak_absolute, w.sum_squares) for w in rows],
    }
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True).encode("ascii")
    inventory_digest = hashlib.sha256(_DOMAIN + canonical).hexdigest()
    check_epoch()
    result = OfflinePcmActivityReview(
        owner, privacy, digest, channels, rate, bits, frames, window_ms,
        rows, inventory_digest,
    )
    check_epoch()
    if (
        type(result) is not OfflinePcmActivityReview
        or result.windows is not rows
        or result.inventory_sha256 is not inventory_digest
        or any(getattr(result, name) is not False for name in _DENIALS)
    ):
        raise OfflinePcmActivityRejected("constructed PCM review changed")
    check_epoch()
    return result
