"""PCM alignment rejects altered handlers before exposing private PCM bytes.

All inputs are synthetic; there is no ASR, real audio capture, consent, or tool.
"""
from __future__ import annotations

import pytest

import ark.offline_activity_transcript_overlap as align


def _invalid_fixture():
    # Deliberately malformed metadata: original-callback preflight must reject
    # instrumentation BEFORE reaching even the normal input-shape exception.
    return align.review_offline_activity_transcript_overlap(
        b"private-synthetic-pcm-contents", "a" * 64, object(), object(),
        (), retained_transcript_fingerprint="b" * 64,
    )


@pytest.mark.parametrize("handler", ("sha256", "dumps", "verifier"))
def test_substituted_alignment_callback_cannot_observe_fixture_pcm(
    monkeypatch, handler,
):
    intercepted = []

    def intercept(*_args, **_kwargs):
        intercepted.append(True)
        raise AssertionError("private PCM must not reach a substituted callback")

    with monkeypatch.context() as patch:
        if handler == "sha256":
            patch.setattr(align.hashlib, "sha256", intercept)
        elif handler == "dumps":
            patch.setattr(align.json, "dumps", intercept)
        else:
            patch.setattr(align.activity_module, "verify_activity_regions", intercept)
        with pytest.raises(
            align.OfflineAlignmentRejected,
            match="original alignment authority changed",
        ):
            _invalid_fixture()
    assert intercepted == []


@pytest.mark.parametrize("target", ("domain", "constructor", "denial"))
def test_result_domain_constructor_or_authority_retarget_rejected_preaccess(
    monkeypatch, target,
):
    intercepted = []

    def intercept(*_args, **_kwargs):
        intercepted.append(True)
        raise AssertionError("substituted alignment constructor executed")

    with monkeypatch.context() as patch:
        if target == "domain":
            patch.setattr(align, "_DOMAIN", b"invalid-alignment-domain")
        elif target == "constructor":
            patch.setattr(align.OfflineActivityTranscriptOverlap, "__init__", intercept)
        else:
            patch.setattr(
                align.OfflineActivityTranscriptOverlap,
                "consent_verified", property(lambda _self: False),
            )
        with pytest.raises(
            align.OfflineAlignmentRejected,
            match="original alignment authority changed",
        ):
            _invalid_fixture()
    assert intercepted == []


def test_restored_callback_contract_reaches_original_input_shape_rejection():
    with pytest.raises(
        align.OfflineAlignmentRejected, match="exact local alignment inputs required",
    ):
        _invalid_fixture()
