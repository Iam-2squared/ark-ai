"""Offline private search refuses executable nested result descriptors before use.

Synthetic fixture only: these local excerpts are not disclosure consent, an
export permission, retained Memory provenance, or a ToolBackend grant.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import offline_context_search as context


def _fixture():
    value = "synthetic private alpha beta"
    row = context.OfflineContextSearchRecord(
        "rec_" + "1" * 32, "a" * 64, "b" * 64,
        value, hashlib.sha256(value.encode()).hexdigest(), 2000,
    )
    return (row,)


def _search(rows):
    return context.search_offline_context(
        rows, owner_digest="a" * 64, allowed_scope_digests=("b" * 64,),
        observed_at_ms=1000, query="alpha",
    )


@pytest.mark.parametrize(("name", "slot"), [
    ("OfflineContextSearchPreview", "owner_digest"),
    ("OfflineContextSearchPreview", "query"),
    ("OfflineContextSearchPreview", "hits"),
    ("OfflineContextSearchPreview", "local_digest"),
    ("OfflineContextSearchHit", "record_id"),
    ("OfflineContextSearchHit", "score"),
    ("OfflineContextSearchHit", "excerpt"),
    ("OfflineContextSearchPreview", "__getattribute__"),
    ("OfflineContextSearchHit", "__getattribute__"),
    ("OfflineContextSearchPreview", "__getattr__"),
    ("OfflineContextSearchHit", "__getattr__"),
])
def test_preinstalled_poisoned_result_slot_does_not_execute(
    monkeypatch, name, slot,
):
    rows = _fixture()
    called = []

    def forbidden(*_args):
        called.append(slot)
        raise AssertionError("executable result slot must never run")

    with monkeypatch.context() as patch:
        if slot.startswith("__"):
            patch.setattr(getattr(context, name), slot, forbidden, raising=False)
        else:
            patch.setattr(getattr(context, name), slot, property(forbidden))
        with pytest.raises(
            context.OfflineContextSearchRejected,
            match="constructor identity mismatch",
        ):
            _search(rows)
    assert called == []


@pytest.mark.parametrize(("name", "slot"), [
    ("OfflineContextSearchPreview", "hits"),
    ("OfflineContextSearchHit", "excerpt"),
])
def test_reentrant_query_hook_cannot_install_executable_result_slot(
    monkeypatch, name, slot,
):
    rows = _fixture()
    called = []
    original = context._utf8

    def forbidden(*_args):
        called.append("invoked")
        raise AssertionError("injected result accessor must never execute")

    with monkeypatch.context() as patch:
        def mutate_on_query(value):
            payload = original(value)
            if value == "alpha":
                patch.setattr(getattr(context, name), slot, property(forbidden))
            return payload

        patch.setattr(context, "_utf8", mutate_on_query)
        with pytest.raises(
            context.OfflineContextSearchRejected,
            match="constructor identity mismatch|search grammar, budget or codec changed",
        ):
            _search(rows)
    assert called == []


def test_unmodified_private_preview_is_still_deny_only():
    preview = _search(_fixture())
    assert preview.hits[0].excerpt == "synthetic private alpha beta"
    assert preview.hits[0].score == 1
    assert preview.consent_verified is False
    assert preview.external_export_authorized is False
    assert preview.tool_dispatch_authorized is False
    assert preview.retention_authorized is False
