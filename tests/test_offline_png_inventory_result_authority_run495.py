"""Disconnected PNG metadata is neither consent nor sensor provenance."""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as png


def _chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data)) + kind + data
        + struct.pack(">I", zlib.crc32(kind + data))
    )


def _request() -> png.OfflinePngRequest:
    header = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    content = (
        b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", b"synthetic-not-decoded")
        + _chunk(b"IEND", b"")
    )
    return png.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(content).hexdigest(), content,
    )


def test_valid_synthetic_inventory_remains_non_authorizing():
    result = png.inspect_disconnected_png(_request())
    assert result.width == result.height == 1
    assert result.consent_verified is False
    assert result.capture_provenance_verified is False
    assert result.decoded_pixels_verified is False
    assert result.context_release_authorized is False


@pytest.mark.parametrize(
    "property_name",
    (
        "decoded_pixels_verified", "capture_provenance_verified",
        "consent_verified", "context_release_authorized",
    ),
)
def test_reflected_png_authority_is_denied(monkeypatch, property_name):
    monkeypatch.setattr(
        png._INVENTORY_TYPE, property_name, property(lambda self: True),
    )
    with pytest.raises(png.OfflinePngRejected, match="claims authority"):
        png.inspect_disconnected_png(_request())


def test_constructor_replacement_cannot_forge_inventory(monkeypatch):
    monkeypatch.setattr(png, "OfflinePngInventory", lambda *args: object())
    with pytest.raises(png.OfflinePngRejected, match="constructed PNG inventory"):
        png.inspect_disconnected_png(_request())


def test_constructor_cannot_relabel_output(monkeypatch):
    original = png._INVENTORY_TYPE

    def swap(*args):
        result = original(*args)
        object.__setattr__(result, "source_sha256", "f" * 64)
        return result

    monkeypatch.setattr(png, "OfflinePngInventory", swap)
    with pytest.raises(png.OfflinePngRejected, match="constructed PNG inventory"):
        png.inspect_disconnected_png(_request())


def test_last_authority_getter_cannot_change_retained_privacy(monkeypatch):
    request = _request()

    def forged(self):
        object.__setattr__(request, "privacy_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        png._INVENTORY_TYPE, "context_release_authorized", property(forged),
    )
    with pytest.raises(png.OfflinePngRejected, match="carrier changed"):
        png.inspect_disconnected_png(request)


def test_last_authority_getter_cannot_rewrite_result_hash(monkeypatch):
    def forged(self):
        object.__setattr__(self, "source_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        png._INVENTORY_TYPE, "context_release_authorized", property(forged),
    )
    with pytest.raises(png.OfflinePngRejected, match="constructed PNG inventory"):
        png.inspect_disconnected_png(_request())
