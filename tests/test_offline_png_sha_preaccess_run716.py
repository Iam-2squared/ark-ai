"""Synthetic PNG inventory rejects replaced SHA-256 before raw byte exposure.

Fixtures are in-memory, disconnected and never decoded into camera pixels.
"""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as inventory


def _png() -> bytes:
    def chunk(kind, body):
        return (
            struct.pack(">I", len(body)) + kind + body
            + struct.pack(">I", zlib.crc32(kind + body))
        )

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", b"synthetic-compressed-placeholder")
        + chunk(b"IEND", b"")
    )


@pytest.mark.parametrize("matching_source_digest", [True, False])
def test_digest_substitution_denied_before_private_png_bytes(
    monkeypatch, matching_source_digest,
):
    data = _png()
    digest = hashlib.sha256(data).hexdigest()
    request = inventory.OfflinePngRequest(
        "a" * 64, "b" * 64,
        digest if matching_source_digest else "0" * 64,
        data,
    )
    calls = []

    def hostile_hash(data=b""):
        calls.append(data)
        raise AssertionError("private PNG bytes reached substituted SHA")

    with monkeypatch.context() as patch:
        patch.setattr(inventory.hashlib, "sha256", hostile_hash)
        with pytest.raises(
            inventory.OfflinePngRejected,
            match="digest implementation changed",
        ):
            inventory.inspect_disconnected_png(request)
    assert calls == []


def test_original_png_hash_metadata_remains_deny_only():
    data = _png()
    request = inventory.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(data).hexdigest(), data,
    )
    report = inventory.inspect_disconnected_png(request)
    assert report.idat_chunks == 1
    assert report.decoded_pixels_verified is False
    assert report.capture_provenance_verified is False
    assert report.consent_verified is False
    assert report.context_release_authorized is False
