"""Run906: disconnected PCM output's raw bytes and denial descriptors are pinned.

Only synthetic in-memory samples. No microphone, capture, training or export.
A false-valued substituted getter is still executable code and must not run.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import offline_pcm_mono16 as mod


def _request(*, owner="a" * 64):
    raw = b"\x00\x80\xff\x7f"
    return mod.OfflinePcmConvertRequest(
        owner, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


@pytest.mark.parametrize("name", (
    "source_authenticated", "consent_verified",
    "audio_disclosure_authorized", "speech_recognized",
))
def test_substituted_false_denial_getter_is_never_called(monkeypatch, name):
    touched = []

    def injected(self):
        touched.append(self.pcm16_mono)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(mod.OfflinePcmMono16, name, property(injected))
        with pytest.raises(mod.OfflinePcmConvertRejected, match="result carrier"):
            mod.convert_offline_pcm_mono16(_request())
    assert touched == []


@pytest.mark.parametrize("name", ("pcm16_mono", "owner_sha256"))
def test_substituted_raw_or_identity_slot_is_never_accessed(monkeypatch, name):
    touched = []

    def injected(_self):
        touched.append(name)
        return b"intercepted"

    with monkeypatch.context() as patch:
        patch.setattr(mod.OfflinePcmMono16, name, property(injected))
        with pytest.raises(mod.OfflinePcmConvertRejected, match="result carrier"):
            mod.convert_offline_pcm_mono16(_request())
    assert touched == []


@pytest.mark.parametrize("name", ("__init__", "__getattribute__"))
def test_replaced_result_construction_or_lookup_cannot_run(monkeypatch, name):
    touched = []

    def injected(*args, **kwargs):
        touched.append(name)
        raise AssertionError("injected output hook executed")

    with monkeypatch.context() as patch:
        patch.setattr(mod.OfflinePcmMono16, name, injected)
        with pytest.raises(mod.OfflinePcmConvertRejected, match="result carrier"):
            mod.convert_offline_pcm_mono16(_request())
    assert touched == []


def test_substituted_exported_result_name_is_denied(monkeypatch):
    with monkeypatch.context() as patch:
        patch.setattr(mod, "OfflinePcmMono16", object)
        with pytest.raises(mod.OfflinePcmConvertRejected, match="result carrier"):
            mod.convert_offline_pcm_mono16(_request())


def test_huge_claimed_digest_is_rejected_without_regex_scan_or_conversion():
    with pytest.raises(mod.OfflinePcmConvertRejected, match="invalid PCM"):
        mod.convert_offline_pcm_mono16(_request(owner="a" * 1_000_000))


def test_valid_private_pcm_remains_exact_and_unauthed():
    output = mod.convert_offline_pcm_mono16(_request())
    assert output.pcm16_mono == b"\x00\x80\xff\x7f"
    assert output.output_sha256 == hashlib.sha256(output.pcm16_mono).hexdigest()
    assert output.source_authenticated is False
    assert output.consent_verified is False
    assert output.audio_disclosure_authorized is False
    assert output.speech_recognized is False
