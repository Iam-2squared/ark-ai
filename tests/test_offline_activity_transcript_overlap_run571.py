"""Bounded synthetic PCM region-span/transcript overlap, no grant or ASR."""

import hashlib
import struct

import pytest

from ark import offline_activity_transcript_overlap as overlap
from ark import offline_pcm_activity_regions as activity
from ark import offline_transcript_binding as binding


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _fixture(samples=None):
    if samples is None:
        samples = [1200] * 160 + [0] * 160
    pcm = struct.pack("<" + "h" * len(samples), *samples)
    digest = _sha(pcm)
    report = activity.detect_activity_regions(pcm, digest, 8_000)
    audio = binding.AudioMetadataClaim("a" * 64, "b" * 64, digest, 8_000, len(samples))
    segments = (
        binding.TranscriptSegmentClaim(0, 80, "und", _sha(b"alpha"), "alpha"),
        binding.TranscriptSegmentClaim(160, len(samples), "en", _sha(b"beta"), "beta"),
    )
    retained = binding.review_audio_transcript_binding(audio, segments).fingerprint
    return pcm, digest, report, audio, segments, retained


def _review(inputs, **changes):
    pcm, digest, report, audio, segments, retained = inputs
    return overlap.review_offline_activity_transcript_overlap(
        pcm, digest, report, audio, segments,
        retained_transcript_fingerprint=changes.pop("retained", retained),
        **changes,
    )


def test_synthetic_pcm_transcript_overlap_is_deterministic_and_redacted():
    fixtures = _fixture()
    a = _review(fixtures)
    b = _review(fixtures)
    assert a == b
    assert a.activity_region_count == 1
    assert a.transcript_segment_count == 2
    assert a.region_span_samples == 160
    assert a.transcript_overlap_samples == 80
    assert a.uncovered_region_span_samples == 80
    assert a.regions_with_overlap == 1
    assert a.overlap_ppm == 500_000
    assert len(a.alignment_sha256) == 64
    assert "alpha" not in repr(a) and "beta" not in repr(a)
    assert a.source_authenticated is False
    assert a.consent_verified is False
    assert a.speech_verified is False
    assert a.tool_execution_authorized is False


def test_zero_activity_is_valid_but_not_speech_evidence():
    a = _review(_fixture(samples=[0] * 320))
    assert a.region_span_samples == 0
    assert a.transcript_overlap_samples == 0
    assert a.overlap_ppm == 0


def test_bridged_silence_is_in_region_span_not_verified_speech():
    samples = [1200] * 160 + [0] * 160 + [1200] * 160
    inputs = _fixture(samples=samples)
    a = _review(inputs)
    assert a.region_span_samples == 480
    assert a.transcript_overlap_samples == 400
    assert a.overlap_ppm == 833_333


@pytest.mark.parametrize("variant", ["stale_fingerprint", "wrong_pcm", "altered_report"])
def test_alignment_fails_closed_on_unbound_or_changed_data(variant):
    args = list(_fixture())
    if variant == "stale_fingerprint":
        args[-1] = "0" * 64
    elif variant == "wrong_pcm":
        args[1] = "0" * 64
    else:
        object.__setattr__(args[2], "active_frame_count", 0)
    with pytest.raises(overlap.OfflineAlignmentRejected):
        _review(tuple(args))


@pytest.mark.parametrize("target", ["validator", "transcript", "denial"])
def test_no_import_time_validator_or_authority_spoofing(monkeypatch, target):
    inputs = _fixture()
    if target == "validator":
        monkeypatch.setattr(activity, "verify_activity_regions", lambda *a, **kw: None)
    elif target == "transcript":
        monkeypatch.setattr(
            binding, "review_audio_transcript_binding", lambda *a, **kw: None,
        )
    else:
        monkeypatch.setattr(
            overlap.OfflineActivityTranscriptOverlap, "consent_verified",
            property(lambda self: False),
        )
    with pytest.raises(overlap.OfflineAlignmentRejected, match="authority changed"):
        _review(inputs)


def test_mismatched_audio_sample_count_rejected():
    args = list(_fixture())
    original = args[3]
    args[3] = binding.AudioMetadataClaim(
        original.owner_sha256, original.scope_sha256, original.audio_sha256,
        original.sample_rate_hz, original.frame_count - 1,
    )
    with pytest.raises(overlap.OfflineAlignmentRejected):
        _review(tuple(args))


def test_frame_config_change_requires_recomputed_activity():
    with pytest.raises(overlap.OfflineAlignmentRejected):
        _review(_fixture(), frame_ms=10)
