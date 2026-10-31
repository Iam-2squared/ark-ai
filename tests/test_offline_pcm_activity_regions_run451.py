import hashlib
import struct
from dataclasses import FrozenInstanceError

import pytest

from ark.offline_pcm_activity_regions import (
    MAX_PCM_BYTES,
    OfflineActivityRejected,
    detect_activity_regions,
)


def packed(*values):
    return struct.pack('<' + 'h' * len(values), *values)


def frames(*amplitudes, frame_samples=160):
    return b''.join(packed(*([a] * frame_samples)) for a in amplitudes)


def run(pcm, rate=8000, **kwargs):
    return detect_activity_regions(pcm, hashlib.sha256(pcm).hexdigest(), rate, **kwargs)


def test_silence_is_empty():
    outcome = run(frames(0, 0))
    assert outcome.active_frame_count == 0
    assert outcome.regions == ()
    assert outcome.total_samples == 320


def test_positive_negative_equal_energy():
    a = run(frames(900))
    b = run(frames(-900))
    assert a.regions[0].start_sample == b.regions[0].start_sample == 0
    assert a.regions[0].end_sample == b.regions[0].end_sample == 160


def test_exact_threshold_is_inactive():
    assert run(frames(512)).regions == ()
    assert len(run(frames(513)).regions) == 1


def test_activity_gaps_are_bridged_without_fabricating_active_count():
    result = run(frames(900, 0, 900, 0, 0, 900))
    assert [(x.start_frame, x.end_frame, x.active_frames) for x in result.regions] == [
        (0, 3, 2), (5, 6, 1)
    ]
    assert result.active_frame_count == 3


def test_unbridged_and_minimum_filter():
    pcm = frames(900, 0, 900, 0, 900)
    result = run(pcm, bridge_silence_frames=0, min_active_frames=2)
    assert result.active_frame_count == 3
    assert result.regions == ()


def test_partial_final_frame_not_padded_with_fake_silence():
    pcm = frames(0) + packed(*([1000] * 40))
    result = run(pcm)
    assert result.total_samples == 200
    assert [(r.start_sample, r.end_sample) for r in result.regions] == [(160, 200)]


def test_frame_ms_30_and_nonzero_offsets():
    result = run(frames(0, 900, 900, frame_samples=240), frame_ms=30)
    assert (result.frame_samples, result.regions[0].start_sample) == (240, 240)


def test_full_negative_amplitude():
    assert len(run(frames(-32768), rms_threshold=32767).regions) == 1
    assert run(frames(-32768), rms_threshold=32768).regions == ()


def test_region_limit_fails_closed():
    with pytest.raises(OfflineActivityRejected, match='regions'):
        run(frames(*([900, 0] * 4)), bridge_silence_frames=0, max_regions=2)


def test_immutable_regions_and_metadata():
    result = run(frames(900))
    with pytest.raises(FrozenInstanceError):
        result.regions[0].end_sample = 1
    with pytest.raises(FrozenInstanceError):
        result.total_samples = 1


@pytest.mark.parametrize('bad', [None, '', 'raw', bytearray(b'\x00\x00'), memoryview(b'\x00\x00'),
                                 b'', b'\x00', b'\x00' * (MAX_PCM_BYTES + 2)])
def test_bad_pcm_rejected(bad):
    with pytest.raises(OfflineActivityRejected):
        detect_activity_regions(bad, hashlib.sha256(b'\x00\x00').hexdigest(), 8000)


@pytest.mark.parametrize('bad', [None, 0, True, 'a' * 64, '0' * 63, 'F' * 64, '!' * 64])
def test_bad_digest_rejected(bad):
    with pytest.raises(OfflineActivityRejected):
        detect_activity_regions(frames(0), bad, 8000)


@pytest.mark.parametrize('bad', [True, 0, 11025, 44100, 8000.0, '8000'])
def test_bad_rate_rejected(bad):
    with pytest.raises(OfflineActivityRejected):
        run(frames(0), bad)


@pytest.mark.parametrize('key,bad', [
    ('frame_ms', True), ('frame_ms', 25), ('rms_threshold', True),
    ('rms_threshold', -1), ('rms_threshold', 32769),
    ('bridge_silence_frames', True), ('bridge_silence_frames', -1),
    ('bridge_silence_frames', 11), ('min_active_frames', 0),
    ('min_active_frames', 101), ('min_active_frames', 1.0),
    ('max_regions', 0), ('max_regions', 33), ('max_regions', True),
])
def test_parameter_types_and_budgets(key, bad):
    with pytest.raises(OfflineActivityRejected):
        run(frames(0), **{key: bad})


def test_mismatched_valid_digest_rejected():
    with pytest.raises(OfflineActivityRejected, match='mismatch'):
        detect_activity_regions(frames(0), hashlib.sha256(frames(900)).hexdigest(), 8000)


def test_duration_budget_rejected_below_byte_limit():
    pcm = b'\x00\x00' * (8000 * 120 + 1)
    with pytest.raises(OfflineActivityRejected, match='duration'):
        run(pcm)


def test_frame_threshold_obeys_integer_mean_square():
    pcm = packed(*([1000] * 80 + [0] * 80))
    assert len(run(pcm, rms_threshold=700).regions) == 1
    assert run(pcm, rms_threshold=710).regions == ()
