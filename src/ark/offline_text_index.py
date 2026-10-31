"""Bounded lexical search on explicitly provided, untrusted local text fixtures.

This disconnected implementation returns identifiers and scores, never snippets.
Caller-supplied hashes/scopes do not authenticate consent, ownership, or retention.
No filesystem, network, model, persistent Memory, or ToolBackend is accessed.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOC = re.compile(r"doc_[0-9a-f]{16}\Z")
_WORD = re.compile(r"\w+", re.UNICODE)
_DOMAIN = b"ARK-detached-local-text-index-v1\0"
_MAX_DOCS = 32
_MAX_TEXT_BYTES = 65_536
_MAX_TOTAL_BYTES = 131_072
_MAX_QUERY_BYTES = 512
_MAX_QUERY_TOKENS = 16
_MAX_TOKENS = 30_000


class OfflineIndexRejected(ValueError):
    """An untrusted document, query, budget, or membership is inconsistent."""


@dataclass(frozen=True, slots=True)
class OfflineIndexDocument:
    document_id: str
    owner_sha256: str
    scope_sha256: str
    text_sha256: str
    text: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class OfflineIndexQuery:
    owner_sha256: str
    scope_sha256: str
    query_sha256: str
    query: str = field(repr=False)
    documents: tuple[OfflineIndexDocument, ...]
    expected_document_ids: tuple[str, ...]
    limit: int = 8


@dataclass(frozen=True, slots=True)
class OfflineIndexHit:
    document_id: str
    distinct_matches: int
    score: int
    document_sha256: str


@dataclass(frozen=True, slots=True)
class OfflineIndexResult:
    hits: tuple[OfflineIndexHit, ...]
    scanned_count: int
    query_token_count: int
    inventory_sha256: str
    result_sha256: str

    @property
    def identity_authenticated(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def revocation_verified(self) -> bool:
        return False


# The original denial-only result and hit carriers cannot be swapped by a
# reentrant synthetic constructor during evidence assembly.
_RESULT_TYPE = OfflineIndexResult
_HIT_TYPE = OfflineIndexHit


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _encode_text(value: object, maximum: int, *, empty_allowed: bool) -> bytes:
    if type(value) is not str or (not value and not empty_allowed):
        raise OfflineIndexRejected("expected exact local text")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise OfflineIndexRejected("invalid Unicode") from exc
    if len(encoded) > maximum:
        raise OfflineIndexRejected("local text budget exceeded")
    return encoded


def _tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return _WORD.findall(normalized)


def _digest(label: str, item: object) -> str:
    payload = json.dumps(
        item, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + label.encode("ascii") + b"\0" + payload).hexdigest()


def search_offline_text(query: OfflineIndexQuery) -> OfflineIndexResult:
    """Search a *complete* bounded exact local corpus; never returns raw text.

    The expected ID list is a caller assertion, not independent custody proof.
    Scores are deterministic integers: 100 per distinct matched query token,
    plus at most 8 for each token's term frequency. Ties use document ID.
    """
    if type(query) is not OfflineIndexQuery:
        raise OfflineIndexRejected("exact query object required")
    original = (
        query.owner_sha256, query.scope_sha256, query.query_sha256, query.query,
        query.documents, query.expected_document_ids, query.limit,
    )
    if (
        type(query.documents) is not tuple
        or not 1 <= len(query.documents) <= _MAX_DOCS
        or type(query.expected_document_ids) is not tuple
        or len(query.expected_document_ids) != len(query.documents)
    ):
        raise OfflineIndexRejected("invalid document collection")
    rows = tuple(query.documents)
    pinned = tuple(
        (row.document_id, row.owner_sha256, row.scope_sha256,
         row.text_sha256, row.text)
        if type(row) is OfflineIndexDocument else None
        for row in rows
    )

    def check_epoch() -> None:
        current = (
            query.owner_sha256, query.scope_sha256, query.query_sha256, query.query,
            query.documents, query.expected_document_ids, query.limit,
        )
        if (
            any(a is not b for a, b in zip(current, original, strict=True))
            or any(row is not query.documents[i] for i, row in enumerate(rows))
            or any(
                type(row) is not OfflineIndexDocument
                or any(a is not b for a, b in zip(
                    (row.document_id, row.owner_sha256, row.scope_sha256,
                     row.text_sha256, row.text), pinned[i], strict=True,
                ))
                for i, row in enumerate(rows)
            )
        ):
            raise OfflineIndexRejected("source carriers changed during local index review")

    check_epoch()
    owner, scope, declared_query_sha, query_text, _, expected, limit = original
    if (
        not _sha(owner) or not _sha(scope) or not _sha(declared_query_sha)
        or type(limit) is not int or not 1 <= limit <= 8
    ):
        raise OfflineIndexRejected("invalid query identity or result budget")
    query_bytes = _encode_text(query_text, _MAX_QUERY_BYTES, empty_allowed=False)
    if hashlib.sha256(query_bytes).hexdigest() != declared_query_sha:
        raise OfflineIndexRejected("query digest mismatch")
    terms = _tokens(query_text)
    if not 1 <= len(terms) <= _MAX_QUERY_TOKENS:
        raise OfflineIndexRejected("query token count out of bounds")
    distinct_terms = tuple(sorted(set(terms)))
    if len(distinct_terms) > _MAX_QUERY_TOKENS:
        raise OfflineIndexRejected("query unique-token budget exceeded")
    check_epoch()
    seen: set[str] = set()
    size = 0
    tokens_total = 0
    candidates: list[OfflineIndexHit] = []
    manifest: list[tuple[str, str]] = []
    for row in pinned:
        check_epoch()
        if row is None:
            raise OfflineIndexRejected("invalid document carrier")
        doc_id, doc_owner, doc_scope, declared_text_sha, text = row
        if (
            type(doc_id) is not str or _DOC.fullmatch(doc_id) is None
            or doc_id in seen or doc_owner != owner or doc_scope != scope
            or not _sha(declared_text_sha)
        ):
            raise OfflineIndexRejected("document identity, scope, or membership invalid")
        seen.add(doc_id)
        raw = _encode_text(text, _MAX_TEXT_BYTES, empty_allowed=True)
        size += len(raw)
        if size > _MAX_TOTAL_BYTES:
            raise OfflineIndexRejected("total local index byte budget exceeded")
        if hashlib.sha256(raw).hexdigest() != declared_text_sha:
            raise OfflineIndexRejected("document content digest mismatch")
        token_list = _tokens(text)
        tokens_total += len(token_list)
        if tokens_total > _MAX_TOKENS:
            raise OfflineIndexRejected("local token budget exceeded")
        frequencies = Counter(token_list)
        matching = tuple(term for term in distinct_terms if term in frequencies)
        if matching:
            score = 100 * len(matching) + sum(min(frequencies[term], 8) for term in matching)
            candidates.append(OfflineIndexHit(doc_id, len(matching), score, declared_text_sha))
        manifest.append((doc_id, declared_text_sha))
        check_epoch()
    if (
        any(type(item) is not str or _DOC.fullmatch(item) is None for item in expected)
        or tuple(sorted(seen)) != tuple(expected)
    ):
        raise OfflineIndexRejected("complete ordered document membership mismatch")
    inventory = _digest("inventory", (owner, scope, manifest))
    hits = tuple(sorted(candidates, key=lambda row: (-row.score, row.document_id))[:limit])
    result = _digest("result", (
        inventory, declared_query_sha, distinct_terms,
        [(r.document_id, r.score, r.distinct_matches, r.document_sha256) for r in hits],
    ))
    check_epoch()
    # A hit and its tuple element are the same mutable-under-reflection object.
    # Preserve field carriers separately; comparing hit to itself is not a
    # post-callback integrity check.
    hit_epochs = tuple((
        hit, hit.document_id, hit.distinct_matches, hit.score, hit.document_sha256,
    ) for hit in hits)
    output = OfflineIndexResult(hits, len(rows), len(terms), inventory, result)

    def assert_output() -> None:
        check_epoch()
        if (
            type(output) is not _RESULT_TYPE
            or output.hits is not hits
            or type(output.scanned_count) is not int
            or output.scanned_count != len(rows)
            or type(output.query_token_count) is not int
            or output.query_token_count != len(terms)
            or output.inventory_sha256 is not inventory
            or output.result_sha256 is not result
            or any(
                type(hit) is not _HIT_TYPE
                or hit is not original
                or hit.document_id is not doc_id
                or type(hit.distinct_matches) is not int
                or hit.distinct_matches != matches
                or type(hit.score) is not int
                or hit.score != score
                or hit.document_sha256 is not content_hash
                for hit, (original, doc_id, matches, score, content_hash) in zip(
                    output.hits, hit_epochs, strict=True,
                )
            )
        ):
            raise OfflineIndexRejected("local index result carrier changed")

    assert_output()
    # A detached lexical hit is never authenticated source custody, live
    # consent, revocation freshness, or authority for content disclosure.
    if (
        output.identity_authenticated is not False
        or output.disclosure_authorized is not False
        or output.revocation_verified is not False
    ):
        raise OfflineIndexRejected("local index result authority changed")
    # Authority descriptors may have altered nested hits or source carriers.
    assert_output()
    return output
