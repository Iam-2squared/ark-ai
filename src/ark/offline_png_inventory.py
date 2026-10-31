"""Strict metadata-only PNG inventory for disconnected, synthetic image fixtures.

Never decodes pixels, reads a camera, authenticates consent, or authorizes reuse.
Only a small canonical PNG subset is admitted; all metadata chunks are rejected.
"""

from __future__ import annotations

import hashlib
import re
import struct
import zlib
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MAX_SOURCE = 8 * 1024 * 1024
_MAX_PIXELS = 4_194_304
_MAX_SIDE = 4096
_MAX_CHUNKS = 70
_MAX_IDATS = 64
_VALID_DEPTHS = {
    0: (1, 2, 4, 8, 16),
    2: (8, 16),
    3: (1, 2, 4, 8),
    4: (8, 16),
    6: (8, 16),
}


class OfflinePngRejected(ValueError):
    """Untrusted PNG fixture is malformed, noncanonical, or over budget."""


@dataclass(frozen=True, slots=True)
class OfflinePngRequest:
    owner_sha256: str = field(repr=False)
    privacy_sha256: str = field(repr=False)
    source_sha256: str
    png_bytes: bytes = field(repr=False)


@dataclass(frozen=True, slots=True)
class OfflinePngInventory:
    owner_sha256: str = field(repr=False)
    privacy_sha256: str = field(repr=False)
    source_sha256: str
    idat_sha256: str
    width: int
    height: int
    color_type: int
    bit_depth: int
    idat_chunks: int
    total_idat_bytes: int

    @property
    def decoded_pixels_verified(self) -> bool:
        return False

    @property
    def capture_provenance_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def context_release_authorized(self) -> bool:
        return False


_INVENTORY_TYPE = OfflinePngInventory


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def inspect_disconnected_png(request: OfflinePngRequest) -> OfflinePngInventory:
    """Verify exact bounded PNG framing/CRC, not compressed-pixel validity.

    Admits IHDR, optional indexed PLTE, contiguous IDAT, and final IEND only.
    PNG ancillary chunks, unknown critical chunks, Adam7, and trailing bytes
    are rejected. CRC32 detects accidental chunk corruption, not authenticity.
    """
    if type(request) is not OfflinePngRequest:
        raise OfflinePngRejected("exact PNG request required")
    epoch = (
        request.owner_sha256, request.privacy_sha256,
        request.source_sha256, request.png_bytes,
    )

    def assert_epoch() -> None:
        current = (
            request.owner_sha256, request.privacy_sha256,
            request.source_sha256, request.png_bytes,
        )
        if any(value is not pinned for value, pinned in zip(current, epoch, strict=True)):
            raise OfflinePngRejected("PNG request carrier changed during inspection")

    assert_epoch()
    owner, privacy, declared_digest, data = epoch
    if not all(_sha(x) for x in (owner, privacy, declared_digest)):
        raise OfflinePngRejected("invalid PNG owner, privacy or source digest")
    if type(data) is not bytes or not 8 + 25 + 12 + 13 <= len(data) <= _MAX_SOURCE:
        raise OfflinePngRejected("PNG source must be bounded exact bytes")
    if not data.startswith(_SIGNATURE):
        raise OfflinePngRejected("PNG signature mismatch")
    if hashlib.sha256(data).hexdigest() != declared_digest:
        raise OfflinePngRejected("PNG source digest mismatch")

    cursor = len(_SIGNATURE)
    stage = "HEADER"
    width = height = color = depth = 0
    palette_entries = 0
    idat_count = idat_bytes = 0
    idat_digest = hashlib.sha256()
    chunk_count = 0
    while cursor < len(data):
        assert_epoch()
        chunk_count += 1
        if chunk_count > _MAX_CHUNKS or cursor + 12 > len(data):
            raise OfflinePngRejected("PNG chunk framing/budget invalid")
        size = struct.unpack_from(">I", data, cursor)[0]
        kind = data[cursor + 4:cursor + 8]
        body_start = cursor + 8
        body_end = body_start + size
        if body_end + 4 > len(data):
            raise OfflinePngRejected("PNG chunk exceeds source length")
        recorded_crc = struct.unpack_from(">I", data, body_end)[0]
        calculated_crc = zlib.crc32(memoryview(data)[cursor + 4:body_end])
        if calculated_crc != recorded_crc:
            raise OfflinePngRejected("PNG chunk CRC mismatch")
        payload = memoryview(data)[body_start:body_end]
        cursor = body_end + 4
        if stage == "HEADER":
            if kind != b"IHDR" or size != 13:
                raise OfflinePngRejected("PNG requires first canonical IHDR")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload,
            )
            if (
                not 1 <= width <= _MAX_SIDE
                or not 1 <= height <= _MAX_SIDE
                or width * height > _MAX_PIXELS
                or color not in _VALID_DEPTHS
                or depth not in _VALID_DEPTHS[color]
                or (compression, filtering, interlace) != (0, 0, 0)
            ):
                raise OfflinePngRejected("PNG dimensions/format unsupported")
            stage = "PRE_DATA"
        elif kind == b"PLTE" and stage == "PRE_DATA" and color == 3:
            if palette_entries or size == 0 or size % 3 or size > (1 << depth) * 3:
                raise OfflinePngRejected("PNG indexed palette is malformed")
            palette_entries = size // 3
        elif kind == b"IDAT" and stage in ("PRE_DATA", "DATA"):
            if color == 3 and palette_entries == 0:
                raise OfflinePngRejected("indexed PNG requires palette")
            if size == 0 or idat_count >= _MAX_IDATS:
                raise OfflinePngRejected("PNG IDAT budget invalid")
            idat_digest.update(payload)
            idat_count += 1
            idat_bytes += size
            stage = "DATA"
        elif kind == b"IEND" and stage == "DATA":
            if size != 0 or cursor != len(data):
                raise OfflinePngRejected("PNG requires final empty IEND")
            assert_epoch()
            hashed_idat = idat_digest.hexdigest()
            result = OfflinePngInventory(
                owner, privacy, declared_digest, hashed_idat,
                width, height, color, depth, idat_count, idat_bytes,
            )
            assert_epoch()
            if (
                type(result) is not _INVENTORY_TYPE
                or result.owner_sha256 is not owner
                or result.privacy_sha256 is not privacy
                or result.source_sha256 is not declared_digest
                or result.idat_sha256 is not hashed_idat
                or any(
                    type(value) is not int or value != expected
                    for value, expected in zip(
                        (result.width, result.height, result.color_type,
                         result.bit_depth, result.idat_chunks,
                         result.total_idat_bytes),
                        (width, height, color, depth, idat_count, idat_bytes),
                        strict=True,
                    )
                )
                or result.decoded_pixels_verified is not False
                or result.capture_provenance_verified is not False
                or result.consent_verified is not False
                or result.context_release_authorized is not False
            ):
                raise OfflinePngRejected(
                    "constructed PNG inventory changed or claims authority"
                )
            # Authority getters may execute injected code before returning
            # False; revalidate source and constructed fields afterwards.
            assert_epoch()
            if (
                type(result) is not _INVENTORY_TYPE
                or result.owner_sha256 is not owner
                or result.privacy_sha256 is not privacy
                or result.source_sha256 is not declared_digest
                or result.idat_sha256 is not hashed_idat
                or (result.width, result.height, result.color_type,
                    result.bit_depth, result.idat_chunks,
                    result.total_idat_bytes) != (
                        width, height, color, depth, idat_count, idat_bytes
                    )
            ):
                raise OfflinePngRejected("constructed PNG inventory changed")
            return result
        else:
            raise OfflinePngRejected("unknown, private, or reordered PNG chunk")
    raise OfflinePngRejected("PNG missing final IEND")
