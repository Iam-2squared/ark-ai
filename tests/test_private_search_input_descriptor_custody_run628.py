"""Never invoke a counterfeit private record getter during local search.

Records are constructed before hostile descriptor injection. No real personal
account, external search, retention approval or disclosure is exercised.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

import ark.offline_context_search as search


def _case():
    content = "private alpha fixture"
    row = search.OfflineContextSearchRecord(
        "rec_" + "1" * 32, "a" * 64, "b" * 64, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 2000,
    )
    return (row,)


def _review(rows):
    return search.search_offline_context(
        rows, owner_digest="a" * 64, allowed_scope_digests=("b" * 64,),
        observed_at_ms=1000, query="alpha",
    )


@pytest.mark.parametrize(
    "descriptor",
    ("__getattribute__", "__getattr__", "content", "owner_digest", "expires_at_ms"),
)
def test_preinstalled_private_input_getter_never_executes(
    monkeypatch, descriptor,
):
    rows = _case()
    invoked = []

    def hostile(*args):
        invoked.append(args)
        raise AssertionError("private input getter should not execute")

    replacement = (
        hostile if descriptor.startswith("__") else property(hostile)
    )
    monkeypatch.setattr(
        search.OfflineContextSearchRecord, descriptor, replacement, raising=False,
    )
    with pytest.raises(search.OfflineContextSearchRejected, match="constructor identity"):
        _review(rows)
    assert invoked == []


def test_input_descriptor_swapped_during_content_hash_is_denied(
    monkeypatch,
):
    rows = _case()
    invoked = []
    original = hashlib.sha256

    def hostile(self):
        invoked.append(True)
        raise AssertionError("private input getter should not execute")

    def reentrant_digest(data=b"", *args, **kwargs):
        if type(data) is bytes and b"private alpha" in data:
            monkeypatch.setattr(
                search.OfflineContextSearchRecord, "content", property(hostile),
            )
        return original(data, *args, **kwargs)

    monkeypatch.setattr(
        search, "hashlib", SimpleNamespace(sha256=reentrant_digest),
    )
    # The reviewed codec itself is now checked before private bytes are read.
    with pytest.raises(
        search.OfflineContextSearchRejected,
        match="search grammar, budget or codec changed",
    ):
        _review(rows)
    assert invoked == []


def test_unmodified_private_search_remains_local_and_denial_only():
    result = _review(_case())
    assert len(result.hits) == 1
    assert result.hits[0].score == 1
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
