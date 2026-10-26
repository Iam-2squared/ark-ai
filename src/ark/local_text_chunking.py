"""Deterministic, bounded local text chunking for *untrusted* synthetic Memory.

All content stays in the returned in-memory object. No disk, network, model,
Memory store or ToolBackend is touched. Hashes establish local consistency,
not ownership, consent, provenance, or permission to export text.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_HEX = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-local-text-chunk-v1\0"
_MAX_SOURCE_BYTES = 65_536
_MAX_CHUNKS = 64
_MAX_CHUNK_BYTES = 4_096


class LocalChunkRejected(ValueError):
    """Text is ambiguous, altered, or exceeds the local chunking budget."""


@dataclass(frozen=True, slots=True)
class LocalChunkRequest:
    text: str
    source_sha256: str
    owner_sha256: str
    scope_sha256: str
    chunk_byte_limit: int = 1_024
    chunk_limit: int = 64


@dataclass(frozen=True, slots=True)
class LocalTextChunk:
    index: int
    start: int
    end: int
    text: str
    sha256: str


@dataclass(frozen=True, slots=True)
class LocalTextChunkBundle:
    owner_sha256: str
    scope_sha256: str
    source_sha256: str
    chunk_byte_limit: int
    chunks: tuple[LocalTextChunk, ...]
    bundle_sha256: str

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def retention_authorized(self) -> bool:
        return False


def _hex(value: object) -> bool:
    return type(value) is str and _HEX.fullmatch(value) is not None


def _digest(label: str, value: object) -> str:
    data = json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + label.encode("ascii") + b"\0" + data).hexdigest()


def _text_bytes(value: object) -> bytes:
    if type(value) is not str or not value:
        raise LocalChunkRejected("source text must be nonempty exact text")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise LocalChunkRejected("source text has invalid Unicode") from exc
    if len(encoded) > _MAX_SOURCE_BYTES:
        raise LocalChunkRejected("source exceeds in-memory byte budget")
    return encoded


def _manifest(bundle: LocalTextChunkBundle) -> dict[str, object]:
    return {
        "owner": bundle.owner_sha256,
        "scope": bundle.scope_sha256,
        "source": bundle.source_sha256,
        "chunk_byte_limit": bundle.chunk_byte_limit,
        "chunks": [
            (row.index, row.start, row.end, row.sha256) for row in bundle.chunks
        ],
    }


def verify_local_chunks(bundle: LocalTextChunkBundle) -> str:
    """Validate a complete local bundle and return its reconstructed text.

    This check detects accidental alteration but NOT coordinated rewriting of
    the bundle, declared hashes and caller-supplied owner/scope identities.
    """
    if type(bundle) is not LocalTextChunkBundle:
        raise LocalChunkRejected("exact local bundle type required")
    if (
        not all(_hex(x) for x in (
            bundle.owner_sha256, bundle.scope_sha256, bundle.source_sha256,
            bundle.bundle_sha256,
        ))
        or type(bundle.chunk_byte_limit) is not int
        or not 1 <= bundle.chunk_byte_limit <= _MAX_CHUNK_BYTES
        or type(bundle.chunks) is not tuple
        or not 1 <= len(bundle.chunks) <= _MAX_CHUNKS
    ):
        raise LocalChunkRejected("bundle header invalid")
    fragments: list[str] = []
    end = 0
    for index, row in enumerate(bundle.chunks):
        if (
            type(row) is not LocalTextChunk
            or type(row.index) is not int or row.index != index
            or type(row.start) is not int or row.start != end
            or type(row.end) is not int or row.end <= row.start
            or not _hex(row.sha256)
        ):
            raise LocalChunkRejected("chunk order, span or identity changed")
        payload = _text_bytes(row.text)
        if len(payload) > bundle.chunk_byte_limit or len(row.text) != row.end - row.start:
            raise LocalChunkRejected("chunk contents exceed declared span or byte limit")
        if row.sha256 != _digest("piece", (row.index, row.start, row.end, row.text)):
            raise LocalChunkRejected("local chunk digest mismatch")
        fragments.append(row.text)
        end = row.end
    source = "".join(fragments)
    if hashlib.sha256(_text_bytes(source)).hexdigest() != bundle.source_sha256:
        raise LocalChunkRejected("source digest or membership mismatch")
    if _digest("bundle", _manifest(bundle)) != bundle.bundle_sha256:
        raise LocalChunkRejected("bundle membership digest mismatch")
    return source


def chunk_local_text(request: LocalChunkRequest) -> LocalTextChunkBundle:
    """Split entire UTF-8 text on codepoint boundaries without truncation."""
    if type(request) is not LocalChunkRequest:
        raise LocalChunkRejected("exact source request required")
    original = (
        request.text, request.source_sha256, request.owner_sha256,
        request.scope_sha256, request.chunk_byte_limit, request.chunk_limit,
    )

    def check_epoch() -> None:
        current = (
            request.text, request.source_sha256, request.owner_sha256,
            request.scope_sha256, request.chunk_byte_limit, request.chunk_limit,
        )
        if any(a is not b for a, b in zip(current, original, strict=True)):
            raise LocalChunkRejected("source request changed during chunking")

    check_epoch()
    text, source, owner, scope, byte_limit, chunk_limit = original
    if (
        not all(_hex(x) for x in (source, owner, scope))
        or type(byte_limit) is not int or not 1 <= byte_limit <= _MAX_CHUNK_BYTES
        or type(chunk_limit) is not int or not 1 <= chunk_limit <= _MAX_CHUNKS
    ):
        raise LocalChunkRejected("invalid chunk budget or untrusted identity shape")
    source_bytes = _text_bytes(text)
    check_epoch()
    if hashlib.sha256(source_bytes).hexdigest() != source:
        raise LocalChunkRejected("declared source digest mismatches original content")
    check_epoch()
    chunks: list[LocalTextChunk] = []
    start = 0
    while start < len(text):
        if len(chunks) >= chunk_limit:
            raise LocalChunkRejected("chunk budget would silently truncate source")
        size = 0
        end = start
        while end < len(text):
            width = len(text[end].encode("utf-8"))
            if size + width > byte_limit:
                break
            size += width
            end += 1
        if end == start:
            raise LocalChunkRejected("single Unicode codepoint exceeds chunk budget")
        piece = text[start:end]
        digest = _digest("piece", (len(chunks), start, end, piece))
        check_epoch()
        chunks.append(LocalTextChunk(len(chunks), start, end, piece, digest))
        start = end
    bundle = LocalTextChunkBundle(owner, scope, source, byte_limit, tuple(chunks), "")
    digest = _digest("bundle", _manifest(bundle))
    check_epoch()
    result = LocalTextChunkBundle(owner, scope, source, byte_limit, tuple(chunks), digest)
    if verify_local_chunks(result) != text:
        raise LocalChunkRejected("final reconstructed text changed")
    check_epoch()
    return result
