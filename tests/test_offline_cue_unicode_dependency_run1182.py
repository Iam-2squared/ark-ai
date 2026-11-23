"""Run1182: Unicode dependency custody for offline transcript cue parsing."""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_transcript_cues as cues


def _request(
    transcript: str = "Hey ARK, show time",
    *,
    phrase: str = "Hey ARK",
) -> cues.OfflineCueRequest:
    cue = cues.OfflineWakeCue("cue_00000001", phrase)
    return cues.OfflineCueRequest(
        "a" * 64,
        "b" * 64,
        hashlib.sha256(transcript.encode("utf-8")).hexdigest(),
        transcript,
        (cue,),
        (cue.cue_id,),
    )


@pytest.mark.parametrize("control", ("\u0600", "\ufff9", "\U000e0001"))
@pytest.mark.parametrize("field", ("transcript", "phrase"))
def test_offline_cue_parser_rejects_unicode_control_categories(
    control: str, field: str,
) -> None:
    request = (
        _request(transcript="Hey ARK" + control + ", show time")
        if field == "transcript"
        else _request(phrase="Hey" + control + " ARK")
    )
    with pytest.raises(
        cues.OfflineCueRejected,
        match="control or invisible Unicode",
    ):
        cues.review_offline_transcript_cues(request)


def test_replaced_unicode_normalizer_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def forbidden(*_args: object) -> str:
        called.append("normalize")
        raise AssertionError("unreviewed normalizer received transcript text")

    monkeypatch.setattr(cues.unicodedata, "normalize", forbidden)
    with pytest.raises(
        cues.OfflineCueRejected,
        match="Unicode policy changed",
    ):
        cues.review_offline_transcript_cues(_request())
    assert called == []


def test_replaced_unicode_category_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    def forbidden(_character: str) -> str:
        called.append("category")
        raise AssertionError("unreviewed category function received transcript text")

    monkeypatch.setattr(cues.unicodedata, "category", forbidden)
    with pytest.raises(
        cues.OfflineCueRejected,
        match="Unicode policy changed",
    ):
        cues.review_offline_transcript_cues(_request())
    assert called == []
