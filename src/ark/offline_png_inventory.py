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


# A substituted digest/framing callback could receive raw private PNG fixture
# bytes before the integrity/authority checks run. Pin callable identities.
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_CRC32 = zlib.crc32
_ORIGINAL_UNPACK = struct.unpack
_ORIGINAL_UNPACK_FROM = struct.unpack_from
# The decode-admission and allocation limits are executable input policy.
# Detect accidental or hostile in-process changes before consulting private
# fixture bytes; the input still has no authenticated camera provenance.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_STRUCT = struct
_ORIGINAL_ZLIB = zlib
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_SIGNATURE = _SIGNATURE
_ORIGINAL_LIMITS = (
    _MAX_SOURCE, _MAX_PIXELS, _MAX_SIDE, _MAX_CHUNKS, _MAX_IDATS,
)
_ORIGINAL_VALID_DEPTHS_OBJECT = _VALID_DEPTHS
_ORIGINAL_VALID_DEPTHS = tuple(sorted(_VALID_DEPTHS.items()))
_INVENTORY_TYPE = OfflinePngInventory
_DENIAL_NAMES = (
    "decoded_pixels_verified", "capture_provenance_verified",
    "consent_verified", "context_release_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_INVENTORY_TYPE)[name] for name in _DENIAL_NAMES)
_REQUEST_TYPE = OfflinePngRequest
_REQUEST_FIELDS = ("owner_sha256", "privacy_sha256", "source_sha256", "png_bytes")
_RESULT_FIELDS = (
    "owner_sha256", "privacy_sha256", "source_sha256", "idat_sha256",
    "width", "height", "color_type", "bit_depth", "idat_chunks",
    "total_idat_bytes",
)
_LOOKUP_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REQUEST_INIT = vars(_REQUEST_TYPE)["__init__"]
_ORIGINAL_RESULT_INIT = vars(_INVENTORY_TYPE)["__init__"]
_ORIGINAL_REQUEST_FIELDS = tuple(vars(_REQUEST_TYPE)[name] for name in _REQUEST_FIELDS)
_ORIGINAL_RESULT_FIELDS = tuple(vars(_INVENTORY_TYPE)[name] for name in _RESULT_FIELDS)
_ORIGINAL_REQUEST_HOOKS = tuple(
    vars(_REQUEST_TYPE).get(name) for name in _LOOKUP_HOOKS
)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_INVENTORY_TYPE).get(name) for name in _LOOKUP_HOOKS
)


def _require_original_png_authority() -> None:
    if hashlib is not _ORIGINAL_HASHLIB or hashlib.sha256 is not _ORIGINAL_SHA256:
        raise OfflinePngRejected("PNG digest implementation changed before private bytes")
    if (
        zlib is not _ORIGINAL_ZLIB
        or struct is not _ORIGINAL_STRUCT
        or zlib.crc32 is not _ORIGINAL_CRC32
        or struct.unpack is not _ORIGINAL_UNPACK
        or struct.unpack_from is not _ORIGINAL_UNPACK_FROM
    ):
        raise OfflinePngRejected("PNG framing implementation changed before private bytes")
    if (
        _SHA is not _ORIGINAL_SHA_PATTERN
        # The helper itself receives private owner/privacy/source digests.
        # Refuse a substituted callable before any request field is read.
        or _sha is not _ORIGINAL_SHA_HELPER
        or _SIGNATURE is not _ORIGINAL_SIGNATURE
        or any(type(n) is not int for n in (
            _MAX_SOURCE, _MAX_PIXELS, _MAX_SIDE, _MAX_CHUNKS, _MAX_IDATS,
        ))
        or (
            _MAX_SOURCE, _MAX_PIXELS, _MAX_SIDE, _MAX_CHUNKS, _MAX_IDATS,
        ) != _ORIGINAL_LIMITS
        or type(_VALID_DEPTHS) is not dict
        or _VALID_DEPTHS is not _ORIGINAL_VALID_DEPTHS_OBJECT
        # The table is a mutable dict. Comparing its values can call an
        # injected __eq__/__ne__ on a private PNG ingress path. Require
        # exact canonical keys and original tuple objects before any bytes.
        or any(type(key) is not int for key in _VALID_DEPTHS)
        or len(_VALID_DEPTHS) != len(_ORIGINAL_VALID_DEPTHS)
        or any(
            _VALID_DEPTHS.get(key) is not saved
            for key, saved in _ORIGINAL_VALID_DEPTHS
        )
    ):
        raise OfflinePngRejected("PNG framing limits changed before private bytes")
    # Never run a replacement class constructor or a False-looking forged
    # descriptor. Both can have side effects and can forge an inert receipt.
    if (
        OfflinePngRequest is not _REQUEST_TYPE
        or vars(_REQUEST_TYPE).get("__init__") is not _ORIGINAL_REQUEST_INIT
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for names, originals in (
                (_REQUEST_FIELDS, _ORIGINAL_REQUEST_FIELDS),
                (_LOOKUP_HOOKS, _ORIGINAL_REQUEST_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise OfflinePngRejected("PNG request identity descriptor changed")
    if (
        OfflinePngInventory is not _INVENTORY_TYPE
        or vars(_INVENTORY_TYPE).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_INVENTORY_TYPE).get(name) is not original
            for names, originals in (
                (_RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_LOOKUP_HOOKS, _ORIGINAL_RESULT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise OfflinePngRejected(
            "constructed PNG inventory field, constructor or lookup changed"
        )
    if any(
        vars(_INVENTORY_TYPE).get(name) is not original
        for name, original in zip(_DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True)
    ):
        raise OfflinePngRejected(
            "constructed PNG inventory denial descriptor changed or claims authority"
        )


def _sha(value: object) -> bool:
    # Canonical SHA-256 is fixed-width ASCII. Avoid scanning unbounded labels.
    return type(value) is str and len(value) == 64 and _SHA.fullmatch(value) is not None


_ORIGINAL_SHA_HELPER = _sha


def inspect_disconnected_png(request: OfflinePngRequest) -> OfflinePngInventory:
    """Verify exact bounded PNG framing/CRC, not compressed-pixel validity.

    Admits IHDR, optional indexed PLTE, contiguous IDAT, and final IEND only.
    PNG ancillary chunks, unknown critical chunks, Adam7, and trailing bytes
    are rejected. CRC32 detects accidental chunk corruption, not authenticity.
    """
    _require_original_png_authority()
    if type(request) is not OfflinePngRequest:
        raise OfflinePngRejected("exact PNG request required")
    epoch = (
        request.owner_sha256, request.privacy_sha256,
        request.source_sha256, request.png_bytes,
    )

    def assert_epoch() -> None:
        # Hash and CRC callbacks may replace class descriptors. Inspect the
        # original declarations before AND after touching private fixture bytes.
        _require_original_png_authority()
        current = (
            request.owner_sha256, request.privacy_sha256,
            request.source_sha256, request.png_bytes,
        )
        _require_original_png_authority()
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
            _require_original_png_authority()
            result = OfflinePngInventory(
                owner, privacy, declared_digest, hashed_idat,
                width, height, color, depth, idat_count, idat_bytes,
            )
            assert_epoch()
            # Fail closed before a forged False getter runs; module import
            # captured the only non-authorizing descriptor definitions.
            def assert_result(
                *,
                result: OfflinePngInventory = result,
                hashed_idat: str = hashed_idat,
                width: int = width,
                height: int = height,
                color: int = color,
                depth: int = depth,
                idat_count: int = idat_count,
                idat_bytes: int = idat_bytes,
            ) -> None:
                _require_original_png_authority()
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
                            (
                                result.width, result.height, result.color_type,
                                result.bit_depth, result.idat_chunks,
                                result.total_idat_bytes,
                            ),
                            (width, height, color, depth, idat_count, idat_bytes),
                            strict=True,
                        )
                    )
                ):
                    raise OfflinePngRejected("constructed PNG inventory changed")

            assert_result()
            for name in _DENIAL_NAMES:
                _require_original_png_authority()
                if getattr(result, name) is not False:
                    raise OfflinePngRejected(
                        "constructed PNG inventory claims authority"
                    )
                # Callbacks are not an authoritative record of custody.
                # Recheck both the request and exact receipt fields after each.
                assert_result()
            return result
        else:
            raise OfflinePngRejected("unknown, private, or reordered PNG chunk")
    raise OfflinePngRejected("PNG missing final IEND")
