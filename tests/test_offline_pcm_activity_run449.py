"""Pure audio fixture tests; no microphone, model, network or filesystem input."""

import hashlib
import struct
from dataclasses import replace

import pytest

from ark.offline_pcm_activity import (
    OfflinePcmActivityRejected,
    OfflinePcmActivityRequest,
    analyze_offline_pcm_activity,
)

OWNER = "a" * 64
SCOPE = "b" * 64


def request(pcm=b"\x80" * 160, *, channels=1, bits=8, rate=8000, window_ms=20):
    return OfflinePcmActivityRequest(
        OWNER, SCOPE, hashlib.sha256(pcm).hexdigest(), pcm, channels,
        rate, bits, window_ms,
    )


def test_unsigned_eight_bit_center_and_complete_window():
    result = analyze_offline_pcm_activity(request())
    assert result.frame_count == 160
    assert [(w.start_frame, w.end_frame, w.sample_count, w.peak_absolute,
             w.sum_squares) for w in result.windows] == [(0, 160, 160, 0, 0)]
    assert not result.consent_verified
    assert not result.disclosure_authorized
    assert not result.microphone_provenance_verified
    assert not result.speech_or_speaker_recognized


@pytest.mark.parametrize("value,expected", [(0, 128), (255, 127), (128, 0)])
def test_eight_bit_extremes(value, expected):
    result = analyze_offline_pcm_activity(request(bytes([value])))
    assert result.windows[0].peak_absolute == expected
    assert result.windows[0].sum_squares == expected**2


@pytest.mark.parametrize("bits,minimum", [(16, -(2**15)), (24, -(2**23)),
                                           (32, -(2**31))])
def test_signed_little_endian_minimum(bits, minimum):
    sample = minimum.to_bytes(bits // 8, "little", signed=True)
    result = analyze_offline_pcm_activity(request(sample, bits=bits))
    assert result.windows[0].peak_absolute == -minimum
    assert result.windows[0].sum_squares == minimum**2


def test_stereo_frames_and_partial_tail():
    pcm = struct.pack("<hh", -5, 10) * 161
    result = analyze_offline_pcm_activity(request(pcm, channels=2, bits=16))
    assert [(w.start_frame, w.end_frame, w.sample_count) for w in result.windows] == [
        (0, 160, 320), (160, 161, 2),
    ]
    assert [(w.peak_absolute, w.sum_squares) for w in result.windows] == [
        (10, 160 * 125), (10, 125),
    ]


def test_digest_determinism_and_owner_scope_separation():
    a = analyze_offline_pcm_activity(request())
    b = analyze_offline_pcm_activity(request())
    c = analyze_offline_pcm_activity(replace(request(), privacy_sha256="c" * 64))
    assert a == b
    assert a.inventory_sha256 != c.inventory_sha256
    assert len(a.inventory_sha256) == 64
    assert b"\x80" * 160 not in repr(a).encode()


@pytest.mark.parametrize("change", [
    {"pcm_sha256": "0" * 64}, {"pcm_sha256": "Z" * 64},
    {"owner_sha256": "bad"}, {"privacy_sha256": 123},
    {"pcm_bytes": b""}, {"pcm_bytes": b"\x80" * (2 * 1024 * 1024 + 1)},
    {"pcm_bytes": bytearray(b"\x80")}, {"pcm_bytes": memoryview(b"\x80")},
    {"channels": True}, {"channels": 3},
    {"sample_rate_hz": False}, {"sample_rate_hz": 7999},
    {"sample_rate_hz": 48001}, {"bits_per_sample": True},
    {"bits_per_sample": 12}, {"window_ms": False}, {"window_ms": 0},
    {"window_ms": 110}, {"window_ms": 11},
    {"sample_rate_hz": 8001},
])
def test_rejects_bad_carriers(change):
    with pytest.raises(OfflinePcmActivityRejected):
        analyze_offline_pcm_activity(replace(request(), **change))


def test_rejects_partial_stereo_frame():
    with pytest.raises(OfflinePcmActivityRejected, match="partial"):
        analyze_offline_pcm_activity(request(b"\x80" * 3, channels=2, bits=16))


def test_rejects_too_many_windows_without_silent_truncation():
    pcm = b"\x80" * (8000 * 11)
    with pytest.raises(OfflinePcmActivityRejected, match="budget"):
        analyze_offline_pcm_activity(request(pcm, window_ms=10))


def test_no_external_effect_just_in_memory():
    result = analyze_offline_pcm_activity(request(bytes(range(160))))
    assert type(result.windows) is tuple
    assert sum(w.sample_count for w in result.windows) == result.frame_count


def test_exact_request_type_only():
    with pytest.raises(OfflinePcmActivityRejected):
        analyze_offline_pcm_activity(object())
