"""Offline PNG fixture formats/digest widths remain immutable and deny-only."""

from __future__ import annotations

import hashlib
import zlib
from dataclasses import replace

import pytest

import ark.offline_png_scanlines as png


def _fixture() -> tuple[png.OfflineScanlineRequest, png.OfflineScanlineAudit]:
    encoded = zlib.compress(b"\x00\x12\x34")
    source = png.OfflineScanlineRequest(
        "a" * 64, "b" * 64, hashlib.sha256(encoded).hexdigest(),
        encoded, 2, 1, 0, 8, 0,
    )
    return source, png.inspect_offline_png_scanlines(source)


def _review(
    which: str, source: png.OfflineScanlineRequest, report: png.OfflineScanlineAudit,
) -> None:
    if which == "inspect":
        png.inspect_offline_png_scanlines(source)
    else:
        png.verify_offline_png_scanlines(report, source)


@pytest.mark.parametrize("which", ("inspect", "verify"))
@pytest.mark.parametrize("tamper", (
    "depth_extension", "depth_nonprimitive", "channel_count",
    "copied_depth_table", "sha_pattern", "pixel_budget",
))
def test_mutated_format_or_budget_denied_before_private_codec(
    monkeypatch: pytest.MonkeyPatch, which: str, tamper: str,
) -> None:
    source, report = _fixture()
    intercepted = []

    class HostileDepth:
        def __eq__(self, other: object) -> bool:
            intercepted.append(other)
            raise AssertionError("hostile format equality executed")

    class HostilePattern:
        def fullmatch(self, value: str) -> None:
            intercepted.append(value)
            raise AssertionError("hostile digest matcher executed")

    if tamper == "depth_extension":
        monkeypatch.setitem(png._DEPTHS, 2, (1, 8, 16))
    elif tamper == "depth_nonprimitive":
        monkeypatch.setitem(png._DEPTHS, 2, (8, HostileDepth()))
    elif tamper == "channel_count":
        monkeypatch.setitem(png._CHANNELS, 0, 4)
    elif tamper == "copied_depth_table":
        monkeypatch.setattr(png, "_DEPTHS", dict(png._DEPTHS))
    elif tamper == "sha_pattern":
        monkeypatch.setattr(png, "_SHA", HostilePattern())
    else:
        monkeypatch.setattr(png, "_MAX_PIXELS", 2**31)
    with pytest.raises(png.OfflineScanlineRejected, match="codec"):
        _review(which, source, report)
    assert intercepted == []


@pytest.mark.parametrize("which", ("inspect", "verify"))
@pytest.mark.parametrize("field,replacement", (
    ("owner_sha256", "a" * 65),
    ("privacy_sha256", "b" * 100_000),
    ("idat_sha256", "c" * 63),
    ("owner_sha256", "a" * 63 + "\ud800"),
))
def test_inexact_digest_width_or_unicode_denied_before_decompression(
    which: str, field: str, replacement: str,
) -> None:
    source, report = _fixture()
    bad = replace(source, **{field: replacement})
    with pytest.raises(png.OfflineScanlineRejected, match="digest"):
        _review(which, bad, report)


def test_unmodified_fixture_retains_private_denials() -> None:
    source, report = _fixture()
    assert report.inflated_bytes == 3
    assert png.verify_offline_png_scanlines(report, source) is None
    assert report.raw_pixels_released is False
    assert report.user_consent_verified is False
