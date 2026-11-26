"""Regression: sensitive raw bytes and nested wake phrases stay out of repr.

This protects only implicit diagnostics, not asdict, serialization or logging.
"""

import hashlib
import struct
from dataclasses import asdict, fields

from ark.offline_binary_inventory import OfflineBinaryRequest, inventory_offline_binary
from ark.offline_pcm_activity import OfflinePcmActivityRequest, analyze_offline_pcm_activity
from ark.offline_transcript_cues import (
    OfflineCueRequest,
    OfflineWakeCue,
    review_offline_transcript_cues,
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def test_raw_pcm_activity_request_redacts_repr_but_still_analyzes():
    audio = struct.pack("<" + "h" * 160, *([1234] * 160))
    request = OfflinePcmActivityRequest("a" * 64, "b" * 64, digest(audio), audio, 1, 8000, 16)
    for view in (repr(request), str(request), repr((request,))):
        assert "pcm_bytes=" not in view
        assert repr(audio) not in view
    assert next(f for f in fields(request) if f.name == "pcm_bytes").repr is False
    assert request.pcm_bytes is audio
    assert analyze_offline_pcm_activity(request).frame_count == 160


def test_binary_inventory_raw_bytes_redacted_but_inventory_still_valid():
    binary = b"private-fixture-raw-PCM-55"
    request = OfflineBinaryRequest("a" * 64, "b" * 64, digest(binary), binary, 8)
    for view in (repr(request), str(request), repr({"fixture": request})):
        assert "source_bytes=" not in view
        assert repr(binary) not in view
    assert next(f for f in fields(request) if f.name == "source_bytes").repr is False
    assert request.source_bytes is binary
    inventory = inventory_offline_binary(request)
    assert inventory.source_sha256 == digest(binary)
    assert inventory.source_size == len(binary)


def test_nested_wake_cue_phrase_redacted_with_valid_match():
    phrase = "private wake phrase 455"
    transcript = phrase + ", show status"
    cue = OfflineWakeCue("cue_00000001", phrase)
    request = OfflineCueRequest(
        "a" * 64, "b" * 64, digest(transcript.encode()), transcript,
        (cue,), ("cue_00000001",),
    )
    for view in (repr(cue), repr(request), str(request), repr([request])):
        assert phrase not in view
        assert "phrase=" not in view
        assert transcript not in view
    assert next(f for f in fields(cue) if f.name == "phrase").repr is False
    assert cue.phrase == phrase
    outcome = review_offline_transcript_cues(request)
    assert outcome.matched_cue_id == "cue_00000001"
    assert outcome.command_text == "show status"
    assert not outcome.action_authorized


def test_repr_only_does_not_hide_explicit_access_or_serialization():
    binary = b"do-not-export-private-data"
    request = OfflineBinaryRequest("a" * 64, "b" * 64, digest(binary), binary)
    assert asdict(request)["source_bytes"] == binary
    assert request.source_bytes is binary
    assert "source_bytes=" not in repr(request)
