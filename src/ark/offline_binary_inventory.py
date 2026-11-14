"""Bounded, metadata-only integrity inventory for explicit local binary fixtures.

Receipts contain no source bytes. SHA-256 checks detect changed supplied bytes,
not authentic origin, consent, owner, or completeness without independent
retention of the inventory digest and entire expected source digest.
No filesystem, external compute, network, devices or side effects.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-binary-inventory-v1\0"
_MAX_BYTES = 2 * 1024 * 1024
_MAX_CHUNKS = 64
_MAX_CHUNK_BYTES = 65_536


class OfflineBinaryRejected(ValueError):
    """Binary input or retained receipt lacks exact bounded integrity."""


@dataclass(frozen=True, slots=True)
class OfflineBinaryRequest:
    owner_sha256: str
    privacy_sha256: str
    source_sha256: str
    source_bytes: bytes = field(repr=False)
    chunk_bytes: int = 65_536


@dataclass(frozen=True, slots=True)
class OfflineBinaryChunk:
    index: int
    start_byte: int
    end_byte: int
    content_sha256: str


@dataclass(frozen=True, slots=True)
class OfflineBinaryInventory:
    owner_sha256: str
    privacy_sha256: str
    source_sha256: str
    source_size: int
    chunk_bytes: int
    chunks: tuple[OfflineBinaryChunk, ...]
    inventory_sha256: str

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _source(data: object, size: int | None = None) -> bytes:
    if type(data) is not bytes or not 0 < len(data) <= _MAX_BYTES:
        raise OfflineBinaryRejected("unbounded or non-exact binary bytes")
    if size is not None and len(data) != size:
        raise OfflineBinaryRejected("binary size disagrees with receipt")
    return data


def _chunk_digest(payload: bytes) -> str:
    return hashlib.sha256(_DOMAIN + b"chunk\0" + payload).hexdigest()


def _manifest_digest(receipt: OfflineBinaryInventory) -> str:
    manifest = {
        "owner": receipt.owner_sha256, "privacy": receipt.privacy_sha256,
        "source": receipt.source_sha256, "size": receipt.source_size,
        "chunk_bytes": receipt.chunk_bytes,
        "chunks": [(c.index, c.start_byte, c.end_byte, c.content_sha256)
                   for c in receipt.chunks],
    }
    encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=True,
                         separators=(",", ":")).encode("ascii")
    return hashlib.sha256(_DOMAIN + b"manifest\0" + encoded).hexdigest()


def inventory_offline_binary(request: OfflineBinaryRequest) -> OfflineBinaryInventory:
    """Cover every byte exactly once and return only a digest inventory."""
    if type(request) is not OfflineBinaryRequest:
        raise OfflineBinaryRejected("exact binary request required")
    pinned = (request.owner_sha256, request.privacy_sha256,
              request.source_sha256, request.source_bytes, request.chunk_bytes)

    def epoch() -> None:
        current = (request.owner_sha256, request.privacy_sha256,
                   request.source_sha256, request.source_bytes, request.chunk_bytes)
        if any(a is not b for a, b in zip(current, pinned, strict=True)):
            raise OfflineBinaryRejected("binary request mutated during inspection")

    epoch()
    owner, privacy, declared, data, chunk_bytes = pinned
    if (
        not all(_sha(value) for value in (owner, privacy, declared))
        or type(chunk_bytes) is not int or not 1 <= chunk_bytes <= _MAX_CHUNK_BYTES
    ):
        raise OfflineBinaryRejected("invalid identity or chunk budget")
    source = _source(data)
    if (len(source) + chunk_bytes - 1) // chunk_bytes > _MAX_CHUNKS:
        raise OfflineBinaryRejected("chunk count would exceed budget")
    if hashlib.sha256(source).hexdigest() != declared:
        raise OfflineBinaryRejected("declared binary digest mismatch")
    epoch()
    chunks = tuple(
        OfflineBinaryChunk(i, start, min(len(source), start + chunk_bytes),
                           _chunk_digest(source[start:start + chunk_bytes]))
        for i, start in enumerate(range(0, len(source), chunk_bytes))
    )
    proto = OfflineBinaryInventory(owner, privacy, declared, len(source),
                                   chunk_bytes, chunks, "")
    digest = _manifest_digest(proto)
    epoch()
    result = OfflineBinaryInventory(owner, privacy, declared, len(source),
                                    chunk_bytes, chunks, digest)
    verify_offline_binary_inventory(
        result, source, retained_inventory_sha256=digest,
        retained_source_sha256=declared,
    )
    epoch()
    return result


def verify_offline_binary_inventory(
    receipt: OfflineBinaryInventory, source_bytes: bytes, *,
    retained_inventory_sha256: str, retained_source_sha256: str,
) -> None:
    """Compare all bytes against the claimed AND independently retained hashes.

    The retained hashes must come from an independent trustworthy channel to
    provide provenance; caller-controlled retained values offer no authority.
    """
    if type(receipt) is not OfflineBinaryInventory:
        raise OfflineBinaryRejected("exact inventory type required")
    if (
        not all(_sha(x) for x in (
            receipt.owner_sha256, receipt.privacy_sha256,
            receipt.source_sha256, receipt.inventory_sha256,
            retained_source_sha256, retained_inventory_sha256,
        ))
        or type(receipt.source_size) is not int
        or not 0 < receipt.source_size <= _MAX_BYTES
        or type(receipt.chunk_bytes) is not int
        or not 1 <= receipt.chunk_bytes <= _MAX_CHUNK_BYTES
        or type(receipt.chunks) is not tuple
        or not 1 <= len(receipt.chunks) <= _MAX_CHUNKS
    ):
        raise OfflineBinaryRejected("invalid inventory header")
    data = _source(source_bytes, receipt.source_size)
    pinned = (receipt.owner_sha256, receipt.privacy_sha256, receipt.source_sha256,
              receipt.source_size, receipt.chunk_bytes, receipt.chunks,
              receipt.inventory_sha256)
    originals = tuple(receipt.chunks)
    fields = tuple((c.index, c.start_byte, c.end_byte, c.content_sha256)
                   if type(c) is OfflineBinaryChunk else None for c in originals)

    def epoch() -> None:
        now = (receipt.owner_sha256, receipt.privacy_sha256, receipt.source_sha256,
               receipt.source_size, receipt.chunk_bytes, receipt.chunks,
               receipt.inventory_sha256)
        if (
            any(a is not b for a, b in zip(now, pinned, strict=True))
            or len(receipt.chunks) != len(originals)
            or any(c is not old for c, old in zip(receipt.chunks, originals, strict=True))
            or any(type(c) is not OfflineBinaryChunk
                   or any(a is not b for a, b in zip(
                       (c.index, c.start_byte, c.end_byte, c.content_sha256),
                       saved, strict=True))
                   for c, saved in zip(originals, fields, strict=True))
        ):
            raise OfflineBinaryRejected("inventory mutated during verification")

    epoch()
    if (
        len(originals) != (len(data) + receipt.chunk_bytes - 1) // receipt.chunk_bytes
        or receipt.source_sha256 != retained_source_sha256
        or hashlib.sha256(data).hexdigest() != retained_source_sha256
    ):
        raise OfflineBinaryRejected("source membership or digest mismatch")
    cursor = 0
    for i, row in enumerate(originals):
        epoch()
        if (
            type(row) is not OfflineBinaryChunk
            or type(row.index) is not int or row.index != i
            or type(row.start_byte) is not int or row.start_byte != cursor
            or type(row.end_byte) is not int
            or row.end_byte != min(len(data), cursor + receipt.chunk_bytes)
            or not _sha(row.content_sha256)
        ):
            raise OfflineBinaryRejected("chunk gap, overlap or forged boundary")
        if _chunk_digest(data[cursor:row.end_byte]) != row.content_sha256:
            raise OfflineBinaryRejected("chunk digest mismatch")
        cursor = row.end_byte
    if cursor != len(data) or receipt.inventory_sha256 != retained_inventory_sha256:
        raise OfflineBinaryRejected("incomplete receipt or mismatched retained inventory")
    epoch()
    if _manifest_digest(receipt) != retained_inventory_sha256:
        raise OfflineBinaryRejected("inventory manifest integrity mismatch")
    epoch()
