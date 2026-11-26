"""Synthetic PNG depth-table tampering must not invoke private-data callbacks.

No pixel decoding, sensor access, consent or disclosure occurs.
"""

from __future__ import annotations

import hashlib
import struct
import zlib

import pytest

import ark.offline_png_inventory as png


def _request() -> png.OfflinePngRequest:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data))
        )

    raw = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", b"disconnected-fixture-no-decoding")
        + chunk(b"IEND", b"")
    )
    return png.OfflinePngRequest(
        "a" * 64, "b" * 64, hashlib.sha256(raw).hexdigest(), raw,
    )


def test_original_depth_table_still_allows_inert_metadata_inventory() -> None:
    inventory = png.inspect_disconnected_png(_request())
    assert (inventory.width, inventory.height, inventory.color_type) == (1, 1, 6)
    assert inventory.decoded_pixels_verified is False
    assert inventory.capture_provenance_verified is False
    assert inventory.consent_verified is False
    assert inventory.context_release_authorized is False


@pytest.mark.parametrize("color_type", (0, 2, 3, 4, 6))
def test_poisoned_depth_value_never_runs_equality_or_iteration(
    monkeypatch: pytest.MonkeyPatch, color_type: int,
) -> None:
    invoked: list[str] = []

    class PoisonedDepths:
        def __eq__(self, other: object) -> bool:
            invoked.append("eq")
            raise AssertionError("depth value equality executed")

        def __ne__(self, other: object) -> bool:
            invoked.append("ne")
            raise AssertionError("depth value inequality executed")

        def __iter__(self):
            invoked.append("iter")
            raise AssertionError("depth table value iterated")

    with monkeypatch.context() as patch:
        patch.setitem(png._VALID_DEPTHS, color_type, PoisonedDepths())
        with pytest.raises(
            png.OfflinePngRejected,
            match="framing limits changed before private bytes",
        ):
            png.inspect_disconnected_png(_request())
    assert invoked == []


def test_equal_value_but_new_depth_tuple_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous = png._VALID_DEPTHS[6]
    replacement = tuple(list(previous))
    assert replacement == previous
    assert replacement is not previous
    with monkeypatch.context() as patch:
        patch.setitem(png._VALID_DEPTHS, 6, replacement)
        with pytest.raises(
            png.OfflinePngRejected,
            match="framing limits changed before private bytes",
        ):
            png.inspect_disconnected_png(_request())


def test_non_integer_extra_depth_key_fails_without_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setitem(png._VALID_DEPTHS, "6", (8,))
        with pytest.raises(
            png.OfflinePngRejected,
            match="framing limits changed before private bytes",
        ):
            png.inspect_disconnected_png(_request())
