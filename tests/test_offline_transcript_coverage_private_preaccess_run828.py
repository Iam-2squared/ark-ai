"""No private PNG/WAV/transcript field may be read via a replaced slot.

Use inert, in-memory carrier values only. A refusal does not establish
consent, source provenance, speaker identity, ASR or tool authority.
"""

from __future__ import annotations

import pytest

import ark.offline_transcript_coverage as mod
from ark.offline_pcm_wav import OfflineWaveRequest
from ark.offline_png_inventory import OfflinePngRequest
from ark.offline_transcript_binding import TranscriptSegmentClaim


def _case():
    image = OfflinePngRequest("a" * 64, "b" * 64, "c" * 64, b"private-image")
    audio = OfflineWaveRequest("a" * 64, "b" * 64, "d" * 64, b"private-audio")
    segment = TranscriptSegmentClaim(0, 1, "und", "e" * 64, "private-transcript")
    return (image, audio, (segment,)), {
        "retained_owner_sha256": "a" * 64,
        "retained_privacy_sha256": "b" * 64,
        "retained_png_sha256": "c" * 64,
        "retained_wav_sha256": "d" * 64,
        "retained_transcript_fingerprint": "f" * 64,
    }


@pytest.mark.parametrize(
    ("class_", "field"),
    (
        (OfflinePngRequest, "png_bytes"),
        (OfflinePngRequest, "owner_sha256"),
        (OfflineWaveRequest, "wav_bytes"),
        (OfflineWaveRequest, "privacy_sha256"),
        (TranscriptSegmentClaim, "text"),
        (TranscriptSegmentClaim, "start_frame"),
    ),
)
def test_private_fields_never_read_from_replaced_class_slots(
    monkeypatch: pytest.MonkeyPatch, class_: type, field: str,
) -> None:
    args, options = _case()
    calls: list[str] = []

    def poison(_self: object) -> object:
        calls.append("private field observed")
        raise AssertionError("private slot getter must never run")

    monkeypatch.setattr(class_, field, property(poison))
    with pytest.raises(mod.OfflineCoverageRejected, match="ingress"):
        mod.review_disconnected_transcript_coverage(*args, **options)
    assert calls == []


@pytest.mark.parametrize(
    ("provider", "field"),
    (
        ("png_module", "_require_original_png_authority"),
        ("wave_module", "_require_original_wave_authority"),
        ("binding_module", "_assert_original_binding_carriers"),
    ),
)
def test_swapped_child_validator_cannot_observe_private_carriers(
    monkeypatch: pytest.MonkeyPatch, provider: str, field: str,
) -> None:
    args, options = _case()
    touched: list[str] = []

    def swapped() -> None:
        touched.append("called")
        raise AssertionError("swapped validator must never run")

    monkeypatch.setattr(getattr(mod, provider), field, swapped)
    with pytest.raises(mod.OfflineCoverageRejected, match="dependencies"):
        mod.review_disconnected_transcript_coverage(*args, **options)
    assert touched == []


def test_coverage_refuses_digest_substitution_before_private_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args, options = _case()
    touched: list[str] = []

    def replacement(_value: object) -> object:
        touched.append("hashed")
        raise AssertionError("private content must not enter substituted digest")

    monkeypatch.setattr(mod.hashlib, "sha256", replacement)
    with pytest.raises(mod.OfflineCoverageRejected, match="dependencies"):
        mod.review_disconnected_transcript_coverage(*args, **options)
    assert touched == []
