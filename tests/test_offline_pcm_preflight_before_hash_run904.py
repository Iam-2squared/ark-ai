"""Offline mono16 input admission precedes the sensitive PCM hash pass.

Synthetic bytes only: no microphone, audio device, ASR service, transmission,
training or consent. Error precedence is part of the fail-closed ingress.
"""

from __future__ import annotations

import hashlib
import struct

import pytest

from ark.offline_pcm_resample16 import OfflineResampleRejected, resample_pcm16


@pytest.mark.parametrize(
    ("source", "target", "reason"),
    (
        (0, 8_000, "unsupported source rate"),
        (True, 8_000, "unsupported source rate"),
        (8_000, 0, "unsupported target rate"),
        (8_000, 16_000.0, "unsupported target rate"),
    ),
)
def test_invalid_rates_rejected_before_digest_comparison(source, target, reason):
    # Intentionally wrong but syntactically valid hash: old implementation
    # failed at the content hash before noticing malformed caller metadata.
    raw = struct.pack("<hh", -1, 1)
    with pytest.raises(OfflineResampleRejected, match=reason):
        resample_pcm16(raw, "0" * 64, source, target)


def test_duration_budget_precedes_digest_comparison():
    # 120 seconds + 1 sample at 8 kHz, below the PCM byte capacity.
    raw = b"\\x00\\x00" * (8_000 * 120 + 1)
    with pytest.raises(OfflineResampleRejected, match="duration"):
        resample_pcm16(raw, "0" * 64, 8_000, 8_000)


def test_derived_output_budget_precedes_digest_comparison():
    # This valid-duration input expands past the 2-MiB output allocation cap.
    raw = b"\\x00\\x00" * 200_000
    with pytest.raises(OfflineResampleRejected, match="output"):
        resample_pcm16(raw, "0" * 64, 8_000, 48_000)


def test_excessive_hash_label_rejected_without_content_comparison():
    raw = struct.pack("<h", 7)
    with pytest.raises(OfflineResampleRejected, match="invalid source digest"):
        resample_pcm16(raw, "a" * 2_000_000, 8_000, 8_000)


def test_admitted_audio_still_binds_the_actual_source_hash():
    raw = struct.pack("<hh", -32768, 32767)
    result = resample_pcm16(raw, hashlib.sha256(raw).hexdigest(), 8_000, 16_000)
    assert result.source_samples == 2
    assert result.output_samples == 4
    assert result.output_sha256 == hashlib.sha256(result.pcm).hexdigest()
