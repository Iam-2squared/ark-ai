"""No-disclosure chunk-to-lexical-index bridge for synthetic local Memory.

A caller must retain the bundle digest independently. A successful lexical
match does not authenticate consent, revocation, ownership or source content.
No snippets, file writes, model inference, network or live Memory operations.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import local_text_chunking as chunk_mod
from . import offline_text_index as index_mod

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-chunk-index-bridge-v1\0"
_CHUNK_BUNDLE = chunk_mod.LocalTextChunkBundle
_CHUNK = chunk_mod.LocalTextChunk
_VERIFY = chunk_mod.verify_local_chunks
_QUERY = index_mod.OfflineIndexQuery
_DOCUMENT = index_mod.OfflineIndexDocument
_INDEX_RESULT = index_mod.OfflineIndexResult
_HIT = index_mod.OfflineIndexHit
_SEARCH = index_mod.search_offline_text
_BUNDLE_DENIAL_NAMES = (
    "disclosure_authorized", "source_authenticated", "retention_authorized",
)
_INDEX_DENIAL_NAMES = (
    "identity_authenticated", "disclosure_authorized", "revocation_verified",
)
_BUNDLE_DENIALS = tuple(vars(_CHUNK_BUNDLE)[k] for k in _BUNDLE_DENIAL_NAMES)
_INDEX_DENIALS = tuple(vars(_INDEX_RESULT)[k] for k in _INDEX_DENIAL_NAMES)


class OfflineChunkIndexRejected(ValueError):
    """A detached source, query, or index membership is untrusted or changed."""


@dataclass(frozen=True, slots=True)
class OfflineChunkIndexHit:
    chunk_index: int
    start: int
    end: int
    document_id: str
    score: int
    chunk_sha256: str


@dataclass(frozen=True, slots=True)
class OfflineChunkIndexReview:
    hits: tuple[OfflineChunkIndexHit, ...]
    scanned_count: int
    source_sha256: str
    index_inventory_sha256: str
    evidence_sha256: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def source_authenticated(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def retention_authorized(self) -> bool:
        return False


_RESULT = OfflineChunkIndexReview
_RESULT_DENIAL_NAMES = (
    "consent_verified", "source_authenticated",
    "disclosure_authorized", "retention_authorized",
)
_RESULT_DENIALS = tuple(vars(_RESULT)[k] for k in _RESULT_DENIAL_NAMES)


def search_detached_local_chunks(
    bundle: chunk_mod.LocalTextChunkBundle,
    query: str,
    *,
    query_sha256: str,
    retained_bundle_sha256: str,
    limit: int = 8,
) -> OfflineChunkIndexReview:
    """Bridge a fully reconstructed bounded text bundle into hash-only hits."""
    def original() -> None:
        if (
            chunk_mod.LocalTextChunkBundle is not _CHUNK_BUNDLE
            or chunk_mod.LocalTextChunk is not _CHUNK
            or chunk_mod.verify_local_chunks is not _VERIFY
            or index_mod.OfflineIndexQuery is not _QUERY
            or index_mod.OfflineIndexDocument is not _DOCUMENT
            or index_mod.OfflineIndexResult is not _INDEX_RESULT
            or index_mod.OfflineIndexHit is not _HIT
            or index_mod.search_offline_text is not _SEARCH
            or OfflineChunkIndexReview is not _RESULT
            or OfflineChunkIndexHit is not _RESULT_HIT
            or any(vars(_CHUNK_BUNDLE).get(k) is not v for k, v in zip(
                _BUNDLE_DENIAL_NAMES, _BUNDLE_DENIALS, strict=True,
            ))
            or any(vars(_INDEX_RESULT).get(k) is not v for k, v in zip(
                _INDEX_DENIAL_NAMES, _INDEX_DENIALS, strict=True,
            ))
            or any(vars(_RESULT).get(k) is not v for k, v in zip(
                _RESULT_DENIAL_NAMES, _RESULT_DENIALS, strict=True,
            ))
        ):
            raise OfflineChunkIndexRejected("chunk index authority changed")

    original()
    if (
        type(bundle) is not _CHUNK_BUNDLE
        or type(query) is not str or not query or len(query) > 512
        or type(query_sha256) is not str
        or _SHA.fullmatch(query_sha256) is None
        or type(retained_bundle_sha256) is not str
        or _SHA.fullmatch(retained_bundle_sha256) is None
        or type(limit) is not int or not 1 <= limit <= 8
        or type(bundle.chunks) is not tuple
        or not 1 <= len(bundle.chunks) <= 32
        or any(type(row) is not _CHUNK for row in bundle.chunks)
    ):
        raise OfflineChunkIndexRejected("exact bounded source and query required")

    header = (
        bundle.owner_sha256, bundle.scope_sha256, bundle.source_sha256,
        bundle.chunk_byte_limit, bundle.chunks, bundle.bundle_sha256,
    )
    originals = tuple(bundle.chunks)
    fields = tuple((
        c.index, c.start, c.end, c.text, c.sha256,
    ) for c in originals)

    def stable() -> None:
        original()
        if (
            type(bundle) is not _CHUNK_BUNDLE
            or any(a is not b for a, b in zip(
                (bundle.owner_sha256, bundle.scope_sha256, bundle.source_sha256,
                 bundle.chunk_byte_limit, bundle.chunks, bundle.bundle_sha256),
                header, strict=True,
            ))
            or type(bundle.chunks) is not tuple
            or len(bundle.chunks) != len(originals)
            or any(
                type(row) is not _CHUNK or row is not old
                or any(a is not b for a, b in zip(
                    (row.index, row.start, row.end, row.text, row.sha256),
                    f, strict=True,
                ))
                for row, old, f in zip(bundle.chunks, originals, fields, strict=True)
            )
        ):
            raise OfflineChunkIndexRejected("chunk source evidence changed")

    stable()
    if bundle.bundle_sha256 != retained_bundle_sha256:
        raise OfflineChunkIndexRejected("retained chunk digest mismatch")
    try:
        query_bytes = query.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise OfflineChunkIndexRejected("query has invalid Unicode") from exc
    if len(query_bytes) > 512:
        raise OfflineChunkIndexRejected("query byte budget exceeded")
    actual_query_sha = hashlib.sha256(query_bytes).hexdigest()
    stable()
    if actual_query_sha != query_sha256:
        raise OfflineChunkIndexRejected("query source digest mismatch")
    try:
        source = _VERIFY(bundle)
    except chunk_mod.LocalChunkRejected as exc:
        raise OfflineChunkIndexRejected("source chunk bundle rejected") from exc
    stable()
    if type(source) is not str:
        raise OfflineChunkIndexRejected("reconstructed source type changed")
    for name in _BUNDLE_DENIAL_NAMES:
        if getattr(bundle, name) is not False:
            raise OfflineChunkIndexRejected("chunk bundle gained authority")
        stable()

    docs = []
    mapping = {}
    for item in originals:
        stable()
        raw_sha = hashlib.sha256(item.text.encode("utf-8")).hexdigest()
        label = json.dumps(
            (bundle.source_sha256, item.index, item.sha256),
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        doc_id = "doc_" + hashlib.sha256(
            _DOMAIN + b"document\0" + label,
        ).hexdigest()[:16]
        if doc_id in mapping:
            raise OfflineChunkIndexRejected("derived document identity collision")
        mapping[doc_id] = item
        docs.append(_DOCUMENT(
            doc_id, bundle.owner_sha256, bundle.scope_sha256,
            raw_sha, item.text,
        ))
    stable()
    request = _QUERY(
        bundle.owner_sha256, bundle.scope_sha256,
        query_sha256, query, tuple(docs), tuple(sorted(mapping)), limit,
    )
    try:
        indexed = _SEARCH(request)
    except index_mod.OfflineIndexRejected as exc:
        raise OfflineChunkIndexRejected("source lexical index rejected") from exc
    stable()
    if type(indexed) is not _INDEX_RESULT:
        raise OfflineChunkIndexRejected("index result carrier changed")
    epoch = (
        indexed.hits, indexed.scanned_count, indexed.query_token_count,
        indexed.inventory_sha256, indexed.result_sha256,
    )
    if type(indexed.hits) is not tuple or len(indexed.hits) > limit:
        raise OfflineChunkIndexRejected("index returned unbounded hits")
    hit_epoch = tuple((
        row, row.document_id, row.distinct_matches, row.score,
        row.document_sha256,
    ) for row in indexed.hits)

    def stable_index() -> None:
        stable()
        if (
            type(indexed) is not _INDEX_RESULT
            or any(a is not b for a, b in zip(
                (indexed.hits, indexed.scanned_count,
                 indexed.query_token_count, indexed.inventory_sha256,
                 indexed.result_sha256), epoch, strict=True,
            ))
            or len(indexed.hits) != len(hit_epoch)
            or any(
                type(row) is not _HIT or row is not before
                or any(a is not b for a, b in zip(
                    (row.document_id, row.distinct_matches, row.score,
                     row.document_sha256), fields, strict=True,
                ))
                for row, (before, *fields) in zip(
                    indexed.hits, hit_epoch, strict=True,
                )
            )
        ):
            raise OfflineChunkIndexRejected("index report changed")

    stable_index()
    for name in _INDEX_DENIAL_NAMES:
        if getattr(indexed, name) is not False:
            raise OfflineChunkIndexRejected("index gained authority")
        stable_index()

    hits = []
    for hit in indexed.hits:
        stable_index()
        if type(hit) is not _HIT or hit.document_id not in mapping:
            raise OfflineChunkIndexRejected("unknown index hit")
        chunk = mapping[hit.document_id]
        hits.append(_RESULT_HIT(
            chunk.index, chunk.start, chunk.end, hit.document_id,
            hit.score, chunk.sha256,
        ))
    encoded = json.dumps(
        (bundle.bundle_sha256, query_sha256, epoch[3], epoch[4],
         [(h.chunk_index, h.start, h.end, h.document_id, h.score,
           h.chunk_sha256) for h in hits]),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    stable_index()
    digest = hashlib.sha256(_DOMAIN + b"receipt\0" + encoded).hexdigest()
    stable_index()
    result = _RESULT(tuple(hits), len(originals), bundle.source_sha256,
                     epoch[3], digest)
    final = (result.hits, result.scanned_count, result.source_sha256,
             result.index_inventory_sha256, result.evidence_sha256)
    final_hits = tuple((
        hit, hit.chunk_index, hit.start, hit.end, hit.document_id,
        hit.score, hit.chunk_sha256,
    ) for hit in hits)
    for flag in _RESULT_DENIAL_NAMES:
        if getattr(result, flag) is not False:
            raise OfflineChunkIndexRejected("chunk index result gained authority")
        stable_index()
        if type(result) is not _RESULT or any(a is not b for a, b in zip(
            (result.hits, result.scanned_count, result.source_sha256,
             result.index_inventory_sha256, result.evidence_sha256),
            final, strict=True,
        )) or any(
            type(row) is not _RESULT_HIT or row is not before
            or any(a is not b for a, b in zip(
                (row.chunk_index, row.start, row.end, row.document_id,
                 row.score, row.chunk_sha256), fields, strict=True,
            ))
            for row, (before, *fields) in zip(
                result.hits, final_hits, strict=True,
            )
        ):
            raise OfflineChunkIndexRejected("chunk index receipt changed")
    return result


_RESULT_HIT = OfflineChunkIndexHit
