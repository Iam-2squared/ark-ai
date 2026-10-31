"""Detached Memory-like lexical index results must remain denial-only."""

import hashlib

import pytest

from ark import offline_text_index as mod


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _request():
    doc = mod.OfflineIndexDocument(
        "doc_" + "1" * 16, "a" * 64, "b" * 64,
        _sha("private alpha"), "private alpha",
    )
    return mod.OfflineIndexQuery(
        "a" * 64, "b" * 64, _sha("alpha"), "alpha",
        (doc,), (doc.document_id,),
    )


def test_valid_local_index_remains_a_non_authority():
    result = mod.search_offline_text(_request())
    assert len(result.hits) == 1
    assert result.identity_authenticated is False
    assert result.disclosure_authorized is False
    assert result.revocation_verified is False
    assert "private" not in repr(result)


@pytest.mark.parametrize("flag", [
    "identity_authenticated", "disclosure_authorized", "revocation_verified",
])
def test_forged_result_authority_rejected(monkeypatch, flag):
    monkeypatch.setattr(
        mod.OfflineIndexResult, flag, property(lambda _self: True),
    )
    with pytest.raises(mod.OfflineIndexRejected, match="authority"):
        mod.search_offline_text(_request())


def test_authority_getter_mutation_of_result_rejected(monkeypatch):
    def change_result(self):
        object.__setattr__(self, "result_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        mod.OfflineIndexResult, "revocation_verified", property(change_result),
    )
    with pytest.raises(mod.OfflineIndexRejected, match="result carrier"):
        mod.search_offline_text(_request())


def test_authority_getter_mutation_of_nested_hit_rejected(monkeypatch):
    def change_hit(self):
        object.__setattr__(self.hits[0], "score", 9_999)
        return False

    monkeypatch.setattr(
        mod.OfflineIndexResult, "revocation_verified", property(change_hit),
    )
    with pytest.raises(mod.OfflineIndexRejected, match="result carrier"):
        mod.search_offline_text(_request())


def test_authority_getter_mutation_of_source_carrier_rejected(monkeypatch):
    request = _request()

    def change_source(_self):
        object.__setattr__(request.documents[0], "text", "substituted")
        return False

    monkeypatch.setattr(
        mod.OfflineIndexResult, "revocation_verified", property(change_source),
    )
    with pytest.raises(mod.OfflineIndexRejected, match="carriers"):
        mod.search_offline_text(request)


def test_injected_result_constructor_class_rejected(monkeypatch):
    class DerivedResult(mod.OfflineIndexResult):
        pass

    monkeypatch.setattr(mod, "OfflineIndexResult", DerivedResult)
    with pytest.raises(mod.OfflineIndexRejected, match="result carrier"):
        mod.search_offline_text(_request())
