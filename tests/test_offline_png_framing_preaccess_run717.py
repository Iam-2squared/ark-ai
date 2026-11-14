"""Disallow substituted PNG CRC/framing callbacks before raw fixture access.

These are disconnected synthetic bytes, never camera frames or decoded pixels.
"""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as png


def _fixture() -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload)) + kind + payload
            + struct.pack(">I", zlib.crc32(kind + payload))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", b"offline-synthetic-fixture")
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("valid_digest", (True, False))
@pytest.mark.parametrize("symbol", ("crc32", "unpack", "unpack_from"))
def test_framing_substitution_never_receives_private_png(
    monkeypatch, valid_digest, symbol,
):
    raw = _fixture()
    digest = hashlib.sha256(raw).hexdigest() if valid_digest else "0" * 64
    request = png.OfflinePngRequest("a" * 64, "b" * 64, digest, raw)
    observed = []

    def hostile(*args, **kwargs):
        observed.append((args, kwargs))
        raise AssertionError("substituted framing callback received fixture")

    target = png.zlib if symbol == "crc32" else png.struct
    with monkeypatch.context() as patch:
        patch.setattr(target, symbol, hostile)
        with pytest.raises(
            png.OfflinePngRejected,
            match="framing implementation changed before private bytes",
        ):
            png.inspect_disconnected_png(request)
    assert observed == []


def test_unmodified_png_still_uses_crc_and_remains_non_authorizing():
    raw = _fixture()
    receipt = png.inspect_disconnected_png(png.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    ))
    assert receipt.width == receipt.height == 1
    assert receipt.idat_chunks == 1
    assert receipt.consent_verified is False
    assert receipt.capture_provenance_verified is False
    assert receipt.context_release_authorized is False
