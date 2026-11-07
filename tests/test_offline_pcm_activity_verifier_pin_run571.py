"""Detached PCM activity verification must not accept a replaced comparator."""

import hashlib
import struct

import pytest

from ark import offline_pcm_activity_regions as activity


def _fixture():
    pcm = struct.pack("<" + "h" * 320, *([1200] * 320))
    digest = hashlib.sha256(pcm).hexdigest()
    report = activity.detect_activity_regions(pcm, digest, 8_000)
    return pcm, digest, report


def test_detached_pcm_activity_baseline():
    pcm, digest, report = _fixture()
    activity.verify_activity_regions(report, pcm, digest, 8_000)
    assert report.active_frame_count == 2


@pytest.mark.parametrize("target", ["detector", "result_type", "region_type"])
def test_original_verifier_dependency_cannot_be_replaced(monkeypatch, target):
    pcm, digest, report = _fixture()
    if target == "detector":
        monkeypatch.setattr(
            activity, "detect_activity_regions", lambda *args, **kwargs: report,
        )
    elif target == "result_type":
        monkeypatch.setattr(activity, "ActivityRegions", type("ForgedRegions", (), {}))
    else:
        monkeypatch.setattr(activity, "ActivityRegion", type("ForgedRegion", (), {}))
    with pytest.raises(activity.OfflineActivityRejected, match="original activity verifier"):
        activity.verify_activity_regions(report, pcm, digest, 8_000)


@pytest.mark.parametrize("field,value", [
    ("sample_rate", 16_000),
    ("active_frame_count", 0),
    ("source_sha256", "0" * 64),
])
def test_detached_pcm_activity_rejects_mutated_report(field, value):
    pcm, digest, report = _fixture()
    object.__setattr__(report, field, value)
    with pytest.raises(activity.OfflineActivityRejected):
        activity.verify_activity_regions(report, pcm, digest, 8_000)


def test_detached_pcm_activity_rejects_forged_recomputed_report(monkeypatch):
    pcm, digest, report = _fixture()
    object.__setattr__(report, "active_frame_count", 0)
    monkeypatch.setattr(
        activity, "detect_activity_regions", lambda *args, **kwargs: report,
    )
    with pytest.raises(activity.OfflineActivityRejected, match="original activity verifier"):
        activity.verify_activity_regions(report, pcm, digest, 8_000)
