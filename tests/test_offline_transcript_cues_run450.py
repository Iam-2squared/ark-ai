"""Synthetic text-only cue fixtures. A match must never dispatch a real action."""

import hashlib
from dataclasses import replace

import pytest

from ark.offline_transcript_cues import (
    OfflineCueRejected,
    OfflineCueRequest,
    OfflineWakeCue,
    review_offline_transcript_cues,
)

OWNER = "a" * 64
PRIVACY = "b" * 64
CUES = (OfflineWakeCue("cue_00000001", "Hey ARK"),)


def request(text="Hey ARK, show time", *, cues=CUES, expected=None):
    if expected is None:
        expected = tuple(sorted(c.cue_id for c in cues))
    return OfflineCueRequest(
        OWNER, PRIVACY, hashlib.sha256(text.encode("utf-8")).hexdigest(),
        text, cues, expected,
    )


@pytest.mark.parametrize("input_text,command", [
    ("Hey ARK, show time", "show time"),
    ("hey ark SHOW TIME", "show time"),
    ("Ｈｅｙ ＡＲＫ：日本語", "日本語"),
    ("Hey ARK", None),
    ("HEY ARK!!!", None),
    ("Hey ARK: ##HELLO", "##hello"),
    ("Hey ARK、日本語で説明", "日本語で説明"),
])
def test_match_normalized_text_and_command(input_text, command):
    output = review_offline_transcript_cues(request(input_text))
    assert output.matched_cue_id == "cue_00000001"
    assert output.command_text == command
    assert output.command_sha256 == (
        hashlib.sha256(command.encode("utf-8")).hexdigest() if command else None
    )
    assert not output.action_authorized
    assert not output.speaker_authenticated
    assert not output.microphone_provenance_verified
    assert not output.consent_verified
    assert "command_text=" not in repr(output)


@pytest.mark.parametrize("text", [
    "Not Hey ARK, time", "Hey ARKish, time", "hello", "ARK please", "hey ar", "hey",
    "Hey ARK日本語", "myhey ark", "hey ark_", "hey ark123",
])
def test_non_matching_input_never_becomes_command(text):
    result = review_offline_transcript_cues(request(text))
    assert result.matched_cue_id is None
    assert result.command_text is None
    assert result.command_sha256 is None


def test_japanese_cue_with_separator():
    cues = (OfflineWakeCue("cue_00000003", "アーク"),)
    result = review_offline_transcript_cues(request("アーク、天気", cues=cues))
    assert result.matched_cue_id == "cue_00000003"
    assert result.command_text == "天気"


def test_duplicate_normalized_phrases_rejected():
    cues = (OfflineWakeCue("cue_00000001", "hey ark"),
            OfflineWakeCue("cue_00000002", "ＨＥＹ ＡＲＫ"))
    with pytest.raises(OfflineCueRejected, match="duplicate"):
        review_offline_transcript_cues(request(cues=cues))


def test_prefix_cue_overlap_is_ambiguous_not_best_effort():
    cues = (OfflineWakeCue("cue_00000001", "hey"),
            OfflineWakeCue("cue_00000002", "hey ark"))
    with pytest.raises(OfflineCueRejected, match="ambiguous"):
        review_offline_transcript_cues(request(cues=cues))


def test_results_bind_owner_scope_and_source_hash():
    first = review_offline_transcript_cues(request())
    second = review_offline_transcript_cues(request())
    third = review_offline_transcript_cues(replace(request(), privacy_sha256="c" * 64))
    assert first == second and first != third
    assert first.cue_inventory_sha256 != third.cue_inventory_sha256
    assert len(first.result_sha256) == 64
    assert "show time" not in repr(first)
    assert "show time" not in repr(request())


@pytest.mark.parametrize("changes", [
    {"owner_sha256": "bad"}, {"privacy_sha256": "A" * 64},
    {"transcript_sha256": "0" * 64},
    {"transcript_text": ""},
    {"transcript_text": "Hey ARK\x00 hi"},
    {"transcript_text": "Hey ARK\nhi"},
    {"transcript_text": "Hey ARK\u200b hi"},
    {"transcript_text": "Hey ARK\ud800"},
    {"transcript_text": "x" * 4097},
    {"cues": []}, {"cues": ()},
    {"expected_cue_ids": ()},
    {"expected_cue_ids": ("cue_00000001", "cue_00000002")},
    {"expected_cue_ids": ("bad",)},
])
def test_rejects_bad_carriers(changes):
    with pytest.raises(OfflineCueRejected):
        review_offline_transcript_cues(replace(request(), **changes))


@pytest.mark.parametrize("cue", [
    OfflineWakeCue("cue_00000001", ""),
    OfflineWakeCue("cue_00000001", " hi"),
    OfflineWakeCue("cue_00000001", "hi!"),
    OfflineWakeCue("cue_00000001", "hi "),
    OfflineWakeCue("cue_00000001", "h\x00i"),
    OfflineWakeCue("cue_00000001", "h" * 97),
    OfflineWakeCue("bad", "hi"),
    OfflineWakeCue("cue_00000001", "\ud800"),
])
def test_rejects_invalid_cues(cue):
    with pytest.raises(OfflineCueRejected):
        review_offline_transcript_cues(request(cues=(cue,)))


def test_duplicate_id_rejected():
    cues = (CUES[0], OfflineWakeCue("cue_00000001", "different"))
    with pytest.raises(OfflineCueRejected):
        review_offline_transcript_cues(request(cues=cues))


def test_cue_budget_rejected():
    cues = tuple(OfflineWakeCue(f"cue_{i:08x}", f"phrase {i}") for i in range(9))
    with pytest.raises(OfflineCueRejected, match="budget"):
        review_offline_transcript_cues(request(cues=cues))


def test_exact_types_and_subclasses_rejected():
    class Derived(OfflineCueRequest):
        pass

    with pytest.raises(OfflineCueRejected):
        review_offline_transcript_cues(Derived(
            OWNER, PRIVACY, "0" * 64, "Hey ARK", CUES, ("cue_00000001",),
        ))


def test_exact_tuple_order_required():
    cues = (OfflineWakeCue("cue_00000002", "hi"),
            OfflineWakeCue("cue_00000001", "bye"))
    valid = review_offline_transcript_cues(request("hi there", cues=cues))
    assert valid.matched_cue_id == "cue_00000002"
    with pytest.raises(OfflineCueRejected, match="membership"):
        review_offline_transcript_cues(request("hi there", cues=cues,
                                               expected=("cue_00000002", "cue_00000001")))
