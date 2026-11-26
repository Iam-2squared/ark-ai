"""On-device lexical search of explicit synthetic context fixtures only.

This is not a MemoryStore reader or a permission check. The returned excerpts
may contain private fixture text; never export, persist or execute them without
separate verified authority. Synthetic time and scope digests are untrusted.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_RECORD = re.compile(r"rec_[0-9a-f]{32}\Z")
_DOMAIN = b"ARK-offline-context-lexical-search-v1\0"
_MAX_TIME = 2**63 - 1
_MAX_RECORDS = 32
_MAX_RECORD_BYTES = 2_048
_MAX_TOTAL_BYTES = 8_192
_MAX_QUERY_BYTES = 256
# Treat the digest grammar and fixture-byte budgets as part of the locally
# reviewed privacy protocol, not mutable knobs supplied by a caller.
_ORIGINAL_DIGEST_PATTERN = _DIGEST
_ORIGINAL_RECORD_PATTERN = _RECORD
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_TIME = _MAX_TIME
_ORIGINAL_MAX_RECORDS = _MAX_RECORDS
_ORIGINAL_MAX_RECORD_BYTES = _MAX_RECORD_BYTES
_ORIGINAL_MAX_TOTAL_BYTES = _MAX_TOTAL_BYTES
_ORIGINAL_MAX_QUERY_BYTES = _MAX_QUERY_BYTES
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps


class OfflineContextSearchRejected(ValueError):
    """A search fixture is mismatched, stale, mutated or unbounded."""


@dataclass(frozen=True, slots=True)
class OfflineContextSearchRecord:
    record_id: str
    owner_digest: str
    scope_digest: str
    content: str = field(repr=False)
    content_sha256: str
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class OfflineContextSearchHit:
    record_id: str
    score: int
    excerpt: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class OfflineContextSearchPreview:
    owner_digest: str
    query: str = field(repr=False)
    hits: tuple[OfflineContextSearchHit, ...]
    local_digest: str

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def external_export_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def retention_authorized(self) -> bool:
        return False


# The private input record's frozen slot descriptors are executable if
# replaced with properties; pin them before reading any fixture content.
_RECORD_TYPE = OfflineContextSearchRecord
_RECORD_FIELDS = (
    "record_id", "owner_digest", "scope_digest", "content",
    "content_sha256", "expires_at_ms",
)
_ORIGINAL_RECORD_FIELDS = tuple(vars(_RECORD_TYPE)[name] for name in _RECORD_FIELDS)
_ORIGINAL_RECORD_LOOKUPS = (
    vars(_RECORD_TYPE).get("__getattribute__"),
    vars(_RECORD_TYPE).get("__getattr__"),
)
# Pin the original inert carrier classes against synthetic constructor injection.
_RESULT_TYPE = OfflineContextSearchPreview
_HIT_TYPE = OfflineContextSearchHit
_DENIALS = (
    "consent_verified", "external_export_authorized",
    "tool_dispatch_authorized", "retention_authorized",
)
_DENIAL_DESCRIPTORS = tuple(vars(_RESULT_TYPE)[key] for key in _DENIALS)
_ORIGINAL_RESULT_INIT = vars(_RESULT_TYPE)["__init__"]
_ORIGINAL_HIT_INIT = vars(_HIT_TYPE)["__init__"]
# A frozen result can still have its fields or inherited lookup hooks
# replaced at class level. Pin both nested hit and outer result carriers
# before hashing or constructing a preview with private fixture excerpts.
_RESULT_FIELDS = ("owner_digest", "query", "hits", "local_digest")
_HIT_FIELDS = ("record_id", "score", "excerpt")
_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT_TYPE)[name] for name in _RESULT_FIELDS)
_ORIGINAL_HIT_FIELDS = tuple(vars(_HIT_TYPE)[name] for name in _HIT_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(vars(_RESULT_TYPE).get(name) for name in _RESULT_HOOKS)
_ORIGINAL_HIT_HOOKS = tuple(vars(_HIT_TYPE).get(name) for name in _RESULT_HOOKS)


def _require_original_constructors() -> None:
    if (
        OfflineContextSearchRecord is not _RECORD_TYPE
        or any(
            vars(_RECORD_TYPE).get(name) is not original
            for name, original in zip(
                _RECORD_FIELDS, _ORIGINAL_RECORD_FIELDS, strict=True,
            )
        )
        or vars(_RECORD_TYPE).get("__getattribute__") is not _ORIGINAL_RECORD_LOOKUPS[0]
        or vars(_RECORD_TYPE).get("__getattr__") is not _ORIGINAL_RECORD_LOOKUPS[1]
        or OfflineContextSearchPreview is not _RESULT_TYPE
        or OfflineContextSearchHit is not _HIT_TYPE
        or vars(_RESULT_TYPE).get("__init__") is not _ORIGINAL_RESULT_INIT
        or vars(_HIT_TYPE).get("__init__") is not _ORIGINAL_HIT_INIT
        or any(
            vars(cls).get(name) is not saved
            for cls, names, originals in (
                (_RESULT_TYPE, _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_HIT_TYPE, _HIT_FIELDS, _ORIGINAL_HIT_FIELDS),
                (_RESULT_TYPE, _RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS),
                (_HIT_TYPE, _RESULT_HOOKS, _ORIGINAL_HIT_HOOKS),
            )
            for name, saved in zip(names, originals, strict=True)
        )
    ):
        raise OfflineContextSearchRejected(
            "search preview result changed: constructor identity mismatch"
        )


def _require_original_denials() -> None:
    # A forged descriptor may impersonate the original on class access.
    # Never execute its __get__, including before reading private fixtures.
    if any(
        vars(_RESULT_TYPE).get(name) is not original
        for name, original in zip(
            _DENIALS, _DENIAL_DESCRIPTORS, strict=True,
        )
    ):
        raise OfflineContextSearchRejected(
            "search preview authority descriptor changed"
        )


def _utf8(value: str) -> bytes:
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise OfflineContextSearchRejected("invalid Unicode") from exc


_ORIGINAL_UTF8 = _utf8


def _require_original_search_protocol() -> None:
    # Check before a replaced regex matcher or digest callback could observe
    # even the caller's owner/scope/query metadata, let alone record content.
    if (
        _DIGEST is not _ORIGINAL_DIGEST_PATTERN
        or _RECORD is not _ORIGINAL_RECORD_PATTERN
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or type(_MAX_TIME) is not int or _MAX_TIME != _ORIGINAL_MAX_TIME
        or type(_MAX_RECORDS) is not int
        or _MAX_RECORDS != _ORIGINAL_MAX_RECORDS
        or type(_MAX_RECORD_BYTES) is not int
        or _MAX_RECORD_BYTES != _ORIGINAL_MAX_RECORD_BYTES
        or type(_MAX_TOTAL_BYTES) is not int
        or _MAX_TOTAL_BYTES != _ORIGINAL_MAX_TOTAL_BYTES
        or type(_MAX_QUERY_BYTES) is not int
        or _MAX_QUERY_BYTES != _ORIGINAL_MAX_QUERY_BYTES
        or hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _utf8 is not _ORIGINAL_UTF8
    ):
        raise OfflineContextSearchRejected("search grammar, budget or codec changed")


def search_offline_context(
    fixtures: tuple[OfflineContextSearchRecord, ...],
    *,
    owner_digest: str,
    allowed_scope_digests: tuple[str, ...],
    observed_at_ms: int,
    query: str,
    max_hits: int = 8,
) -> OfflineContextSearchPreview:
    """Return bounded local excerpts; reject ALL records if any is unsafe.

    The literal query is retained locally in the return value. This never
    verifies consent, identity, revocation freshness or storage provenance.
    """
    _require_original_denials()
    _require_original_constructors()
    _require_original_search_protocol()
    if (
        type(fixtures) is not tuple or not 1 <= len(fixtures) <= _MAX_RECORDS
        or any(type(row) is not OfflineContextSearchRecord for row in fixtures)
        or type(owner_digest) is not str or _DIGEST.fullmatch(owner_digest) is None
        or type(allowed_scope_digests) is not tuple
        or not 1 <= len(allowed_scope_digests) <= _MAX_RECORDS
        or any(type(scope) is not str or _DIGEST.fullmatch(scope) is None
               for scope in allowed_scope_digests)
        or tuple(sorted(set(allowed_scope_digests))) != allowed_scope_digests
        or type(observed_at_ms) is not int or not 0 <= observed_at_ms <= _MAX_TIME
        or type(query) is not str or not 0 < len(query) <= _MAX_QUERY_BYTES
        or type(max_hits) is not int or not 1 <= max_hits <= 8
    ):
        raise OfflineContextSearchRejected("invalid exact bounded search batch")
    if len(_utf8(query)) > _MAX_QUERY_BYTES:
        raise OfflineContextSearchRejected("query byte budget exceeded")
    terms = tuple(dict.fromkeys(token.casefold() for token in query.split()))
    if not 1 <= len(terms) <= 12 or any(len(_utf8(term)) > 128 for term in terms):
        raise OfflineContextSearchRejected("invalid search tokens")
    if any(not term.strip() for term in terms):
        raise OfflineContextSearchRejected("empty search token")
    roots = (fixtures, owner_digest, allowed_scope_digests, observed_at_ms, query, max_hits)
    rows = tuple(fixtures)
    fields = tuple((row.record_id, row.owner_digest, row.scope_digest,
                    row.content, row.content_sha256, row.expires_at_ms)
                   for row in rows)

    def assert_epoch() -> None:
        _require_original_denials()
        _require_original_constructors()
        _require_original_search_protocol()
        if (
            any(now is not before for now, before in zip(
                (fixtures, owner_digest, allowed_scope_digests, observed_at_ms, query, max_hits),
                roots, strict=True,
            ))
            or any(
                new is not original or any(
                    actual is not old for actual, old in zip(
                        (new.record_id, new.owner_digest, new.scope_digest,
                         new.content, new.content_sha256, new.expires_at_ms),
                        saved, strict=True,
                    )
                )
                for new, original, saved in zip(fixtures, rows, fields, strict=True)
            )
        ):
            raise OfflineContextSearchRejected("search carrier mutated during review")

    total = 0
    last_id = ""
    scored: list[tuple[int, str, str]] = []
    for _row, saved in zip(rows, fields, strict=True):
        assert_epoch()
        record_id, owner, scope, content, digest, expires = saved
        if (
            type(record_id) is not str or _RECORD.fullmatch(record_id) is None
            or record_id <= last_id or type(owner) is not str or owner != owner_digest
            or type(scope) is not str or scope not in allowed_scope_digests
            or type(content) is not str or len(content) > _MAX_RECORD_BYTES
            or type(digest) is not str or _DIGEST.fullmatch(digest) is None
            or type(expires) is not int or not observed_at_ms < expires <= _MAX_TIME
        ):
            raise OfflineContextSearchRejected("stale, unordered or foreign search record")
        last_id = record_id
        raw = _utf8(content)
        total += len(raw)
        if len(raw) > _MAX_RECORD_BYTES or total > _MAX_TOTAL_BYTES:
            raise OfflineContextSearchRejected("search content byte budget exceeded")
        if hashlib.sha256(raw).hexdigest() != digest:
            raise OfflineContextSearchRejected("search record hash mismatch")
        assert_epoch()
        # A full Unicode casefold may expand one source character into
        # several normalized codepoints (e.g. ß -> ss). Folded offsets are
        # not valid slice positions in the original private fixture text.
        folded_parts: list[str] = []
        original_positions: list[int] = []
        for position, character in enumerate(content):
            folded = character.casefold()
            folded_parts.append(folded)
            original_positions.extend([position] * len(folded))
        normalized = "".join(folded_parts)
        if all(term in normalized for term in terms):
            score = sum(normalized.count(term) for term in terms)
            first_folded, first_term = min(
                (normalized.find(term), term) for term in terms
            )
            first_source = original_positions[first_folded]
            last_folded = first_folded + len(first_term) - 1
            last_source = original_positions[last_folded] + 1
            # Each query token is accepted up to 128 UTF-8 bytes. A fixed
            # first_source+96 excerpt could truncate a longer matching token,
            # and casefold-expanded offsets cannot index the source directly.
            # Include the entire earliest matched term with bounded context:
            # at most 64 preceding + 128 matched + 64 following codepoints.
            begin = max(0, first_source - 64)
            end = min(len(content), max(first_source + 96, last_source + 64))
            excerpt = content[begin:end]
            scored.append((score, record_id, excerpt))
        assert_epoch()
    scored.sort(key=lambda item: (-item[0], item[1]))
    assert_epoch()
    selected = tuple(scored[:max_hits])
    _require_original_constructors()
    hits = tuple(OfflineContextSearchHit(record_id, score, excerpt)
                 for score, record_id, excerpt in selected)
    payload = json.dumps(
        {"owner_digest": owner_digest, "query": query,
         "hits": [(hit.record_id, hit.score, hit.excerpt) for hit in hits]},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
    )
    assert_epoch()
    local_digest = hashlib.sha256(_DOMAIN + payload.encode("utf-8")).hexdigest()
    assert_epoch()
    _require_original_constructors()
    result = OfflineContextSearchPreview(owner_digest, query, hits, local_digest)
    _require_original_constructors()
    def assert_result() -> None:
        assert_epoch()
        if (
            type(result) is not _RESULT_TYPE
            or result.owner_digest is not owner_digest
            or result.query is not query
            or result.hits is not hits
            or result.local_digest is not local_digest
            or any(
                type(hit) is not _HIT_TYPE
                or hit.record_id is not record_id
                or type(hit.score) is not int or hit.score != score
                or hit.excerpt is not excerpt
                for hit, (score, record_id, excerpt) in zip(
                    result.hits, selected, strict=True,
                )
            )
        ):
            raise OfflineContextSearchRejected("search preview result changed")

    assert_result()
    # False-only authority getters are arbitrary callbacks. Recheck original
    # descriptors and result/source carriers after EACH getter, including the
    # last, so a swapped False-valued descriptor never becomes a silent grant.
    for index, key in enumerate(_DENIALS):
        _require_original_denials()
        if getattr(result, key) is not False:
            raise OfflineContextSearchRejected("search preview authority changed")
        assert_result()
        # Check inspected descriptors now, but do not preempt a later getter:
        # a later callback may itself mutate the source/result, which must be
        # reported by the original post-callback integrity diagnostic.
        if any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _DENIALS[:index + 1],
                _DENIAL_DESCRIPTORS[:index + 1],
                strict=True,
            )
        ):
            raise OfflineContextSearchRejected(
                "search preview authority descriptor changed"
            )
        assert_result()
    if any(
        vars(_RESULT_TYPE).get(name) is not original
        for name, original in zip(_DENIALS, _DENIAL_DESCRIPTORS, strict=True)
    ):
        raise OfflineContextSearchRejected("search preview authority descriptor changed")
    assert_result()
    return result
