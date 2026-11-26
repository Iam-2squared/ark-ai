import hashlib
import random
import struct
from dataclasses import FrozenInstanceError

import pytest

from ark.offline_pcm_resample16 import (
    MAX_PCM_BYTES,
    OfflineResampleRejected,
    resample_pcm16,
)


def pcm(*samples):
    return struct.pack('<' + 'h' * len(samples), *samples)


def resample(data, source=8000, target=16000):
    return resample_pcm16(data, hashlib.sha256(data).hexdigest(), source, target)


def unpack(data):
    return [x[0] for x in struct.iter_unpack('<h', data)]


@pytest.mark.parametrize('rate', [8000, 16000, 22050, 32000, 44100, 48000])
def test_same_rate_is_bit_exact(rate):
    data = pcm(-32768, -1, 0, 1, 32767)
    result = resample(data, rate, rate)
    assert result.pcm is data
    assert (result.source_samples, result.output_samples) == (5, 5)
    assert result.output_sha256 == result.source_sha256


@pytest.mark.parametrize('value', [-32768, -99, -1, 0, 1, 99, 32767])
def test_single_sample_upsample_preserves_constant(value):
    result = resample(pcm(value))
    assert unpack(result.pcm) == [value, value]


def test_interpolation_halfway_ties_away_from_zero():
    assert unpack(resample(pcm(0, 1)).pcm) == [0, 1, 1, 1]
    assert unpack(resample(pcm(0, -1)).pcm) == [0, -1, -1, -1]


def test_downsampling_is_bounded_and_deterministic():
    assert unpack(resample(pcm(100, 200, 300, 400), 16000, 8000).pcm) == [100, 300]


def test_ceil_output_samples_and_endpoint_clamp():
    result = resample(pcm(100, 200, 300), 16000, 8000)
    assert result.output_samples == 2
    assert unpack(result.pcm) == [100, 300]


def test_metadata_and_immutability():
    result = resample(pcm(100, -100))
    assert result.output_sha256 == hashlib.sha256(result.pcm).hexdigest()
    with pytest.raises(FrozenInstanceError):
        result.pcm = b''


@pytest.mark.parametrize('bad', [None, True, '', b'', b'\x00', bytearray(b'\x00\x00'),
                                 memoryview(b'\x00\x00'), b'\x00' * (MAX_PCM_BYTES + 2)])
def test_invalid_audio_rejected(bad):
    with pytest.raises(OfflineResampleRejected):
        resample_pcm16(bad, hashlib.sha256(b'\x00\x00').hexdigest(), 8000, 8000)


@pytest.mark.parametrize('bad', [None, 1, True, 'A' * 64, '0' * 63, '!' * 64])
def test_invalid_digest_rejected(bad):
    with pytest.raises(OfflineResampleRejected):
        resample_pcm16(pcm(1), bad, 8000, 8000)


@pytest.mark.parametrize('bad', [True, 0, 11025, 96000, 8000.0, '8000'])
def test_invalid_rate_rejected_in_both_positions(bad):
    for source, target in ((bad, 8000), (8000, bad)):
        with pytest.raises(OfflineResampleRejected):
            resample(pcm(1), source, target)


def test_mismatched_real_digest_rejected():
    with pytest.raises(OfflineResampleRejected, match='mismatch'):
        resample_pcm16(pcm(1), hashlib.sha256(pcm(2)).hexdigest(), 8000, 16000)


def test_output_budget_rejected_before_allocation():
    data = b'\x00\x00' * 400000
    with pytest.raises(OfflineResampleRejected, match='output'):
        resample(data, 8000, 48000)


def test_duration_budget_below_input_byte_limit():
    data = b'\x00\x00' * (8000 * 120 + 1)
    with pytest.raises(OfflineResampleRejected, match='duration'):
        resample(data, 8000, 8000)


def test_random_integer_reference_differential():
    rng = random.Random(451)
    for _ in range(240):
        source = rng.choice([8000, 16000, 22050, 32000, 44100, 48000])
        target = rng.choice([8000, 16000, 22050, 32000, 44100, 48000])
        src = [rng.randrange(-32768, 32768) for _ in range(rng.randrange(1, 45))]
        result = resample(pcm(*src), source, target)
        expected = []
        for j in range((len(src) * target + source - 1) // source):
            left, fraction = divmod(j * source, target)
            if left >= len(src) - 1:
                expected.append(src[-1])
                continue
            numerator = src[left] * (target - fraction) + src[left + 1] * fraction
            # Independent nearest integer with symmetric negative handling.
            magnitude = (2 * abs(numerator) + target) // (2 * target)
            expected.append(-magnitude if numerator < 0 else magnitude)
        assert unpack(result.pcm) == expected


def test_repr_cannot_dump_sensitive_raw_pcm():
    result = resample(pcm(5, 10, 15))
    assert 'pcm=' not in repr(result)
    assert repr(result.pcm) not in repr(result)
