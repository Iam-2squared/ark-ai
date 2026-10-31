"""Independent verification of detached synthetic PCM activity metadata."""

import hashlib
import struct
from dataclasses import replace

import pytest

from ark.offline_pcm_activity_regions import (
    ActivityRegion,
    ActivityRegions,
    OfflineActivityRejected,
    detect_activity_regions,
    verify_activity_regions,
)


def source():
    pcm = struct.pack("<" + "h" * 480, *([900] * 160 + [0] * 160 + [900] * 160))
    digest = hashlib.sha256(pcm).hexdigest()
    report = detect_activity_regions(pcm, digest, 8000)
    return pcm, digest, report


def test_detached_fixture_verification_round_trip():
    pcm, digest, report = source()
    assert verify_activity_regions(report, pcm, digest, 8000) is None
    assert report.active_frame_count == 2
    assert report.regions[0].active_frames == 2


@pytest.mark.parametrize("field,invalid", [
    ("source_sha256", "0" * 64),
    ("sample_rate", 16000),
    ("frame_samples", 320),
    ("total_samples", 99),
    ("active_frame_count", 3),
    ("active_frame_count", True),
    ("regions", []),
])
def test_reject_changed_detached_summary(field, invalid):
    pcm, digest, report = source()
    with pytest.raises(OfflineActivityRejected):
        verify_activity_regions(replace(report, **{field: invalid}), pcm, digest, 8000)


@pytest.mark.parametrize("region", [
    ActivityRegion(0, 3, 0, 480, 3),
    ActivityRegion(0, 3, 0, 479, 2),
    ActivityRegion(0, 3, 0, 480, True),
    ActivityRegion(0, 3, 0, 480, 1),
])
def test_reject_changed_region_identity(region):
    pcm, digest, report = source()
    with pytest.raises(OfflineActivityRejected):
        verify_activity_regions(replace(report, regions=(region,)), pcm, digest, 8000)


def test_reference_digest_and_threshold_must_be_independently_pinned():
    pcm, digest, report = source()
    with pytest.raises(OfflineActivityRejected):
        verify_activity_regions(report, pcm, "f" * 64, 8000)
    with pytest.raises(OfflineActivityRejected):
        verify_activity_regions(report, pcm, digest, 8000, rms_threshold=1000)


def test_reflected_mutation_during_recompute_is_denied(monkeypatch):
    import ark.offline_pcm_activity_regions as module

    pcm, digest, report = source()
    original = module.detect_activity_regions

    def altered(*args, **kwargs):
        object.__setattr__(report, "active_frame_count", 99)
        return original(*args, **kwargs)

    monkeypatch.setattr(module, "detect_activity_regions", altered)
    with pytest.raises(OfflineActivityRejected, match="changed"):
        verify_activity_regions(report, pcm, digest, 8000)


class ForgedActivityRegions(ActivityRegions):
    pass


def test_subclass_and_forged_region_types_are_denied():
    pcm, digest, report = source()
    subclass = ForgedActivityRegions(
        report.source_sha256, report.sample_rate, report.frame_samples,
        report.total_samples, report.active_frame_count, report.regions,
    )
    with pytest.raises(OfflineActivityRejected):
        verify_activity_regions(subclass, pcm, digest, 8000)
    with pytest.raises(OfflineActivityRejected):
        verify_activity_regions(replace(report, regions=(object(),)), pcm, digest, 8000)
