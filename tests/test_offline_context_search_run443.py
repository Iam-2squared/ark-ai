"""Local lexical fixture retrieval and privacy non-authority regressions."""

import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark import offline_context_search as mod

OWNER = "a" * 64
SCOPE = "b" * 64
OTHER = "c" * 64


def record(number=1, content="alpha beta", **changes):
    source = mod.OfflineContextSearchRecord(
        f"rec_{number:032x}", OWNER, SCOPE, content,
        hashlib.sha256(content.encode("utf-8", "surrogatepass")).hexdigest(), 2000,
    )
    return replace(source, **changes)


def search(rows=None, **changes):
    return mod.search_offline_context(
        (record(),) if rows is None else rows,
        owner_digest=changes.get("owner", OWNER),
        allowed_scope_digests=changes.get("scopes", (SCOPE,)),
        observed_at_ms=changes.get("now", 1000),
        query=changes.get("query", "alpha"),
        max_hits=changes.get("limit", 8),
    )


def test_matched_content_and_deterministic_rank():
    one, two, three = record(1, "alpha beta"), record(2, "alpha alpha beta"), record(3, "none")
    result = search((one, two, three), query="alpha beta")
    assert tuple(hit.record_id for hit in result.hits) == (two.record_id, one.record_id)
    assert result.hits[0].score == 3
    assert "alpha" in result.hits[0].excerpt
    assert len(result.local_digest) == 64
    assert search((one, two, three), query="alpha beta") == result
    assert not result.consent_verified
    assert not result.external_export_authorized
    assert not result.tool_dispatch_authorized
    assert not result.retention_authorized


def test_no_matching_hits_and_hit_limit():
    result = search((record(),), query="unknown")
    assert result.hits == ()
    rows = tuple(record(i, content="alpha") for i in range(1, 10))
    assert len(search(rows, limit=3).hits) == 3


@pytest.mark.parametrize("changes", [
    {"owner_digest": OTHER}, {"scope_digest": OTHER},
    {"content_sha256": OTHER}, {"content_sha256": "bad"},
    {"record_id": "bad"}, {"record_id": None},
    {"content": "a" * 2049}, {"content": "🔥" * 600},
    {"content": "\ud800"}, {"expires_at_ms": 1000},
    {"expires_at_ms": True}, {"expires_at_ms": 2**63},
])
def test_all_foreign_corrupted_or_expired_rows_fail_closed(changes):
    # No silent filtering of a contaminated batch even if another row matches.
    with pytest.raises(mod.OfflineContextSearchRejected):
        search((record(1), record(2, **changes)))


@pytest.mark.parametrize("rows", [
    (), (record(2), record(1)), (record(1), record(1)),
    (record(1), record(2, "ok"), record(3, "ok"), record(4, "ok"),
     record(5, "ok"), record(6, "ok"), record(7, "ok"),
     record(8, "ok"), record(9, "a" * 2048), record(10, "a" * 2048),
     record(11, "a" * 2048), record(12, "a" * 2048), record(13, "a" * 2048)),
])
def test_bad_batch_order_or_aggregate_budget(rows):
    with pytest.raises(mod.OfflineContextSearchRejected):
        search(rows)


@pytest.mark.parametrize("options", [
    {"owner": OTHER}, {"owner": True}, {"scopes": (OTHER,)},
    {"scopes": (SCOPE, SCOPE)}, {"scopes": []},
    {"now": 2000}, {"now": -1}, {"now": True},
    {"query": ""}, {"query": "   "}, {"query": "a" * 257},
    {"query": "🔥" * 65}, {"query": "\ud800"},
    {"limit": 0}, {"limit": 9}, {"limit": True},
])
def test_invalid_scope_query_or_time_rejected(options):
    with pytest.raises(mod.OfflineContextSearchRejected):
        search(**options)


def test_casefold_and_query_normalization():
    value = search((record(content="ALPHA alpha beta"),), query="AlPhA   alpha")
    assert value.hits[0].score == 2


def test_mutated_record_during_hash_rejected(monkeypatch):
    row = record()
    original = mod.hashlib.sha256

    def altered(data):
        object.__setattr__(row, "content", "redirected")
        return original(data)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=altered))
    with pytest.raises(mod.OfflineContextSearchRejected, match="mutated"):
        search((row,))


def test_exact_fixture_types_required():
    class SubRecord(mod.OfflineContextSearchRecord):
        pass

    row = record()
    derived = SubRecord(
        row.record_id, row.owner_digest, row.scope_digest,
        row.content, row.content_sha256, row.expires_at_ms,
    )
    with pytest.raises(mod.OfflineContextSearchRejected):
        search((derived,))
