"""Nested activity-region custody during detached audio/transcript alignment.

Synthetic local bytes, not authenticated device audio, ASR, or permission.
"""

import hashlib
import struct
from dataclasses import replace

import pytest

from ark import offline_activity_transcript_overlap as alignment
from ark import offline_pcm_activity_regions as activity
from ark import offline_transcript_binding as binding


def fixture():
    pcm = struct.pack("<320h", *([1200] * 160 + [0] * 160))
    digest = hashlib.sha256(pcm).hexdigest()
    report = activity.detect_activity_regions(pcm, digest, 8_000)
    audio = binding.AudioMetadataClaim("a" * 64, "b" * 64, digest, 8_000, 320)
    segments = (
        binding.TranscriptSegmentClaim(
            0, 80, "en", hashlib.sha256(b"alpha").hexdigest(), "alpha",
        ),
    )
    fingerprint = binding.review_audio_transcript_binding(
        audio, segments,
    ).fingerprint
    return pcm, digest, report, audio, segments, fingerprint


def review(args):
    pcm, digest, report, audio, segments, fingerprint = args
    return alignment.review_offline_activity_transcript_overlap(
        pcm, digest, report, audio, segments,
        retained_transcript_fingerprint=fingerprint,
    )


@pytest.mark.parametrize(
    "field",
    ("start_frame", "end_frame", "start_sample", "end_sample", "active_frames"),
)
def test_nested_region_mutation_callback_is_refused_before_invocation(
    monkeypatch, field,
):
    args = fixture()
    region = args[2].regions[0]
    original = alignment.json.dumps
    touched = []
    before = getattr(region, field)

    def mutate(*pos, **kw):
        touched.append(field)
        object.__setattr__(region, field, getattr(region, field) + 1)
        return original(*pos, **kw)

    monkeypatch.setattr(alignment.json, "dumps", mutate)
    with pytest.raises(
        alignment.OfflineAlignmentRejected, match="original alignment authority changed",
    ):
        review(args)
    assert touched == []
    assert getattr(region, field) == before


def test_nested_region_replacement_callback_is_refused_before_invocation(monkeypatch):
    args = fixture()
    report = args[2]
    original = alignment.json.dumps
    original_region = report.regions[0]
    invoked = []

    def mutate(*pos, **kw):
        invoked.append(True)
        object.__setattr__(report, "regions", (replace(report.regions[0]),))
        return original(*pos, **kw)

    monkeypatch.setattr(alignment.json, "dumps", mutate)
    with pytest.raises(
        alignment.OfflineAlignmentRejected, match="original alignment authority changed",
    ):
        review(args)
    assert invoked == []
    assert report.regions[0] is original_region


def test_original_region_carrier_type_cannot_be_rebound(monkeypatch):
    args = fixture()
    monkeypatch.setattr(activity, "ActivityRegion", object)
    with pytest.raises(alignment.OfflineAlignmentRejected, match="authority changed"):
        review(args)


def test_unchanged_nested_region_still_has_deterministic_no_authority_result():
    args = fixture()
    first = review(args)
    assert first == review(args)
    assert first.region_span_samples == 160
    assert first.transcript_overlap_samples == 80
    assert first.speech_verified is False
    assert first.consent_verified is False
    assert first.tool_execution_authorized is False
    assert "alpha" not in repr(first)
