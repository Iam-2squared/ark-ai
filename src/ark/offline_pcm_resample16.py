"""Bounded deterministic mono signed-16 PCM resampler for offline fixtures.

Linear interpolation has no anti-alias filtering: NOT production ASR quality,
identity evidence, user consent or permission to transmit the raw result.
"""

from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass, field

MAX_PCM_BYTES = 2 * 1024 * 1024
_RATES = frozenset({8_000, 16_000, 22_050, 32_000, 44_100, 48_000})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class OfflineResampleRejected(ValueError):
    """Fail-closed unsupported, corrupt or excessive fixture data."""


@dataclass(frozen=True, slots=True)
class ResampledPcm:
    source_sha256: str
    output_sha256: str
    source_rate: int
    target_rate: int
    source_samples: int
    output_samples: int
    pcm: bytes = field(repr=False)  # sensitive; never auto-log, upload, persist or dispatch


_RESULT_TYPE = ResampledPcm


def _round_ratio_away_from_zero(numerator: int, denominator: int) -> int:
    sign = -1 if numerator < 0 else 1
    return sign * ((abs(numerator) * 2 + denominator) // (2 * denominator))


def resample_pcm16(
    pcm: bytes, expected_sha256: str, source_rate: int, target_rate: int
) -> ResampledPcm:
    """Map output index j to source coordinate j * source_rate / target_rate.

    Output length is ceil(source_samples * target_rate / source_rate);
    extrapolation clamps to the last input sample. All arithmetic is integer
    and round-to-nearest ties away from zero. No implicit side effects.
    """
    if type(pcm) is not bytes or not pcm or len(pcm) % 2 or len(pcm) > MAX_PCM_BYTES:
        raise OfflineResampleRejected("invalid raw mono16 input")
    if type(expected_sha256) is not str or _SHA256.fullmatch(expected_sha256) is None:
        raise OfflineResampleRejected("invalid source digest")
    if hashlib.sha256(pcm).hexdigest() != expected_sha256:
        raise OfflineResampleRejected("source digest mismatch")
    if type(source_rate) is not int or source_rate not in _RATES:
        raise OfflineResampleRejected("unsupported source rate")
    if type(target_rate) is not int or target_rate not in _RATES:
        raise OfflineResampleRejected("unsupported target rate")
    source_samples = len(pcm) // 2
    if source_samples > source_rate * 120:
        raise OfflineResampleRejected("audio duration exceeds budget")
    output_samples = (source_samples * target_rate + source_rate - 1) // source_rate
    if output_samples * 2 > MAX_PCM_BYTES:
        raise OfflineResampleRejected("resampled output exceeds budget")
    if source_rate == target_rate:
        output = pcm
    else:
        samples = [value[0] for value in struct.iter_unpack("<h", pcm)]
        out = bytearray(output_samples * 2)
        for j in range(output_samples):
            numerator = j * source_rate
            left, fraction = divmod(numerator, target_rate)
            if left >= source_samples - 1:
                value = samples[-1]
            else:
                weighted = samples[left] * (target_rate - fraction)
                weighted += samples[left + 1] * fraction
                value = _round_ratio_away_from_zero(weighted, target_rate)
            struct.pack_into("<h", out, 2 * j, max(-32768, min(32767, value)))
        output = bytes(out)
    output_digest = hashlib.sha256(output).hexdigest()
    result = ResampledPcm(
        expected_sha256, output_digest, source_rate, target_rate,
        source_samples, output_samples, output,
    )
    # Result construction is a local extension boundary, not evidence of a
    # trusted microphone or user approval. In particular a swapped factory or
    # reflective field replacement must not retarget PCM bytes or digests.
    if type(result) is not _RESULT_TYPE:
        raise OfflineResampleRejected("resample result type changed")
    expected = (
        expected_sha256, output_digest, source_rate, target_rate,
        source_samples, output_samples, output,
    )
    actual = (
        result.source_sha256, result.output_sha256,
        result.source_rate, result.target_rate, result.source_samples,
        result.output_samples, result.pcm,
    )
    if any(now is not old for now, old in zip(
        actual, expected, strict=True,
    )):
        raise OfflineResampleRejected("resample output fields changed")
    return result
