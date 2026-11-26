"""Offline PCM amplitude fixture must reject forged carriers before private bytes.

These synthetic examples contain no microphone capture, ASR or consent proof.
"""

from __future__ import annotations

import hashlib
import re
from types import SimpleNamespace

import pytest

import ark.offline_pcm_activity as activity


def _request():
    private_pcm = bytes([0x80]) * 160
    return activity.OfflinePcmActivityRequest(
        "a" * 64, "b" * 64, hashlib.sha256(private_pcm).hexdigest(),
        private_pcm, 1, 8000, 8, 20,
    )


@pytest.mark.parametrize("surface", (
    "sha_module", "sha_callback", "json_module", "json_callback",
    "sha_pattern", "domain", "byte_budget", "window_budget",
    "private_field", "request_lookup", "window_init", "window_field",
    "review_init", "review_denial",
))
def test_hostile_activity_dependency_refused_before_private_audio(
    monkeypatch, surface,
):
    request = _request()
    invoked = []

    def hostile(*_args, **_kwargs):
        invoked.append(True)
        raise AssertionError("hostile activity code accessed private fixture")

    with monkeypatch.context() as patch:
        if surface == "sha_module":
            patch.setattr(activity, "hashlib", SimpleNamespace(sha256=hostile))
        elif surface == "sha_callback":
            patch.setattr(activity.hashlib, "sha256", hostile)
        elif surface == "json_module":
            patch.setattr(activity, "json", SimpleNamespace(dumps=hostile))
        elif surface == "json_callback":
            patch.setattr(activity.json, "dumps", hostile)
        elif surface == "sha_pattern":
            patch.setattr(activity, "_SHA", re.compile(r".*"))
        elif surface == "domain":
            patch.setattr(activity, "_DOMAIN", bytes(bytearray(activity._DOMAIN)))
        elif surface == "byte_budget":
            patch.setattr(activity, "_MAX_BYTES", activity._MAX_BYTES + 1)
        elif surface == "window_budget":
            patch.setattr(activity, "_MAX_WINDOWS", activity._MAX_WINDOWS + 1)
        elif surface == "private_field":
            patch.setattr(activity.OfflinePcmActivityRequest, "pcm_bytes", property(hostile))
        elif surface == "request_lookup":
            patch.setattr(activity.OfflinePcmActivityRequest, "__getattribute__", hostile)
        elif surface == "window_init":
            patch.setattr(activity.OfflinePcmActivityWindow, "__init__", hostile)
        elif surface == "window_field":
            patch.setattr(activity.OfflinePcmActivityWindow, "sum_squares", property(hostile))
        elif surface == "review_init":
            patch.setattr(activity.OfflinePcmActivityReview, "__init__", hostile)
        else:
            patch.setattr(
                activity.OfflinePcmActivityReview, "disclosure_authorized",
                property(hostile),
            )
        with pytest.raises(
            activity.OfflinePcmActivityRejected,
            match="PCM activity codec, carrier or denial authority changed",
        ):
            activity.analyze_offline_pcm_activity(request)
    assert invoked == []


def test_original_activity_analysis_retains_integer_only_deny_all_receipt():
    report = activity.analyze_offline_pcm_activity(_request())
    assert report.frame_count == 160
    assert report.windows[0].peak_absolute == 0
    assert report.windows[0].sum_squares == 0
    assert report.microphone_provenance_verified is False
    assert report.consent_verified is False
    assert report.speech_or_speaker_recognized is False
    assert report.disclosure_authorized is False
    assert len(report.inventory_sha256) == 64
