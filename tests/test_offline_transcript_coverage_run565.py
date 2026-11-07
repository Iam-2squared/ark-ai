"""Detached PNG/WAV transcript interval coverage: metadata, never ASR."""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import replace

import pytest

from ark import offline_transcript_binding as transcript
from ark import offline_transcript_coverage as mod
from ark.offline_pcm_wav import OfflineWaveRequest
from ark.offline_png_inventory import OfflinePngRequest

OWNER = "a" * 64
PRIVACY = "b" * 64


def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data)) + kind + data
        + struct.pack(">I", zlib.crc32(kind + data))
    )


def _case():
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(b"\x00\x00\x00\x00"))
        + _chunk(b"IEND", b"")
    )
    fmt = struct.pack("<HHIIHH", 1, 1, 16000, 32000, 2, 16)
    pcm = b"\x00\x00" * 16
    chunks = (
        b"fmt " + struct.pack("<I", len(fmt)) + fmt
        + b"data" + struct.pack("<I", len(pcm)) + pcm
    )
    wav = b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks
    image = OfflinePngRequest(OWNER, PRIVACY, hashlib.sha256(png).hexdigest(), png)
    audio = OfflineWaveRequest(OWNER, PRIVACY, hashlib.sha256(wav).hexdigest(), wav)
    segments = tuple(
        transcript.TranscriptSegmentClaim(
            start, end, "en", hashlib.sha256(value.encode()).hexdigest(), value,
        )
        for start, end, value in ((0, 4, "hello"), (8, 12, "world"))
    )
    fingerprint = transcript.review_audio_transcript_binding(
        transcript.AudioMetadataClaim(OWNER, PRIVACY, audio.wav_sha256, 16000, 16),
        segments,
    ).fingerprint
    pins = {
        "retained_owner_sha256": OWNER,
        "retained_privacy_sha256": PRIVACY,
        "retained_png_sha256": image.source_sha256,
        "retained_wav_sha256": audio.wav_sha256,
        "retained_transcript_fingerprint": fingerprint,
    }
    return image, audio, segments, pins


def _review(image, audio, segments, pins):
    return mod.review_disconnected_transcript_coverage(
        image, audio, segments, **pins,
    )


def test_interval_accounting_and_private_inert_report():
    image, audio, segments, pins = _case()
    first = _review(image, audio, segments, pins)
    assert type(first) is mod.OfflineTranscriptCoverage
    assert (
        first.audio_frames, first.covered_frames, first.leading_gap_frames,
        first.interior_gap_frames, first.trailing_gap_frames, first.coverage_ppm,
    ) == (16, 8, 0, 4, 4, 500_000)
    assert (first.uncovered_run_count, first.longest_uncovered_run_frames) == (2, 4)
    assert len(first.coverage_sha256) == 64
    assert first == _review(image, audio, segments, pins)
    assert "hello" not in repr(first) and "world" not in repr(first)
    assert all(getattr(first, name) is False for name in mod._DENIALS)


def test_leading_and_trailing_gaps_are_accounted_without_inference():
    image, audio, _, pins = _case()
    spans = (
        transcript.TranscriptSegmentClaim(
            3, 10, "en", hashlib.sha256(b"bounded").hexdigest(), "bounded",
        ),
    )
    pins["retained_transcript_fingerprint"] = transcript.review_audio_transcript_binding(
        transcript.AudioMetadataClaim(OWNER, PRIVACY, audio.wav_sha256, 16000, 16),
        spans,
    ).fingerprint
    report = _review(image, audio, spans, pins)
    assert (
        report.covered_frames, report.leading_gap_frames,
        report.interior_gap_frames, report.trailing_gap_frames,
    ) == (7, 3, 0, 6)
    assert report.coverage_ppm == 437_500
    assert (report.uncovered_run_count, report.longest_uncovered_run_frames) == (2, 6)


@pytest.mark.parametrize("field", (
    "retained_owner_sha256", "retained_privacy_sha256",
    "retained_png_sha256", "retained_wav_sha256",
    "retained_transcript_fingerprint",
))
def test_stale_claims_never_generate_coverage(field):
    image, audio, segments, pins = _case()
    pins[field] = "f" * 64
    with pytest.raises(mod.OfflineCoverageRejected):
        _review(image, audio, segments, pins)


@pytest.mark.parametrize("kind", ("changed_text", "foreign_audio", "bad_spans"))
def test_modified_carriers_are_not_accepted(kind):
    image, audio, segments, pins = _case()
    if kind == "changed_text":
        segments = (replace(segments[0], text="other"), segments[1])
    elif kind == "foreign_audio":
        audio = replace(audio, privacy_sha256="f" * 64)
    else:
        segments = (segments[1], segments[0])
    with pytest.raises(mod.OfflineCoverageRejected):
        _review(image, audio, segments, pins)


@pytest.mark.parametrize("denial", mod._DENIALS)
def test_false_only_authority_replacement_rejected_before_media(monkeypatch, denial):
    image, audio, segments, pins = _case()
    monkeypatch.setattr(mod.OfflineTranscriptCoverage, denial, property(lambda _: False))

    def forbid(*args, **kwargs):
        raise AssertionError("must reject before inspecting media")

    monkeypatch.setattr(mod, "_JOIN", forbid)
    with pytest.raises(mod.OfflineCoverageRejected, match="implementation changed"):
        _review(image, audio, segments, pins)


def test_reentrant_input_mutation_during_pair_reinspection_is_rejected(monkeypatch):
    image, audio, segments, pins = _case()
    original = mod._PAIR

    def mutate(*args, **kwargs):
        value = original(*args, **kwargs)
        object.__setattr__(segments[0], "start_frame", 1)
        return value

    # Original module-level binding is guarded, so there is no media read
    # under a replacement even if it would return a plausible value.
    monkeypatch.setattr(mod, "_PAIR", mutate)
    with pytest.raises(mod.OfflineCoverageRejected, match="implementation changed"):
        _review(image, audio, segments, pins)


@pytest.mark.parametrize(
    ("ranges", "run_count", "longest"),
    (
        (((0, 16),), 0, 0),
        (((0, 4), (5, 6), (10, 16)), 2, 4),
        (((2, 5), (7, 9), (12, 14)), 4, 3),
    ),
)
def test_uncovered_run_counts_are_disjoint_and_receipt_bound(
    ranges, run_count, longest,
):
    image, audio, _, pins = _case()
    spans = tuple(
        transcript.TranscriptSegmentClaim(
            start, end, "en", hashlib.sha256(f"span{i}".encode()).hexdigest(),
            f"span{i}",
        )
        for i, (start, end) in enumerate(ranges)
    )
    pins["retained_transcript_fingerprint"] = transcript.review_audio_transcript_binding(
        transcript.AudioMetadataClaim(OWNER, PRIVACY, audio.wav_sha256, 16000, 16),
        spans,
    ).fingerprint
    report = _review(image, audio, spans, pins)
    assert report.uncovered_run_count == run_count
    assert report.longest_uncovered_run_frames == longest
    assert (
        report.covered_frames + report.leading_gap_frames
        + report.interior_gap_frames + report.trailing_gap_frames
    ) == report.audio_frames == 16
    assert report.coverage_sha256 == _review(image, audio, spans, pins).coverage_sha256
    assert report.tool_execution_authorized is False
