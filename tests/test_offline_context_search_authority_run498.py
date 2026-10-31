"""Synthetic Personal Context search output is never a consent or disclosure grant."""

import hashlib

import pytest

from ark import offline_context_search as mod


def _record():
    content = "private alpha beta"
    return mod.OfflineContextSearchRecord(
        "rec_" + "1" * 32, "a" * 64, "b" * 64, content,
        hashlib.sha256(content.encode()).hexdigest(), 2000,
    )


def _search(row):
    return mod.search_offline_context(
        (row,), owner_digest="a" * 64, allowed_scope_digests=("b" * 64,),
        observed_at_ms=1000, query="alpha",
    )


def test_valid_private_search_is_still_inert():
    result = _search(_record())
    assert result.hits[0].excerpt == "private alpha beta"
    assert result.consent_verified is False
    assert result.external_export_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.retention_authorized is False


@pytest.mark.parametrize("authority", [
    "consent_verified", "external_export_authorized",
    "tool_dispatch_authorized", "retention_authorized",
])
def test_nominal_search_grant_forgery_is_rejected(monkeypatch, authority):
    monkeypatch.setattr(
        mod.OfflineContextSearchPreview, authority,
        property(lambda _self: True),
    )
    with pytest.raises(mod.OfflineContextSearchRejected, match="authority"):
        _search(_record())


def test_authority_getter_cannot_replace_result_after_validation(monkeypatch):
    def change_result(self):
        object.__setattr__(self, "local_digest", "0" * 64)
        return False

    monkeypatch.setattr(
        mod.OfflineContextSearchPreview, "retention_authorized",
        property(change_result),
    )
    with pytest.raises(mod.OfflineContextSearchRejected, match="result changed"):
        _search(_record())


def test_authority_getter_cannot_replace_nested_hit_after_validation(monkeypatch):
    def change_hit(self):
        object.__setattr__(self.hits[0], "excerpt", "tampered secret")
        return False

    monkeypatch.setattr(
        mod.OfflineContextSearchPreview, "tool_dispatch_authorized",
        property(change_hit),
    )
    with pytest.raises(mod.OfflineContextSearchRejected, match="result changed"):
        _search(_record())


def test_authority_getter_cannot_replace_source_after_validation(monkeypatch):
    row = _record()

    def change_source(_self):
        object.__setattr__(row, "expires_at_ms", 999)
        return False

    monkeypatch.setattr(
        mod.OfflineContextSearchPreview, "retention_authorized",
        property(change_source),
    )
    with pytest.raises(mod.OfflineContextSearchRejected, match="carrier mutated"):
        _search(row)


def test_synthetic_result_constructor_substitution_rejected(monkeypatch):
    class DerivedPreview(mod.OfflineContextSearchPreview):
        pass

    monkeypatch.setattr(mod, "OfflineContextSearchPreview", DerivedPreview)
    with pytest.raises(mod.OfflineContextSearchRejected, match="result changed"):
        _search(_record())
