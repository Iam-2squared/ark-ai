"""A PNG inventory callback cannot smuggle changed denial descriptors."""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as png


def _chunk(name: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload)) + name + payload
        + struct.pack(">I", zlib.crc32(name + payload))
    )


def _request() -> png.OfflinePngRequest:
    raw = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + _chunk(b"IDAT", b"offline-synthetic-only")
        + _chunk(b"IEND", b"")
    )
    return png.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


@pytest.mark.parametrize(
    "earlier",
    ("decoded_pixels_verified", "capture_provenance_verified", "consent_verified"),
)
def test_last_false_getter_cannot_replace_earlier_denial(
    monkeypatch, earlier,
):
    report_type = png.OfflinePngInventory

    def callback(self):
        monkeypatch.setattr(
            report_type, earlier,
            property(lambda ignored: True),
        )
        return False

    monkeypatch.setattr(
        report_type, "context_release_authorized",
        property(callback),
    )
    with pytest.raises(png.OfflinePngRejected, match="denial descriptor changed"):
        png.inspect_disconnected_png(_request())


def test_last_false_getter_cannot_replace_earlier_denial_with_false(
    monkeypatch,
):
    report_type = png.OfflinePngInventory

    def callback(self):
        monkeypatch.setattr(
            report_type, "decoded_pixels_verified",
            property(lambda ignored: False),
        )
        return False

    monkeypatch.setattr(
        report_type, "context_release_authorized", property(callback),
    )
    with pytest.raises(png.OfflinePngRejected, match="denial descriptor changed"):
        png.inspect_disconnected_png(_request())


def test_valid_fixture_preserves_all_denials():
    report = png.inspect_disconnected_png(_request())
    assert report.width == 1
    assert report.height == 1
    assert report.decoded_pixels_verified is False
    assert report.capture_provenance_verified is False
    assert report.consent_verified is False
    assert report.context_release_authorized is False
