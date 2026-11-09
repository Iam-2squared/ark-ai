"""Disconnected PCM output cannot be replaced by a forged result factory."""

import hashlib
import struct

import pytest

import ark.offline_pcm_resample16 as resampler


def _resample():
    raw = struct.pack("<hh", 100, 200)
    return resampler.resample_pcm16(
        raw, hashlib.sha256(raw).hexdigest(), 8000, 16000,
    )


@pytest.mark.parametrize("field,bad", [
    ("source_sha256", "e" * 64),
    ("output_sha256", "f" * 64),
    ("source_rate", 22050),
    ("target_rate", 44100),
    ("source_samples", 3),
    ("output_samples", 5),
    ("pcm", b"changed offline PCM"),
])
def test_swapped_result_factory_cannot_retarget_pcm(monkeypatch, field, bad):
    original_type = resampler._RESULT_TYPE

    def forged_result(*args):
        result = original_type(*args)
        object.__setattr__(result, field, bad)
        return result

    calls = []

    def recording_forgery(*args):
        calls.append(args)
        return forged_result(*args)

    monkeypatch.setattr(resampler, "ResampledPcm", recording_forgery)
    # The newer entry fence rejects the substituted result factory before
    # reading private PCM or executing attacker-controlled constructor code.
    with pytest.raises(resampler.OfflineResampleRejected, match="carrier authority changed"):
        _resample()
    assert calls == []


def test_swapped_result_type_is_rejected(monkeypatch):
    original_type = resampler._RESULT_TYPE

    class ForgedResult(original_type):
        pass

    monkeypatch.setattr(resampler, "ResampledPcm", ForgedResult)
    # A replaced result type is denied at entry rather than constructed.
    with pytest.raises(resampler.OfflineResampleRejected, match="carrier authority changed"):
        _resample()


def test_normal_resampler_returns_exact_digest_bound_pcm():
    result = _resample()
    assert type(result) is resampler._RESULT_TYPE
    assert result.source_samples == 2
    assert result.output_samples == 4
    assert result.output_sha256 == hashlib.sha256(result.pcm).hexdigest()
