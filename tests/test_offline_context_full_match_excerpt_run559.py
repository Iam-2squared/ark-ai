"""A private lexical excerpt must contain its first complete Unicode match.

These are explicit offline fixtures, not consent to disclose or tool dispatch.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import offline_context_search as search


@pytest.mark.parametrize("prefix", ["p" * 80, "ß" * 80, "İ" * 80])
@pytest.mark.parametrize("match_length", [110, 128])
def test_long_earliest_match_is_not_truncated(prefix, match_length):
    term = "X" * match_length
    content = prefix + term + "z" * 400
    row = search.OfflineContextSearchRecord(
        "rec_" + "a" * 32, "b" * 64, "c" * 64, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 2000,
    )
    kwargs = {
        "owner_digest": "b" * 64,
        "allowed_scope_digests": ("c" * 64,),
        "observed_at_ms": 1000,
        "query": term.lower(),
    }
    result = search.search_offline_context((row,), **kwargs)
    assert len(result.hits) == 1
    hit = result.hits[0]
    assert hit.score == 1
    assert term in hit.excerpt
    assert len(hit.excerpt) <= 256
    assert hit.excerpt == content[max(0, len(prefix) - 64):
                                  len(prefix) + match_length + 64]
    assert search.search_offline_context((row,), **kwargs) == result
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False


def test_short_match_keeps_existing_96_character_following_window():
    content = "p" * 80 + "N" + "z" * 200
    row = search.OfflineContextSearchRecord(
        "rec_" + "b" * 32, "b" * 64, "c" * 64, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 2000,
    )
    result = search.search_offline_context(
        (row,), owner_digest="b" * 64,
        allowed_scope_digests=("c" * 64,), observed_at_ms=1000,
        query="n",
    )
    assert result.hits[0].excerpt == content[16:176]
    assert result.consent_verified is False
    assert result.retention_authorized is False
