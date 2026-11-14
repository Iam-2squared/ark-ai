"""Detached PCM activity never invokes a shadowed sum or accepts wide SHA."""

from __future__ import annotations

import builtins
import hashlib
import struct

import pytest

import ark.offline_pcm_activity_regions as activity


def _fixture():
    pcm = struct.pack("<hhhh", 1200, -1200, 0, 1000)
    digest = hashlib.sha256(pcm).hexdigest()
    report = activity.detect_activity_regions(pcm, digest, 8000)
    assert report.active_frame_count == 1
    return pcm, digest, report


@pytest.mark.parametrize("entry", ("detect", "verify"))
@pytest.mark.parametrize("surface", ("module", "builtins"))
def test_replaced_sum_is_denied_before_private_pcm_decoding(
    monkeypatch, entry, surface,
):
    pcm, digest, report = _fixture()
    called = []

    def malicious(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("private PCM energy reached untrusted sum")

    with monkeypatch.context() as patch:
        if surface == "module":
            patch.setitem(activity.__dict__, "sum", malicious)
        else:
            patch.setattr(builtins, "sum", malicious)
        with pytest.raises(activity.OfflineActivityRejected, match="codec or digest"):
            if entry == "detect":
                activity.detect_activity_regions(pcm, digest, 8000)
            else:
                activity.verify_activity_regions(report, pcm, digest, 8000)
    assert called == []


@pytest.mark.parametrize("size", (0, 63, 65, 65_536))
@pytest.mark.parametrize("entry", ("detect", "verify"))
def test_exact_digest_width_rejected_without_audio_processing(entry, size):
    pcm, _, report = _fixture()
    with pytest.raises(activity.OfflineActivityRejected, match="digest"):
        if entry == "detect":
            activity.detect_activity_regions(pcm, "a" * size, 8000)
        else:
            activity.verify_activity_regions(report, pcm, "a" * size, 8000)


def test_original_pcm_activity_is_still_verifiable():
    pcm, digest, report = _fixture()
    assert report.source_sha256 == digest
    assert report.regions[0].start_sample == 0
    assert activity.verify_activity_regions(report, pcm, digest, 8000) is None
