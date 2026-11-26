"""Offline private search may never adopt replaced False-only authority getters."""

import hashlib

import pytest

from ark import offline_context_search as mod

OWNER = "a" * 64
SCOPE = "b" * 64
_FLAGS = (
    "consent_verified", "external_export_authorized",
    "tool_dispatch_authorized", "retention_authorized",
)


def _search():
    content = "private context alpha"
    row = mod.OfflineContextSearchRecord(
        "rec_" + "1" * 32, OWNER, SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 2000,
    )
    return mod.search_offline_context(
        (row,), owner_digest=OWNER, allowed_scope_digests=(SCOPE,),
        observed_at_ms=1000, query="alpha",
    )


@pytest.mark.parametrize("flag", _FLAGS)
def test_harmless_looking_false_descriptor_replacement_is_rejected(monkeypatch, flag):
    monkeypatch.setattr(
        mod.OfflineContextSearchPreview, flag,
        property(lambda _self: False),
    )
    with pytest.raises(mod.OfflineContextSearchRejected, match="descriptor"):
        _search()


@pytest.mark.parametrize("replace_flag", _FLAGS[1:])
def test_final_false_getter_cannot_swap_prior_authority_descriptor(
    monkeypatch, replace_flag,
):
    def replace_earlier(_self):
        monkeypatch.setattr(
            mod.OfflineContextSearchPreview,
            "consent_verified",
            property(lambda _review: False),
        )
        return False

    monkeypatch.setattr(
        mod.OfflineContextSearchPreview, replace_flag,
        property(replace_earlier),
    )
    with pytest.raises(mod.OfflineContextSearchRejected, match="descriptor"):
        _search()


def test_original_inert_preview_remains_available():
    review = _search()
    assert review.hits[0].excerpt == "private context alpha"
    assert all(getattr(review, flag) is False for flag in _FLAGS)
