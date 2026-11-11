"""Disconnected PCM request getter custody before sensitive byte access.

Synthetic bytes only; no real device, recognition, consent or dispatch.
A reflected dataclass does not make its class-level getter hooks immutable.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_pcm_mono16 as pcm


def _fixture() -> pcm.OfflinePcmConvertRequest:
    raw = b"\\x01\\x00\\x02\\x00"
    return pcm.OfflinePcmConvertRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(),
        raw, channels=1, sample_rate_hz=16000, bits_per_sample=16,
    )


@pytest.mark.parametrize(
    "slot",
    (
        "owner_sha256", "privacy_sha256", "source_sha256", "pcm_bytes",
        "channels", "sample_rate_hz", "bits_per_sample",
        "__init__", "__new__", "__getattribute__", "__getattr__",
    ),
)
def test_replaced_input_slot_denied_without_reading_private_bytes(
    monkeypatch: pytest.MonkeyPatch, slot: str,
) -> None:
    request = _fixture()
    called: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        called.append(slot)
        raise AssertionError("replaced PCM input accessor executed")

    # Every patched attribute is inspected statically via vars(), not invoked.
    replacement = forbidden if slot.startswith("__") else property(forbidden)
    request_type = pcm.OfflinePcmConvertRequest
    # Pytest restores inherited object.__new__ as an explicit class member;
    # that breaks later legitimate dataclass construction. Reestablish the
    # original *absence* of that hook after this synthetic fault injection.
    original_new_absent = "__new__" not in vars(request_type)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(request_type, slot, replacement, raising=False)
            with pytest.raises(
                pcm.OfflinePcmConvertRejected,
                match="request carrier changed before private bytes",
            ):
                pcm.convert_offline_pcm_mono16(request)
    finally:
        if slot == "__new__" and original_new_absent:
            delattr(request_type, "__new__")
    assert called == []


def test_original_pcm_request_still_converts_without_external_authority() -> None:
    request = _fixture()
    result = pcm.convert_offline_pcm_mono16(request)
    assert result.pcm16_mono == request.pcm_bytes
    assert result.source_sha256 == hashlib.sha256(request.pcm_bytes).hexdigest()
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.audio_disclosure_authorized is False
    assert result.speech_recognized is False
