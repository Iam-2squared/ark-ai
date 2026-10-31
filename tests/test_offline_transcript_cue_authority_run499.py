"""An inert cue result must not grant authority or substitute command bytes."""

import hashlib

import pytest

import ark.offline_transcript_cues as cues


def _review():
    transcript = "Hey ARK, show time"
    return cues.review_offline_transcript_cues(cues.OfflineCueRequest(
        "a" * 64, "b" * 64,
        hashlib.sha256(transcript.encode()).hexdigest(),
        transcript,
        (cues.OfflineWakeCue("cue_00000001", "Hey ARK"),),
        ("cue_00000001",),
    ))


@pytest.mark.parametrize("name,bad", [
    ("matched_cue_id", "cue_00000002"),
    ("command_sha256", "f" * 64),
    ("command_text", "send private data"),
    ("cue_inventory_sha256", "f" * 64),
    ("result_sha256", "e" * 64),
])
def test_constructor_cannot_replace_detached_cue_fields(monkeypatch, name, bad):
    original_type = cues._RESULT_TYPE

    def forged_result(*args):
        result = original_type(*args)
        object.__setattr__(result, name, bad)
        return result

    monkeypatch.setattr(cues, "OfflineCueResult", forged_result)
    with pytest.raises(cues.OfflineCueRejected, match="result carrier changed"):
        _review()


def test_constructor_cannot_return_subclass(monkeypatch):
    class Forged(cues._RESULT_TYPE):
        pass

    monkeypatch.setattr(cues, "OfflineCueResult", Forged)
    with pytest.raises(cues.OfflineCueRejected, match="result carrier changed"):
        _review()


@pytest.mark.parametrize("property_name", [
    "speaker_authenticated",
    "microphone_provenance_verified",
    "action_authorized",
    "consent_verified",
])
def test_cue_preview_never_claims_permission(monkeypatch, property_name):
    monkeypatch.setattr(
        cues.OfflineCueResult, property_name, property(lambda self: True),
    )
    with pytest.raises(cues.OfflineCueRejected, match="authority"):
        _review()


@pytest.mark.parametrize("property_name", [
    "speaker_authenticated",
    "microphone_provenance_verified",
    "action_authorized",
    "consent_verified",
])
def test_late_authority_callback_mutation_is_detected(monkeypatch, property_name):
    def forged_getter(self):
        object.__setattr__(self, "command_text", "exfiltrate private data")
        return False

    monkeypatch.setattr(cues.OfflineCueResult, property_name,
                        property(forged_getter))
    with pytest.raises(cues.OfflineCueRejected, match="result carrier changed"):
        _review()


def test_detached_cue_remains_denial_only():
    result = _review()
    assert result.command_text == "show time"
    assert result.matched_cue_id == "cue_00000001"
    assert not result.speaker_authenticated
    assert not result.microphone_provenance_verified
    assert not result.action_authorized
    assert not result.consent_verified
