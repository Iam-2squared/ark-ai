"""Generated PCM bytes only; conversion never accesses a microphone or file."""

import hashlib
import struct
from dataclasses import replace

import pytest

from ark.offline_pcm_mono16 import (
    OfflinePcmConvertRejected,
    OfflinePcmConvertRequest,
    convert_offline_pcm_mono16,
)

OWNER = "a" * 64
PRIVACY = "b" * 64


def request(data=b"\x00\x00", *, channels=1, rate=16000, bits=16):
    return OfflinePcmConvertRequest(
        OWNER, PRIVACY, hashlib.sha256(data).hexdigest(),
        data, channels, rate, bits,
    )


def samples(result):
    return tuple(value[0] for value in struct.iter_unpack("<h", result.pcm16_mono))


@pytest.mark.parametrize("raw,channels,bits,expected", [
    (b"\x80", 1, 8, (0,)),
    (b"\x00\xff", 1, 8, (-32768, 32512)),
    (b"\x00\x80", 2, 8, (-16384,)),
    (struct.pack("<hhhh", -100, 101, 32767, -32768), 1, 16,
     (-100, 101, 32767, -32768)),
    (struct.pack("<hh", 32767, -32768), 2, 16, (-1,)),
    (b"\x00\x00\x80", 1, 24, (-32768,)),
    (b"\xff\xff\x7f", 1, 24, (32767,)),
    (b"\xff\xff\xff", 1, 24, (-1,)),
    (struct.pack("<i", -(2**31)), 1, 32, (-32768,)),
    (struct.pack("<i", 2**31 - 1), 1, 32, (32767,)),
    (struct.pack("<ii", 2**31 - 1, -(2**31)), 2, 32, (-1,)),
])
def test_exact_conversion(raw, channels, bits, expected):
    out = convert_offline_pcm_mono16(request(raw, channels=channels, bits=bits))
    assert samples(out) == expected
    assert out.frame_count == len(expected)
    assert len(out.pcm16_mono) == 2 * len(expected)
    assert not out.speech_recognized and not out.consent_verified
    assert not out.audio_disclosure_authorized and not out.source_authenticated
    assert out.sample_rate_hz == 16000
    assert out.output_sha256 == hashlib.sha256(out.pcm16_mono).hexdigest()


def test_stereo_mixture_and_full_frame_coverage():
    data = struct.pack("<hhhhhh", -5, 4, 20, -18, 100, 101)
    assert samples(convert_offline_pcm_mono16(request(data, channels=2))) == (-1, 1, 100)


def test_source_identity_binds_inventory_but_not_samples():
    raw = struct.pack("<hh", 7, 8)
    a = convert_offline_pcm_mono16(request(raw))
    b = convert_offline_pcm_mono16(request(raw))
    c = convert_offline_pcm_mono16(replace(request(raw), privacy_sha256="c" * 64))
    assert a == b
    assert a.inventory_sha256 != c.inventory_sha256
    assert c.pcm16_mono == a.pcm16_mono
    assert raw.hex() not in repr(a)
    assert "pcm16_mono=" not in repr(a)
    assert "pcm_bytes=" not in repr(request(raw))


@pytest.mark.parametrize("changes", [
    {"owner_sha256": "bad"}, {"privacy_sha256": None},
    {"source_sha256": "0" * 64}, {"source_sha256": "A" * 64},
    {"pcm_bytes": b""}, {"pcm_bytes": bytearray(b"\x00\x00")},
    {"pcm_bytes": memoryview(b"\x00\x00")},
    {"pcm_bytes": b"\x00" * (2 * 1024 * 1024 + 1)},
    {"channels": 0}, {"channels": 3}, {"channels": True},
    {"sample_rate_hz": 0}, {"sample_rate_hz": 7999},
    {"sample_rate_hz": 48001}, {"sample_rate_hz": False},
    {"bits_per_sample": 0}, {"bits_per_sample": 7},
    {"bits_per_sample": 64}, {"bits_per_sample": True},
])
def test_invalid_source_rejected(changes):
    with pytest.raises(OfflinePcmConvertRejected):
        convert_offline_pcm_mono16(replace(request(), **changes))


@pytest.mark.parametrize("channels,bits,data", [
    (1, 16, b"\x00"), (1, 24, b"\x00\x00"),
    (2, 8, b"\x80"), (2, 32, b"\x00" * 7),
])
def test_partial_frame_rejected(channels, bits, data):
    with pytest.raises(OfflinePcmConvertRejected, match="partial"):
        convert_offline_pcm_mono16(request(data, channels=channels, bits=bits))


def test_duration_rejected_without_truncating():
    raw = b"\x80" * (8000 * 120 + 1)
    with pytest.raises(OfflinePcmConvertRejected, match="duration"):
        convert_offline_pcm_mono16(request(raw, bits=8, rate=8000))


def test_expansion_output_budget_rejected():
    raw = b"\x80" * (1024 * 1024 + 1)
    with pytest.raises(OfflinePcmConvertRejected, match="output"):
        convert_offline_pcm_mono16(request(raw, bits=8, rate=48000))


def test_duration_exact_boundary_valid():
    raw = b"\x80" * (8000 * 120)
    out = convert_offline_pcm_mono16(request(raw, bits=8, rate=8000))
    assert out.frame_count == 8000 * 120
    assert out.pcm16_mono[:20] == b"\x00" * 20


def test_exact_request_and_subclass_rejected():
    class Child(OfflinePcmConvertRequest):
        pass

    with pytest.raises(OfflinePcmConvertRejected):
        convert_offline_pcm_mono16(Child(OWNER, PRIVACY, "0" * 64, b"\x00\x00"))
    with pytest.raises(OfflinePcmConvertRejected):
        convert_offline_pcm_mono16(None)


def test_no_float_or_resampling_and_one_sample_input():
    out = convert_offline_pcm_mono16(request(b"\x80", bits=8, rate=44100))
    assert out.sample_rate_hz == 44100
    assert out.frame_count == 1
    assert out.pcm16_mono == b"\x00\x00"
