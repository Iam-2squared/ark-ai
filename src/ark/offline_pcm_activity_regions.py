"""Deterministic, disconnected PCM activity-region fixture analysis.

Not VAD, ASR, speaker authentication, consent, or execution authorization.
Input/output are privacy-sensitive even when only region metadata is returned.
"""

from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass

MAX_PCM_BYTES = 2 * 1024 * 1024
_RATES = frozenset({8_000, 16_000, 32_000, 48_000})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class OfflineActivityRejected(ValueError):
    """Fail-closed fixture-input or size rejection."""


@dataclass(frozen=True, slots=True)
class ActivityRegion:
    start_frame: int
    end_frame: int  # exclusive
    start_sample: int
    end_sample: int  # exclusive
    active_frames: int


@dataclass(frozen=True, slots=True)
class ActivityRegions:
    source_sha256: str
    sample_rate: int
    frame_samples: int
    total_samples: int
    active_frame_count: int
    regions: tuple[ActivityRegion, ...]


def detect_activity_regions(
    pcm: bytes,
    expected_sha256: str,
    sample_rate: int,
    *,
    frame_ms: int = 20,
    rms_threshold: int = 512,
    bridge_silence_frames: int = 1,
    min_active_frames: int = 1,
    max_regions: int = 32,
) -> ActivityRegions:
    """Group above-threshold mono signed-16 LE frames, without audio disclosure.

    Mean-square strictly exceeds threshold**2 to count as active. A final
    partial frame is evaluated against its actual sample count. Gap bridging
    changes region span, not the minimum actual active-frame requirement.
    """
    if type(pcm) is not bytes or not pcm or len(pcm) > MAX_PCM_BYTES or len(pcm) % 2:
        raise OfflineActivityRejected("invalid PCM bytes")
    if type(expected_sha256) is not str or _SHA256.fullmatch(expected_sha256) is None:
        raise OfflineActivityRejected("invalid source digest")
    if hashlib.sha256(pcm).hexdigest() != expected_sha256:
        raise OfflineActivityRejected("source digest mismatch")
    if type(sample_rate) is not int or sample_rate not in _RATES:
        raise OfflineActivityRejected("unsupported sample rate")
    if type(frame_ms) is not int or frame_ms not in (10, 20, 30):
        raise OfflineActivityRejected("unsupported frame duration")
    if type(rms_threshold) is not int or not 0 <= rms_threshold <= 32768:
        raise OfflineActivityRejected("invalid threshold")
    if type(bridge_silence_frames) is not int or not 0 <= bridge_silence_frames <= 10:
        raise OfflineActivityRejected("invalid silence gap")
    if type(min_active_frames) is not int or not 1 <= min_active_frames <= 100:
        raise OfflineActivityRejected("invalid minimum activity")
    if type(max_regions) is not int or not 1 <= max_regions <= 32:
        raise OfflineActivityRejected("invalid region budget")

    total_samples = len(pcm) // 2
    if total_samples > sample_rate * 120:
        raise OfflineActivityRejected("audio duration exceeds budget")
    frame_samples = sample_rate * frame_ms // 1000
    threshold_sq = rms_threshold * rms_threshold
    starts: list[int] = []
    ends: list[int] = []
    counts: list[int] = []
    active_total = 0
    for frame, offset in enumerate(range(0, total_samples, frame_samples)):
        sample_end = min(total_samples, offset + frame_samples)
        samples = struct.iter_unpack("<h", memoryview(pcm)[2 * offset : 2 * sample_end])
        energy = sum(sample[0] * sample[0] for sample in samples)
        if energy <= threshold_sq * (sample_end - offset):
            continue
        active_total += 1
        if starts and frame - ends[-1] <= bridge_silence_frames:
            ends[-1] = frame + 1
            counts[-1] += 1
        else:
            starts.append(frame)
            ends.append(frame + 1)
            counts.append(1)
        if len(starts) > max_regions:
            raise OfflineActivityRejected("too many activity regions")

    regions = tuple(
        ActivityRegion(start, end, start * frame_samples,
                       min(total_samples, end * frame_samples), count)
        for start, end, count in zip(starts, ends, counts)
        if count >= min_active_frames
    )
    return ActivityRegions(
        expected_sha256, sample_rate, frame_samples, total_samples, active_total, regions
    )
