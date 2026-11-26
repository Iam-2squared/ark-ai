"""PNG fixture metadata must not execute forged authority getters or constructors."""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as png


def _chunk(kind: bytes, body: bytes) -> bytes:
    return (
        struct.pack(">I", len(body)) + kind + body
        + struct.pack(">I", zlib.crc32(kind + body))
    )


def _request() -> png.OfflinePngRequest:
    raw = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + _chunk(b"IDAT", b"synthetic-fixture-not-decoded")
        + _chunk(b"IEND", b"")
    )
    return png.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


@pytest.mark.parametrize("name", (
    "decoded_pixels_verified", "capture_provenance_verified",
    "consent_verified", "context_release_authorized",
))
def test_forged_false_denial_never_runs(monkeypatch, name):
    called = []
    def counterfeit(_self):
        called.append(name)
        return False

    monkeypatch.setattr(png.OfflinePngInventory, name, property(counterfeit))
    with pytest.raises(png.OfflinePngRejected, match="denial descriptor changed"):
        png.inspect_disconnected_png(_request())
    assert called == []


def test_copied_descriptor_class_never_constructs(monkeypatch):
    original = png._INVENTORY_TYPE
    called = []

    class Counterfeit:
        decoded_pixels_verified = vars(original)["decoded_pixels_verified"]
        capture_provenance_verified = vars(original)["capture_provenance_verified"]
        consent_verified = vars(original)["consent_verified"]
        context_release_authorized = vars(original)["context_release_authorized"]

        def __init__(self, *_args):
            called.append(True)
            raise AssertionError("counterfeit constructor must not execute")

    monkeypatch.setattr(png, "OfflinePngInventory", Counterfeit)
    with pytest.raises(
        png.OfflinePngRejected,
        match="constructed PNG inventory field, constructor or lookup changed",
    ):
        png.inspect_disconnected_png(_request())
    assert called == []


def test_digest_callback_cannot_install_false_getter(monkeypatch):
    request = _request()
    called = []

    def during_digest(payload=b""):
        called.append(payload)
        raise AssertionError("private PNG bytes reached substituted digest")

    # The stronger preaccess rejection must run before *any* callback, even
    # one that could replace a False-looking approval/consent descriptor.
    with monkeypatch.context() as patch:
        patch.setattr(png.hashlib, "sha256", during_digest)
        with pytest.raises(
            png.OfflinePngRejected, match="digest implementation changed",
        ):
            png.inspect_disconnected_png(request)
    assert called == []


def test_normal_metadata_is_still_inert():
    inventory = png.inspect_disconnected_png(_request())
    assert inventory.width == inventory.height == 1
    assert inventory.decoded_pixels_verified is False
    assert inventory.capture_provenance_verified is False
    assert inventory.consent_verified is False
    assert inventory.context_release_authorized is False
