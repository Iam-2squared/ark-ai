"""Privacy-safe Unicode source indexing in disconnected fixture search."""

import hashlib

import pytest

from ark import offline_context_search as mod


@pytest.mark.parametrize("prefix", ["ß" * 80, "İ" * 80, "ﬃ" * 80])
@pytest.mark.parametrize("query", ["needle", "NEEDLE"])
def test_casefold_expansion_keeps_original_hit_in_excerpt(prefix, query):
    content = prefix + "needle" + " trailing"
    row = mod.OfflineContextSearchRecord(
        "rec_" + "1" * 32,
        "a" * 64,
        "b" * 64,
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        2000,
    )
    kwargs = {
        "owner_digest": "a" * 64,
        "allowed_scope_digests": ("b" * 64,),
        "observed_at_ms": 1000,
        "query": query,
    }
    result = mod.search_offline_context((row,), **kwargs)
    assert len(result.hits) == 1
    assert result.hits[0].score == 1
    assert "needle" in result.hits[0].excerpt
    assert result.hits[0].excerpt == content[16:176]
    assert result == mod.search_offline_context((row,), **kwargs)
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.retention_authorized is False


def test_expanded_casefold_query_score_still_matches_source_text():
    content = "prefix ß and ss"
    row = mod.OfflineContextSearchRecord(
        "rec_" + "1" * 32,
        "a" * 64,
        "b" * 64,
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        2000,
    )
    result = mod.search_offline_context(
        (row,),
        owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,),
        observed_at_ms=1000,
        query="ss",
    )
    assert result.hits[0].score == 2
    assert result.hits[0].excerpt == content
