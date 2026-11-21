"""Disconnected PNG input-policy limits cannot be retargeted in-process.

No pixels are decoded, no camera used, and no consent or disclosure authority
is claimed from an in-memory fixture's checksum/CRC.
"""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as png


def _request():
    def chunk(kind: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body)) + kind + body
            + struct.pack(">I", zlib.crc32(kind + body))
        )

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", b"synthetic-no-decoding")
        + chunk(b"IEND", b"")
    )
    return png.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(data).hexdigest(), data,
    )


@pytest.mark.parametrize(
    ("name", "value"),
    (
        ("_MAX_SOURCE", 8 * 1024 * 1024 + 1),
        ("_MAX_PIXELS", 4_194_305),
        ("_MAX_SIDE", 4097),
        ("_MAX_CHUNKS", 128),
        ("_MAX_IDATS", 128),
        ("_SIGNATURE", b"incorrect"),
        ("_SHA", object()),
        ("_VALID_DEPTHS", {6: (8, 16, 4)}),
    ),
)
def test_rebound_png_format_contract_rejected_before_private_bytes(
    monkeypatch, name, value,
):
    request = _request()
    with monkeypatch.context() as patch:
        patch.setattr(png, name, value)
        with pytest.raises(
            png.OfflinePngRejected,
            match="framing limits changed before private bytes",
        ):
            png.inspect_disconnected_png(request)


def test_in_place_depth_table_mutation_rejected_and_restored(monkeypatch):
    request = _request()
    with monkeypatch.context() as patch:
        patch.setitem(png._VALID_DEPTHS, 6, (4, 8, 16))
        with pytest.raises(
            png.OfflinePngRejected,
            match="framing limits changed before private bytes",
        ):
            png.inspect_disconnected_png(request)

    result = png.inspect_disconnected_png(request)
    assert (result.width, result.height, result.color_type) == (1, 1, 6)
    assert result.capture_provenance_verified is False
    assert result.consent_verified is False
    assert result.context_release_authorized is False
