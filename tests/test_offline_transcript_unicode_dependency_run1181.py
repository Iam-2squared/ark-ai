"""Run1181: Unicode dependency custody for private transcript text."""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_transcript_binding as binding


def _audio() -> binding.AudioMetadataClaim:
    return binding.AudioMetadataClaim(
        "a" * 64, "b" * 64, "c" * 64, 16000, 16000,
    )


def _segment(text: str) -> binding.TranscriptSegmentClaim:
    return binding.TranscriptSegmentClaim(
        0, 100, "ja", hashlib.sha256(text.encode("utf-8")).hexdigest(), text,
    )


@pytest.mark.parametrize("control", ("\u0600", "\ufff9", "\U000e0001"))
def test_transcript_rejects_all_unicode_format_controls(control: str) -> None:
    with pytest.raises(
        binding.TranscriptBindingRejected,
        match="unsafe transcript control",
    ):
        binding.review_audio_transcript_binding(
            _audio(), (_segment("private" + control + "text"),),
        )


def test_replaced_unicode_normalizer_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def forbidden(*_args: object) -> str:
        called.append("normalize")
        raise AssertionError("unreviewed normalizer received transcript text")

    monkeypatch.setattr(binding.unicodedata, "normalize", forbidden)
    with pytest.raises(
        binding.TranscriptBindingRejected,
        match="Unicode policy changed",
    ):
        binding.review_audio_transcript_binding(_audio(), (_segment("private"),))
    assert called == []


def test_replaced_unicode_category_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def forbidden(_character: str) -> str:
        called.append("category")
        raise AssertionError("unreviewed category function received transcript text")

    monkeypatch.setattr(binding.unicodedata, "category", forbidden)
    with pytest.raises(
        binding.TranscriptBindingRejected,
        match="Unicode policy changed",
    ):
        binding.review_audio_transcript_binding(_audio(), (_segment("private"),))
    assert called == []
