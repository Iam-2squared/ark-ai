"""Detached bounded PNG scanline decompression for synthetic, offline fixtures.

This parses no PNG chunks and trusts no upstream metadata. It checks a supplied
zlib IDAT stream and deterministic PNG row reconstruction only; neither a
camera frame, image meaning, issuer identity, consent nor any Tool is involved.
"""

from __future__ import annotations

import hashlib
import re
import zlib
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DEPTHS = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8),
           4: (8, 16), 6: (8, 16)}
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
_MAX_SOURCE = 8 * 1024 * 1024
_MAX_PIXELS = 4_194_304
_MAX_SIDE = 4096
_MAX_RAW = 40 * 1024 * 1024

# A mutable format table must not silently redefine the supported IDAT
# dialect during an offline privacy review. These are process-local source
# fingerprints, not container or camera provenance.
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_DEPTH_TABLE = _DEPTHS
_ORIGINAL_CHANNEL_TABLE = _CHANNELS
_ORIGINAL_DEPTH_ROWS = tuple(_DEPTHS.items())
_ORIGINAL_CHANNEL_ROWS = tuple(_CHANNELS.items())
_ORIGINAL_BUDGETS = (_MAX_SOURCE, _MAX_PIXELS, _MAX_SIDE, _MAX_RAW)


class OfflineScanlineRejected(ValueError):
    """The fixture stream, declared format, or row reconstruction is invalid."""


@dataclass(frozen=True, slots=True)
class OfflineScanlineRequest:
    owner_sha256: str = field(repr=False)
    privacy_sha256: str = field(repr=False)
    idat_sha256: str
    idat_bytes: bytes = field(repr=False)
    width: int = 0
    height: int = 0
    color_type: int = 0
    bit_depth: int = 0
    palette_entries: int = 0


@dataclass(frozen=True, slots=True)
class OfflineScanlineAudit:
    idat_sha256: str
    reconstructed_sha256: str
    width: int
    height: int
    inflated_bytes: int
    filters_used: tuple[int, ...]

    @property
    def png_container_verified(self) -> bool:
        return False

    @property
    def capture_provenance_verified(self) -> bool:
        return False

    @property
    def user_consent_verified(self) -> bool:
        return False

    @property
    def raw_pixels_released(self) -> bool:
        return False

    @property
    def observation_or_tool_authorized(self) -> bool:
        return False



# Synthetic IDAT bytes must never reach a replaced digest/decompressor or a
# class-level request getter. Pin the import-original local boundary before
# the first private field read; this is NOT remote codec attestation.
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DECOMPRESSOBJ = zlib.decompressobj
_REQUEST_TYPE = OfflineScanlineRequest
_REQUEST_FIELDS = (
    "owner_sha256", "privacy_sha256", "idat_sha256", "idat_bytes",
    "width", "height", "color_type", "bit_depth", "palette_entries",
)
_REQUEST_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REQUEST_SLOTS = tuple(
    vars(_REQUEST_TYPE).get(name) for name in (*_REQUEST_FIELDS, *_REQUEST_HOOKS)
)


def _require_original_scanline_inputs() -> None:
    if (
        hashlib.sha256 is not _ORIGINAL_SHA256
        or zlib.decompressobj is not _ORIGINAL_DECOMPRESSOBJ
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or type(_DEPTHS) is not dict
        or _DEPTHS is not _ORIGINAL_DEPTH_TABLE
        or type(_CHANNELS) is not dict
        or _CHANNELS is not _ORIGINAL_CHANNEL_TABLE
        or len(_DEPTHS) != len(_ORIGINAL_DEPTH_ROWS)
        or len(_CHANNELS) != len(_ORIGINAL_CHANNEL_ROWS)
        # Reject hostile objects before tuple equality or dict membership.
        or any(
            type(key) is not int or type(value) is not tuple
            or any(type(depth) is not int for depth in value)
            for key, value in _DEPTHS.items()
        )
        or any(
            type(key) is not int or type(value) is not int
            for key, value in _CHANNELS.items()
        )
        or tuple(_DEPTHS.items()) != _ORIGINAL_DEPTH_ROWS
        or tuple(_CHANNELS.items()) != _ORIGINAL_CHANNEL_ROWS
        or any(
            type(value) is not int
            for value in (_MAX_SOURCE, _MAX_PIXELS, _MAX_SIDE, _MAX_RAW)
        )
        or (_MAX_SOURCE, _MAX_PIXELS, _MAX_SIDE, _MAX_RAW) != _ORIGINAL_BUDGETS
        or OfflineScanlineRequest is not _REQUEST_TYPE
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(
                (*_REQUEST_FIELDS, *_REQUEST_HOOKS),
                _ORIGINAL_REQUEST_SLOTS, strict=True,
            )
        )
    ):
        raise OfflineScanlineRejected("scanline request or codec implementation changed")


def _sha(value: object) -> bool:
    return type(value) is str and len(value) == 64 and _SHA.fullmatch(value) is not None


def _paeth(left: int, above: int, upper_left: int) -> int:
    prediction = left + above - upper_left
    a = abs(prediction - left)
    b = abs(prediction - above)
    c = abs(prediction - upper_left)
    if a <= b and a <= c:
        return left
    return above if b <= c else upper_left


def inspect_offline_png_scanlines(request: OfflineScanlineRequest) -> OfflineScanlineAudit:
    """Bound inflation, validate all rows/filters and hash unfiltered bytes.

    A raw deflate stream, truncated zlib trailer, extra compressed bytes,
    wrong row shape or invalid indexed palette value is denied. This returns
    digests and counts, NOT reconstructed pixels or disclosure authorization.
    """
    _require_original_scanline_inputs()
    if type(request) is not OfflineScanlineRequest:
        raise OfflineScanlineRejected("exact scanline request required")
    attrs = (
        request.owner_sha256, request.privacy_sha256, request.idat_sha256,
        request.idat_bytes, request.width, request.height,
        request.color_type, request.bit_depth, request.palette_entries,
    )

    def assert_epoch() -> None:
        _require_original_scanline_inputs()
        current = (
            request.owner_sha256, request.privacy_sha256, request.idat_sha256,
            request.idat_bytes, request.width, request.height,
            request.color_type, request.bit_depth, request.palette_entries,
        )
        _require_original_scanline_inputs()
        if any(a is not b for a, b in zip(current, attrs, strict=True)):
            raise OfflineScanlineRejected("scanline request carrier changed during review")

    assert_epoch()
    owner, privacy, declared, data, width, height, color, depth, entries = attrs
    if not all(_sha(x) for x in (owner, privacy, declared)):
        raise OfflineScanlineRejected("invalid fixture identity digest")
    if type(data) is not bytes or not 1 <= len(data) <= _MAX_SOURCE:
        raise OfflineScanlineRejected("IDAT byte budget/type invalid")
    if any(type(v) is not int for v in (width, height, color, depth, entries)):
        raise OfflineScanlineRejected("exact integer PNG metadata required")
    if (
        not 1 <= width <= _MAX_SIDE or not 1 <= height <= _MAX_SIDE
        or width * height > _MAX_PIXELS
        or color not in _DEPTHS or depth not in _DEPTHS[color]
        or (color == 3 and not 1 <= entries <= 1 << depth)
        or (color != 3 and entries != 0)
    ):
        raise OfflineScanlineRejected("unsupported format, palette or pixel budget")
    if hashlib.sha256(data).hexdigest() != declared:
        raise OfflineScanlineRejected("IDAT digest mismatch")
    assert_epoch()
    channels = _CHANNELS[color]
    bytes_per_pixel = max(1, (channels * depth + 7) // 8)
    row_bytes = (width * channels * depth + 7) // 8
    expected = (row_bytes + 1) * height
    if expected > _MAX_RAW:
        raise OfflineScanlineRejected("inflated PNG exceeds byte budget")

    try:
        decoder = zlib.decompressobj(wbits=zlib.MAX_WBITS)
        inflated = decoder.decompress(data, expected + 1)
        # An extra output byte, extra input, missing end marker or bad Adler32
        # must not turn a compressed bomb/truncated image into a valid fixture.
        if (
            len(inflated) != expected or not decoder.eof
            or decoder.unused_data or decoder.unconsumed_tail or decoder.flush()
        ):
            raise OfflineScanlineRejected("IDAT deflate length/trailer invalid")
    except (zlib.error, MemoryError) as exc:
        raise OfflineScanlineRejected("IDAT zlib decompression rejected") from exc
    assert_epoch()

    previous = bytes(row_bytes)
    filtered_counts = [0, 0, 0, 0, 0]
    digest = hashlib.sha256()
    position = 0
    for _ in range(height):
        kind = inflated[position]
        if kind > 4:
            raise OfflineScanlineRejected("unsupported PNG row filter")
        filtered_counts[kind] += 1
        row = inflated[position + 1:position + 1 + row_bytes]
        position += row_bytes + 1
        reconstructed = bytearray(row)
        if kind:
            for i, encoded in enumerate(row):
                left = reconstructed[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                above = previous[i]
                upper_left = previous[i - bytes_per_pixel] if i >= bytes_per_pixel else 0
                if kind == 1:
                    predictor = left
                elif kind == 2:
                    predictor = above
                elif kind == 3:
                    predictor = (left + above) // 2
                else:
                    predictor = _paeth(left, above, upper_left)
                reconstructed[i] = (encoded + predictor) & 255
        if color == 3:
            mask = (1 << depth) - 1
            for x in range(width):
                offset = x * depth
                index = (reconstructed[offset // 8] >> (8 - depth - offset % 8)) & mask
                if index >= entries:
                    raise OfflineScanlineRejected("indexed pixel references absent palette")
        digest.update(reconstructed)
        previous = reconstructed
    assert_epoch()
    return OfflineScanlineAudit(
        idat_sha256=declared,
        reconstructed_sha256=digest.hexdigest(),
        width=width,
        height=height,
        inflated_bytes=expected,
        filters_used=tuple(filtered_counts),
    )



_SCANLINE_DENIALS = (
    "png_container_verified", "capture_provenance_verified",
    "user_consent_verified", "raw_pixels_released",
    "observation_or_tool_authorized",
)
# Original denial-only descriptors are independent of a caller's later
# false-valued replacement. Neither a false getter nor a local digest grants
# consent, capture provenance, or permission to disclose pixels.
_SCANLINE_DENIAL_DESCRIPTORS = tuple(
    getattr(OfflineScanlineAudit, name) for name in _SCANLINE_DENIALS
)


def verify_offline_png_scanlines(
    audit: OfflineScanlineAudit, request: OfflineScanlineRequest,
) -> None:
    """Recheck a detached private report against retained synthetic IDAT.

    Both request bytes and the returned report remain pinned across *all*
    potentially reentrant denial getters. This is still local consistency,
    not camera provenance, authentic consent, or filesystem race immunity.
    """
    _require_original_scanline_inputs()
    if type(audit) is not OfflineScanlineAudit:
        raise OfflineScanlineRejected("exact detached scanline audit required")
    if type(request) is not OfflineScanlineRequest:
        raise OfflineScanlineRejected("exact detached scanline request required")
    fields = (
        audit.idat_sha256, audit.reconstructed_sha256, audit.width,
        audit.height, audit.inflated_bytes, audit.filters_used,
    )
    request_fields = (
        request.owner_sha256, request.privacy_sha256, request.idat_sha256,
        request.idat_bytes, request.width, request.height,
        request.color_type, request.bit_depth, request.palette_entries,
    )
    if (
        not _sha(fields[0]) or not _sha(fields[1])
        or any(type(v) is not int for v in fields[2:5])
        or type(fields[5]) is not tuple
        or len(fields[5]) != 5
        or any(type(v) is not int or v < 0 for v in fields[5])
    ):
        raise OfflineScanlineRejected("detached scanline audit shape invalid")

    def stable_report() -> None:
        if (
            type(audit) is not OfflineScanlineAudit
            or any(
                now is not old for now, old in zip(
                    (audit.idat_sha256, audit.reconstructed_sha256, audit.width,
                     audit.height, audit.inflated_bytes, audit.filters_used),
                    fields, strict=True,
                )
            )
        ):
            raise OfflineScanlineRejected(
                "detached scanline audit changed during verification"
            )

    def stable_request() -> None:
        if (
            type(request) is not OfflineScanlineRequest
            or any(
                now is not old for now, old in zip(
                    (request.owner_sha256, request.privacy_sha256,
                     request.idat_sha256, request.idat_bytes,
                     request.width, request.height, request.color_type,
                     request.bit_depth, request.palette_entries),
                    request_fields, strict=True,
                )
            )
        ):
            raise OfflineScanlineRejected(
                "detached scanline source changed during verification"
            )

    def stable_denials() -> None:
        if any(
            getattr(OfflineScanlineAudit, name) is not original
            for name, original in zip(
                _SCANLINE_DENIALS, _SCANLINE_DENIAL_DESCRIPTORS, strict=True,
            )
        ):
            raise OfflineScanlineRejected(
                "detached scanline denial descriptor changed"
            )

    stable_report()
    stable_request()
    stable_denials()
    expected = inspect_offline_png_scanlines(request)
    stable_request()
    stable_report()
    stable_denials()
    truth = (
        expected.idat_sha256, expected.reconstructed_sha256, expected.width,
        expected.height, expected.inflated_bytes, expected.filters_used,
    )
    if fields != truth:
        raise OfflineScanlineRejected("detached scanline audit differs from source bytes")
    for name in _SCANLINE_DENIALS:
        stable_denials()
        if getattr(audit, name) is not False:
            raise OfflineScanlineRejected("detached scanline report claimed authority")
        stable_report()
        stable_request()
        stable_denials()
    stable_report()
    stable_request()
    stable_denials()
