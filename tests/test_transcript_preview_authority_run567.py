"""Detached transcript preview authority and output must remain passive.

No media decoding, ASR, consent, device origin or tool execution is performed.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import offline_transcript_binding as mod


def _case():
    text = "hello"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    audio = mod.AudioMetadataClaim(
        "a" * 64, "b" * 64, "c" * 64, 16_000, 16_000,
    )
    segment = mod.TranscriptSegmentClaim(0, 80, "en", digest, text)
    return audio, (segment,)


@pytest.mark.parametrize("flag", mod._PREVIEW_DENIAL_NAMES)
@pytest.mark.parametrize("assertion", (False, True))
def test_substituted_preview_authority_refused_before_text(
    monkeypatch, flag, assertion,
):
    audio, segments = _case()
    called = []

    def forbidden_text(_value):
        called.append(True)
        raise AssertionError("transcript text must not be processed")

    monkeypatch.setattr(mod, "_safe_text", forbidden_text)
    monkeypatch.setattr(
        mod.TranscriptBindingPreview, flag,
        property(lambda _self: assertion),
    )
    with pytest.raises(
        mod.TranscriptBindingRejected,
        match="transcript preview authority definition changed",
    ):
        mod.review_audio_transcript_binding(audio, segments)
    assert called == []


def test_false_denial_callback_cannot_change_result_fingerprint():
    audio, segments = _case()
    original = mod.TranscriptBindingPreview.__getattribute__
    invoked = []

    def change_on_denial(self, name):
        invoked.append(name)
        value = original(self, name)
        if name == "user_consent_proven":
            object.__setattr__(self, "fingerprint", "f" * 64)
        return value

    # The original preaccess check now rejects this *before* the changed
    # lookup callback runs. Restore the inherited hook by removing the own
    # class attribute, rather than monkeypatching back object.__getattribute__.
    assert "__getattribute__" not in vars(mod.TranscriptBindingPreview)
    try:
        mod.TranscriptBindingPreview.__getattribute__ = change_on_denial
        with pytest.raises(
            mod.TranscriptBindingRejected,
            match="transcript carrier definition changed",
        ):
            mod.review_audio_transcript_binding(audio, segments)
    finally:
        delattr(mod.TranscriptBindingPreview, "__getattribute__")
    assert invoked == []


def test_original_preview_still_hash_only_and_non_authorizing():
    audio, segments = _case()
    report = mod.review_audio_transcript_binding(audio, segments)
    assert report.fingerprint == mod.review_audio_transcript_binding(
        audio, segments,
    ).fingerprint
    assert report.segment_count == 1
    assert report.first_frame == 0
    assert report.final_frame == 80
    assert report.audio_sha256 == "c" * 64
    assert "hello" not in repr(report)
    for flag in mod._PREVIEW_DENIAL_NAMES:
        assert getattr(report, flag) is False
