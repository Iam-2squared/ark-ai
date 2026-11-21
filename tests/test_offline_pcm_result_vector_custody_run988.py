"""The offline PCM result field and hook vectors are fixed before private PCM."""

import hashlib
import struct

import pytest

from ark import offline_pcm_resample16 as pcm


def _input():
    raw = struct.pack("<hh", 0, 32767)
    return raw, hashlib.sha256(raw).hexdigest()


def test_pcm_fixture_identity_and_halfway_rounding():
    raw, digest = _input()
    unchanged = pcm.resample_pcm16(raw, digest, 8000, 8000)
    assert unchanged.pcm == raw
    assert unchanged.output_sha256 == digest
    result = pcm.resample_pcm16(raw, digest, 8000, 16000)
    assert result.output_samples == 4
    assert result.pcm == struct.pack("<hhhh", 0, 16384, 32767, 32767)
    assert result.output_sha256 == hashlib.sha256(result.pcm).hexdigest()


@pytest.mark.parametrize(
    "tamper",
    [
        "paired_fields",
        "paired_hooks",
        "swapped_original_fields",
        "swapped_original_hooks",
        "result_init",
        "result_pcm_slot",
        "result_symbol",
        "round_helper",
    ],
)
def test_offline_pcm_rejects_result_vector_replacement_before_payload_use(monkeypatch, tamper):
    raw, digest = _input()
    invoked = []

    def malicious(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("replaced result or rounding callback was reached")

    with monkeypatch.context() as m:
        if tamper == "paired_fields":
            m.setattr(pcm, "_RESULT_FIELDS", pcm._RESULT_FIELDS[:-1])
            m.setattr(pcm, "_ORIGINAL_RESULT_FIELDS", pcm._ORIGINAL_RESULT_FIELDS[:-1])
        elif tamper == "paired_hooks":
            m.setattr(pcm, "_RESULT_HOOKS", pcm._RESULT_HOOKS[:-1])
            m.setattr(pcm, "_ORIGINAL_RESULT_HOOKS", pcm._ORIGINAL_RESULT_HOOKS[:-1])
        elif tamper == "swapped_original_fields":
            m.setattr(pcm, "_ORIGINAL_RESULT_FIELDS", pcm._ORIGINAL_RESULT_FIELDS[::-1])
        elif tamper == "swapped_original_hooks":
            m.setattr(pcm, "_ORIGINAL_RESULT_HOOKS", pcm._ORIGINAL_RESULT_HOOKS[::-1])
        elif tamper == "result_init":
            m.setattr(pcm.ResampledPcm, "__init__", malicious)
        elif tamper == "result_pcm_slot":
            m.setattr(pcm.ResampledPcm, "pcm", property(malicious))
        elif tamper == "result_symbol":
            m.setattr(pcm, "ResampledPcm", object)
        elif tamper == "round_helper":
            m.setattr(pcm, "_round_ratio_away_from_zero", malicious)
        with pytest.raises(pcm.OfflineResampleRejected):
            pcm.resample_pcm16(raw, digest, 8000, 16000)
    assert invoked == []
