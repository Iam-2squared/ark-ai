"""Deterministic PCM amplitude preview from explicit, untrusted in-memory fixtures.

No microphone, speech recognition, speaker identification or consent proof.
Frame statistics can themselves be sensitive and MUST remain local unless
separately authorized. This does not dispatch a ToolBackend or persist bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

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
    pcm_bytes: bytes
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


def analyze_offline_pcm_activity(
    request: OfflinePcmActivityRequest,
) -> OfflinePcmActivityReview:
    """Return exact, integer-only amplitude windows with no raw sample output.

    Supports unsigned 8-bit and signed little-endian 16/24/32-bit PCM.
    Every complete frame belongs to exactly one window, including the tail.
    The caller-provided identity hashes are integrity claims, NOT authority.
    """
    if type(request) is not OfflinePcmActivityRequest:
        raise OfflinePcmActivityRejected("exact PCM request required")
    pinned = (
        request.owner_sha256, request.privacy_sha256, request.pcm_sha256,
        request.pcm_bytes, request.channels, request.sample_rate_hz,
        request.bits_per_sample, request.window_ms,
    )

    def check_epoch() -> None:
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
    ):
        raise OfflinePcmActivityRejected("constructed PCM review changed")
    return result
