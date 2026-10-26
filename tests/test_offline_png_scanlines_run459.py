"""Synthetic zlib/PNG scanlines stay bounded and never release raw pixels."""

from dataclasses import FrozenInstanceError, replace
import hashlib
import random
import zlib

import pytest

from ark.offline_png_scanlines import (
    OfflineScanlineRejected, OfflineScanlineRequest, inspect_offline_png_scanlines,
)


def fixture(*, rows=(b"\x00\x10\x20",), width=2, height=1, color=0,
            depth=8, entries=0, compressed=None):
    raw = b"".join(rows)
    payload = zlib.compress(raw) if compressed is None else compressed
    return OfflineScanlineRequest(
        "a" * 64, "b" * 64, hashlib.sha256(payload).hexdigest(), payload,
        width, height, color, depth, entries,
    )


def audit(request):
    return inspect_offline_png_scanlines(request)


def test_valid_unfiltered_grayscale_is_private():
    request = fixture()
    result = audit(request)
    assert result.reconstructed_sha256 == hashlib.sha256(b"\x10\x20").hexdigest()
    assert result.filters_used == (1, 0, 0, 0, 0)
    assert result.inflated_bytes == 3
    assert not result.png_container_verified
    assert not result.capture_provenance_verified
    assert not result.user_consent_verified
    assert not result.raw_pixels_released
    assert not result.observation_or_tool_authorized
    assert request.idat_bytes.hex() not in repr(request)
    assert request.owner_sha256 not in repr(request)
    with pytest.raises(FrozenInstanceError):
        result.height = 3


@pytest.mark.parametrize("filter_code,expected", [
    (0, b"\x01\x02"),
    (1, b"\x01\x03"),
    (2, b"\x01\x02"),
    (3, b"\x01\x02"),
    (4, b"\x01\x03"),
])
def test_first_row_filter_types(filter_code, expected):
    request = fixture(rows=(bytes([filter_code, 1, 2]),))
    assert audit(request).reconstructed_sha256 == hashlib.sha256(expected).hexdigest()


def test_sub_and_up_on_multiple_rows():
    # Row 1 reconstructed 10,20; row 2 filtered UP +2,+4 => 12,24.
    req = fixture(rows=(b"\x00\x0a\x14", b"\x02\x02\x04"), height=2)
    assert audit(req).reconstructed_sha256 == hashlib.sha256(b"\x0a\x14\x0c\x18").hexdigest()


def test_paeth_left_dominant():
    # With no prior row, Paeth predicts left byte on the second position.
    req = fixture(rows=(b"\x04\x05\x06",))
    assert audit(req).reconstructed_sha256 == hashlib.sha256(b"\x05\x0b").hexdigest()


@pytest.mark.parametrize("depth,packed,width,entries", [
    (1, b"\x40", 2, 2),
    (2, b"\x1b", 4, 4),
    (4, b"\x01\x23", 4, 4),
    (8, b"\x00\x01\x02", 3, 3),
])
def test_valid_indexed_palette_values(depth, packed, width, entries):
    req = fixture(rows=(b"\x00" + packed,), width=width, depth=depth,
                  color=3, entries=entries)
    assert audit(req).width == width


@pytest.mark.parametrize("depth,packed,width,entries", [
    (1, b"\xc0", 2, 1),
    (2, b"\xe4", 4, 2),
    (4, b"\x1f", 2, 4),
    (8, b"\x03", 1, 3),
])
def test_undefined_palette_index_is_rejected(depth, packed, width, entries):
    req = fixture(rows=(b"\x00" + packed,), width=width, depth=depth,
                  color=3, entries=entries)
    with pytest.raises(OfflineScanlineRejected, match="palette"):
        audit(req)


def test_rgba16_filter_zero_with_exact_bytes():
    row = bytes(range(16))
    req = fixture(rows=(b"\x00" + row,), width=2, color=6, depth=16)
    assert audit(req).reconstructed_sha256 == hashlib.sha256(row).hexdigest()


@pytest.mark.parametrize("raw", [b"\x05\x00\x00", b"\x00\x10", b"\x00\x01\x02\x03"])
def test_bad_filter_or_row_length(raw):
    with pytest.raises(OfflineScanlineRejected):
        audit(fixture(rows=(raw,)))


def test_concatenated_zlib_stream_denied():
    payload = zlib.compress(b"\x00\x10\x20") * 2
    with pytest.raises(OfflineScanlineRejected, match="trailer"):
        audit(fixture(compressed=payload))


def test_truncated_zlib_and_invalid_adler_denied():
    valid = zlib.compress(b"\x00\x10\x20")
    for invalid in (valid[:-2], valid[:-1] + b"0", b"\x00" * 10):
        with pytest.raises(OfflineScanlineRejected):
            audit(fixture(compressed=invalid))


def test_compressed_expansion_bomb_is_denied():
    payload = zlib.compress(b"\x00" * 10000)
    with pytest.raises(OfflineScanlineRejected, match="trailer"):
        audit(fixture(compressed=payload))


@pytest.mark.parametrize("changes", [
    {"width": True}, {"height": -1}, {"color_type": 1},
    {"bit_depth": 3}, {"palette_entries": 1},
    {"width": 4096, "height": 4096},
    {"width": 0}, {"height": 0},
    {"color_type": 3, "bit_depth": 1, "palette_entries": 0},
])
def test_invalid_geometry_format_or_palette(changes):
    with pytest.raises(OfflineScanlineRejected):
        audit(replace(fixture(), **changes))


def test_wrong_digest_and_broken_identity():
    req = fixture()
    for bad in (replace(req, idat_sha256="0" * 64),
                replace(req, owner_sha256=True),
                replace(req, privacy_sha256="A" * 64)):
        with pytest.raises(OfflineScanlineRejected):
            audit(bad)


def test_reject_subclass_and_mutable_byte_carrier():
    req = fixture()
    with pytest.raises(OfflineScanlineRejected):
        audit(replace(req, idat_bytes=bytearray(req.idat_bytes)))


class Subclass(OfflineScanlineRequest):
    pass


def test_subclass_request_not_accepted():
    req = fixture()
    with pytest.raises(OfflineScanlineRejected):
        audit(Subclass(**{name: getattr(req, name) for name in req.__dataclass_fields__}))


def test_reflective_mutation_during_decode_denied(monkeypatch):
    import ark.offline_png_scanlines as module
    req = fixture()
    original = module.zlib.decompressobj

    def injected(*args, **kwargs):
        object.__setattr__(req, "height", 2)
        return original(*args, **kwargs)

    monkeypatch.setattr(module.zlib, "decompressobj", injected)
    with pytest.raises(OfflineScanlineRejected, match="carrier changed"):
        audit(req)


def test_seeded_random_valid_unfiltered_rows():
    randomizer = random.Random(459)
    for _ in range(200):
        width = randomizer.randint(1, 64)
        height = randomizer.randint(1, 8)
        rows = tuple(b"\x00" + randomizer.randbytes(width) for _ in range(height))
        req = fixture(rows=rows, width=width, height=height)
        digest = hashlib.sha256(b"".join(r[1:] for r in rows)).hexdigest()
        assert audit(req).reconstructed_sha256 == digest
