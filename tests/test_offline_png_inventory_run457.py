"""Strict disconnected PNG inventory: bounded, content-free, deny-only."""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import FrozenInstanceError

import pytest

from ark.offline_png_inventory import (
    OfflinePngRejected,
    OfflinePngRequest,
    inspect_disconnected_png,
)

OWNER = "a" * 64
PRIVACY = "b" * 64
SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload)) + kind + payload
        + struct.pack(">I", zlib.crc32(kind + payload))
    )


def png(*, w=1, h=1, color=6, depth=8, palette=b"", payload=b"x", extra=()):
    ihdr = struct.pack(">IIBBBBB", w, h, depth, color, 0, 0, 0)
    parts = [chunk(b"IHDR", ihdr)]
    if palette:
        parts.append(chunk(b"PLTE", palette))
    parts.extend(chunk(kind, value) for kind, value in extra)
    return SIGNATURE + b"".join(parts) + chunk(b"IDAT", payload) + chunk(b"IEND", b"")


def review(data, *, owner=OWNER, privacy=PRIVACY, sha=None):
    return inspect_disconnected_png(OfflinePngRequest(
        owner, privacy, sha or hashlib.sha256(data).hexdigest(), data,
    ))


def test_rgba_inventory_has_no_source_or_authorization():
    data = png(payload=b"synthetic-compressed-placeholder")
    result = review(data)
    assert (result.width, result.height, result.color_type, result.bit_depth) == (1, 1, 6, 8)
    assert (result.idat_chunks, result.total_idat_bytes) == (1, 32)
    assert result.idat_sha256 == hashlib.sha256(b"synthetic-compressed-placeholder").hexdigest()
    assert not result.decoded_pixels_verified
    assert not result.capture_provenance_verified
    assert not result.consent_verified
    assert not result.context_release_authorized
    assert OWNER not in repr(result)
    assert PRIVACY not in repr(result)
    assert b"synthetic-compressed-placeholder" not in repr(result).encode()
    with pytest.raises(FrozenInstanceError):
        result.width = 100


def test_indexed_palette_and_grayscale():
    index = review(png(color=3, depth=2, palette=b"\x00\x00\x00\xff\xff\xff"))
    gray = review(png(color=0, depth=1))
    assert (index.color_type, index.bit_depth) == (3, 2)
    assert (gray.color_type, gray.bit_depth) == (0, 1)


@pytest.mark.parametrize("data", [
    b"", b"invalid", png() + b"junk", png()[:-1],
    png().replace(SIGNATURE, b"abcdefgh", 1),
    png(color=3, depth=2),
    png(color=3, depth=1, palette=b"\0" * 9),
    png(color=2, palette=b"\0\0\0"),
    png(w=0), png(h=0), png(w=4097), png(h=4097),
    png(w=4096, h=4096), png(color=5), png(depth=4, color=6),
    png(payload=b""),
    SIGNATURE + chunk(b"IEND", b"") + chunk(b"IHDR", b"\0" * 13),
    png(extra=[(b"tEXt", b"Private note")]),
    png(extra=[(b"eXIf", b"private metadata")]),
    png(extra=[(b"sRGB", b"\0")]),
    png(extra=[(b"PLTE", b"\0\0\0")]),
    SIGNATURE + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
    + chunk(b"IDAT", b"a") + chunk(b"tEXt", b"private")
    + chunk(b"IDAT", b"b") + chunk(b"IEND", b""),
])
def test_noncanonical_or_malformed_rejected(data):
    with pytest.raises(OfflinePngRejected):
        review(data)


def test_multiple_contiguous_idats_accepted():
    data = png(payload=b"AB")
    split = data.replace(chunk(b"IDAT", b"AB"), chunk(b"IDAT", b"A") + chunk(b"IDAT", b"B"))
    result = review(split)
    assert result.idat_chunks == 2
    assert result.idat_sha256 == hashlib.sha256(b"AB").hexdigest()


def test_crc_tamper_rejected_even_if_digest_recomputed():
    data = bytearray(png())
    data[-17] ^= 1
    with pytest.raises(OfflinePngRejected, match="CRC"):
        review(bytes(data))


def test_extra_bytes_and_oversized_chunks_refused():
    data = png()
    changed = data[:8] + b"\xff\xff\xff\xff" + data[12:]
    with pytest.raises(OfflinePngRejected):
        review(changed)
    with pytest.raises(OfflinePngRejected):
        review(data + b"not-a-valid-chunk")


@pytest.mark.parametrize("owner,scope", [
    (True, PRIVACY), (OWNER, None), ("A" * 64, PRIVACY),
    (OWNER, "b" * 63), (OWNER, False),
])
def test_identity_shapes_refused(owner, scope):
    with pytest.raises(OfflinePngRejected):
        review(png(), owner=owner, privacy=scope)


def test_source_digest_required_and_bytes_exact():
    data = png()
    with pytest.raises(OfflinePngRejected, match="source digest"):
        review(data, sha="a" * 64)
    with pytest.raises(OfflinePngRejected):
        inspect_disconnected_png(OfflinePngRequest(OWNER, PRIVACY, "a" * 64, bytearray(data)))
    with pytest.raises(OfflinePngRejected):
        inspect_disconnected_png({"png_bytes": data})


def test_reflected_request_swap_is_rejected(monkeypatch):
    original = OfflinePngRequest(OWNER, PRIVACY, hashlib.sha256(png()).hexdigest(), png())
    original_crc = zlib.crc32

    def callback(value):
        object.__setattr__(original, "privacy_sha256", "c" * 64)
        return original_crc(value)

    monkeypatch.setattr("ark.offline_png_inventory.zlib.crc32", callback)
    with pytest.raises(OfflinePngRejected, match="carrier changed"):
        inspect_disconnected_png(original)
