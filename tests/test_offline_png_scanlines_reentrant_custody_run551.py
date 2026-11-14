"""Detached offline scanlines are not authority, including late reentrant getters."""

from __future__ import annotations

import hashlib
import zlib

import pytest

import ark.offline_png_scanlines as png


def _fixture():
    payload = zlib.compress(b"\x00\x04\x09")
    request = png.OfflineScanlineRequest(
        "a" * 64, "b" * 64, hashlib.sha256(payload).hexdigest(),
        payload, 2, 1, 0, 8, 0,
    )
    return request, png.inspect_offline_png_scanlines(request)


@pytest.mark.parametrize("flag", (
    "png_container_verified", "capture_provenance_verified",
    "user_consent_verified", "raw_pixels_released",
    "observation_or_tool_authorized",
))
def test_false_only_replaced_denial_descriptor_is_rejected(monkeypatch, flag):
    request, report = _fixture()
    monkeypatch.setattr(
        png.OfflineScanlineAudit, flag, property(lambda self: False),
    )
    with pytest.raises(png.OfflineScanlineRejected, match="denial descriptor"):
        png.verify_offline_png_scanlines(report, request)


@pytest.mark.parametrize("field,new_value", (
    ("idat_bytes", b"changed fixture IDAT"),
    ("privacy_sha256", "f" * 64),
    ("height", 2),
    ("idat_sha256", "f" * 64),
))
def test_last_false_getter_cannot_rewrite_retained_source(
    monkeypatch, field, new_value,
):
    request, report = _fixture()
    original = png.OfflineScanlineAudit.__getattribute__

    def adversarial(self, name):
        if name == "observation_or_tool_authorized":
            object.__setattr__(request, field, new_value)
            return False
        return original(self, name)

    monkeypatch.setattr(png.OfflineScanlineAudit, "__getattribute__", adversarial)
    with pytest.raises(png.OfflineScanlineRejected, match="source changed"):
        png.verify_offline_png_scanlines(report, request)


def test_last_false_getter_cannot_rewrite_detached_result(monkeypatch):
    request, report = _fixture()
    original = png.OfflineScanlineAudit.__getattribute__

    def adversarial(self, name):
        if name == "observation_or_tool_authorized":
            object.__setattr__(report, "inflated_bytes", 999)
            return False
        return original(self, name)

    monkeypatch.setattr(png.OfflineScanlineAudit, "__getattribute__", adversarial)
    with pytest.raises(png.OfflineScanlineRejected, match="audit changed"):
        png.verify_offline_png_scanlines(report, request)


@pytest.mark.parametrize("replacement", (False, True))
def test_final_getter_cannot_replace_earlier_denial_descriptor(
    monkeypatch, replacement,
):
    request, report = _fixture()
    original = png.OfflineScanlineAudit.__getattribute__

    def adversarial(self, name):
        if name == "observation_or_tool_authorized":
            monkeypatch.setattr(
                png.OfflineScanlineAudit, "png_container_verified",
                property(lambda self: replacement),
            )
            return False
        return original(self, name)

    monkeypatch.setattr(png.OfflineScanlineAudit, "__getattribute__", adversarial)
    with pytest.raises(png.OfflineScanlineRejected, match="denial descriptor"):
        png.verify_offline_png_scanlines(report, request)


def test_unmodified_private_detached_verification_still_succeeds():
    request, report = _fixture()
    assert png.verify_offline_png_scanlines(report, request) is None
    assert report.user_consent_verified is False
    assert report.raw_pixels_released is False
