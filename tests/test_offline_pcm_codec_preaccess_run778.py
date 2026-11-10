"""Offline audio codec instrumentation cannot receive private PCM bytes.

All bytes and identities here are synthetic. No microphone, consent, ASR,
external effect, authenticated capture or production audio permission.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_pcm_mono16 as pcm


def _fixture() -> pcm.OfflinePcmConvertRequest:
    raw = bytes((1, 0, 255, 127))
    return pcm.OfflinePcmConvertRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(),
        raw, channels=1, sample_rate_hz=16000, bits_per_sample=16,
    )


@pytest.mark.parametrize("callback", ("sha256", "json.dumps"))
def test_replaced_codec_callback_rejected_before_private_input(
    monkeypatch, callback,
):
    request = _fixture()
    intercepted = []

    def hostile(*args, **kwargs):
        intercepted.append((args, kwargs))
        raise AssertionError("untrusted codec saw private PCM")

    with monkeypatch.context() as patch:
        if callback == "sha256":
            patch.setattr(pcm.hashlib, "sha256", hostile)
        else:
            patch.setattr(pcm.json, "dumps", hostile)
        with pytest.raises(
            pcm.OfflinePcmConvertRejected,
            match="codec authority changed before private bytes",
        ):
            pcm.convert_offline_pcm_mono16(request)
    assert intercepted == []


@pytest.mark.parametrize(
    ("target", "replacement"),
    (
        ("_MAX_INPUT", True),
        ("_MAX_OUTPUT", 2 * 1024 * 1024 + 1),
        ("_MAX_DURATION", 121),
        ("_DOMAIN", b"unreviewed-protocol"),
        ("_SHA", object()),
    ),
)
def test_changed_codec_protocol_or_budget_rejected_before_pcm_read(
    monkeypatch, target, replacement,
):
    request = _fixture()
    with monkeypatch.context() as patch:
        patch.setattr(pcm, target, replacement)
        with pytest.raises(
            pcm.OfflinePcmConvertRejected,
            match="codec authority changed before private bytes",
        ):
            pcm.convert_offline_pcm_mono16(request)


def test_original_codec_remains_deterministic_and_denial_only():
    first = pcm.convert_offline_pcm_mono16(_fixture())
    repeat = pcm.convert_offline_pcm_mono16(_fixture())
    assert first == repeat
    assert first.pcm16_mono == _fixture().pcm_bytes
    assert first.source_authenticated is False
    assert first.consent_verified is False
    assert first.audio_disclosure_authorized is False
    assert first.speech_recognized is False
    assert "pcm16_mono=" not in repr(first)
