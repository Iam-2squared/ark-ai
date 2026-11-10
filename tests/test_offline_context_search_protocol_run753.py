"""Private context lexical fixtures retain their original protocol and budgets.

This is local-only fixture retrieval. The receipt cannot supply user consent,
external disclosure, trusted time, Memory provenance or tool authorization.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from ark import offline_context_search as search

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _fixture():
    content = "private alpha beta"
    return search.OfflineContextSearchRecord(
        "rec_" + "1" * 32, _OWNER, _SCOPE, content,
        hashlib.sha256(content.encode()).hexdigest(), 2000,
    )


def _run():
    return search.search_offline_context(
        (_fixture(),), owner_digest=_OWNER, allowed_scope_digests=(_SCOPE,),
        observed_at_ms=1000, query="alpha",
    )


@pytest.mark.parametrize("constant", (
    "_DIGEST", "_RECORD", "_DOMAIN", "_MAX_TIME", "_MAX_RECORDS",
    "_MAX_RECORD_BYTES", "_MAX_TOTAL_BYTES", "_MAX_QUERY_BYTES",
))
def test_rebound_privacy_parser_or_budget_is_denied_before_record_access(
    monkeypatch, constant,
):
    record = _fixture()
    original = search.OfflineContextSearchRecord
    observed = []
    if constant.startswith("_MAX"):
        replacement = 10**12
    else:
        replacement = object()
    with monkeypatch.context() as patch:
        patch.setattr(search, constant, replacement)
        # A source record's private content is never needed for the rejection.
        with pytest.raises(
            search.OfflineContextSearchRejected,
            match="search grammar, budget or codec changed",
        ):
            search.search_offline_context(
                (record,), owner_digest=_OWNER,
                allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
                query="alpha",
            )
    assert observed == []
    assert type(_run()) is search.OfflineContextSearchPreview
    assert original is search.OfflineContextSearchRecord


def test_replaced_owner_matcher_never_observes_owner_digest(monkeypatch):
    observed = []

    class MaliciousMatcher:
        def fullmatch(self, value):
            observed.append(value)
            raise AssertionError("owner digest exposed to replacement matcher")

    with monkeypatch.context() as patch:
        patch.setattr(search, "_DIGEST", MaliciousMatcher())
        with pytest.raises(
            search.OfflineContextSearchRejected,
            match="search grammar, budget or codec changed",
        ):
            _run()
    assert observed == []


@pytest.mark.parametrize("dependency", ("hashlib", "json", "_utf8"))
def test_private_fixture_never_reaches_unreviewed_codec(monkeypatch, dependency):
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("called")
        raise AssertionError("private content passed to replaced codec")

    with monkeypatch.context() as patch:
        if dependency == "hashlib":
            patch.setattr(search, dependency, SimpleNamespace(sha256=forbidden))
        elif dependency == "json":
            patch.setattr(search, dependency, SimpleNamespace(dumps=forbidden))
        else:
            patch.setattr(search, dependency, forbidden)
        with pytest.raises(
            search.OfflineContextSearchRejected,
            match="search grammar, budget or codec changed",
        ):
            _run()
    assert invoked == []


def test_valid_fixture_result_is_still_local_only():
    preview = _run()
    assert preview.hits[0].excerpt == "private alpha beta"
    assert preview.consent_verified is False
    assert preview.external_export_authorized is False
    assert preview.tool_dispatch_authorized is False
    assert preview.retention_authorized is False
