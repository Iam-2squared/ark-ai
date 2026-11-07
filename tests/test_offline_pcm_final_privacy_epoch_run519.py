"""Offline PCM output cannot gain authority or drift at the last callback."""

import hashlib

import pytest

import ark.offline_pcm_mono16 as pcm


def fixture():
    raw = b"\x01\x00\x02\x00"
    return pcm.OfflinePcmConvertRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(),
        raw, channels=1, sample_rate_hz=16000, bits_per_sample=16,
    )


def test_original_pcm_result_keeps_exact_private_source_without_authority():
    request = fixture()
    result = pcm.convert_offline_pcm_mono16(request)
    assert result.pcm16_mono == request.pcm_bytes
    assert result.owner_sha256 == request.owner_sha256
    assert result.privacy_sha256 == request.privacy_sha256
    assert result.source_sha256 == request.source_sha256
    assert result.output_sha256 == hashlib.sha256(request.pcm_bytes).hexdigest()
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.audio_disclosure_authorized is False
    assert result.speech_recognized is False
    assert "pcm16_mono=" not in repr(result)


@pytest.mark.parametrize(
    "flag",
    (
        "source_authenticated", "consent_verified",
        "audio_disclosure_authorized", "speech_recognized",
    ),
)
def test_forged_audio_permission_or_recognition_is_rejected(monkeypatch, flag):
    monkeypatch.setattr(
        pcm.OfflinePcmMono16, flag, property(lambda _: True),
    )
    with pytest.raises(pcm.OfflinePcmConvertRejected, match="acquired authority"):
        pcm.convert_offline_pcm_mono16(fixture())


@pytest.mark.parametrize(
    "target",
    (
        "owner_sha256", "privacy_sha256", "source_sha256",
        "output_sha256", "inventory_sha256", "pcm16_mono",
        "sample_rate_hz", "frame_count",
    ),
)
def test_final_false_audio_denial_cannot_replace_output_epoch(
    monkeypatch, target,
):
    changed = []

    def mutate_after_last_check(result):
        original = getattr(result, target)
        if type(original) is str:
            replacement = ("x" + original)[1:]
            assert replacement == original and replacement is not original
        elif type(original) is bytes:
            replacement = bytes(bytearray(original))
            assert replacement == original and replacement is not original
        else:
            replacement = original + 1
        object.__setattr__(result, target, replacement)
        changed.append(True)
        return False

    monkeypatch.setattr(
        pcm.OfflinePcmMono16, "speech_recognized",
        property(mutate_after_last_check),
    )
    with pytest.raises(pcm.OfflinePcmConvertRejected, match="result changed"):
        pcm.convert_offline_pcm_mono16(fixture())
    assert changed


def test_audio_source_retargeting_by_false_denial_fails(monkeypatch):
    request = fixture()

    def retarget_source(_):
        original = request.privacy_sha256
        replacement = ("x" + original)[1:]
        assert replacement == original and replacement is not original
        object.__setattr__(request, "privacy_sha256", replacement)
        return False

    monkeypatch.setattr(
        pcm.OfflinePcmMono16, "speech_recognized",
        property(retarget_source),
    )
    with pytest.raises(pcm.OfflinePcmConvertRejected, match="request changed"):
        pcm.convert_offline_pcm_mono16(request)


def test_substituted_result_constructor_cannot_forge_equal_output_carrier(monkeypatch):
    original = pcm.OfflinePcmMono16

    def forged(*args):
        result = original(*args)
        data = bytes(bytearray(result.pcm16_mono))
        assert data == result.pcm16_mono and data is not result.pcm16_mono
        object.__setattr__(result, "pcm16_mono", data)
        return result

    monkeypatch.setattr(pcm, "OfflinePcmMono16", forged)
    with pytest.raises(pcm.OfflinePcmConvertRejected, match="result changed"):
        pcm.convert_offline_pcm_mono16(fixture())
