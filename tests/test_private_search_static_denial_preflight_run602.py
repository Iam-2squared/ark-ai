"""Search excerpt construction must not execute counterfeit permission getters.

Caller-provided private fixtures remain entirely local: neither a match nor
a digest authenticates consent, revocation, retention or export permission.
"""

import hashlib

import pytest

from ark import offline_context_search as search


class CounterfeitGetter:
    def __init__(self, original, called):
        self.original = original
        self.called = called

    def __get__(self, instance, owner=None):
        self.called.append(True)
        return self.original if instance is None else False


def _request():
    content = "private synthetic alpha"
    row = search.OfflineContextSearchRecord(
        "rec_" + "1" * 32, "a" * 64, "b" * 64,
        content, hashlib.sha256(content.encode()).hexdigest(), 2000,
    )
    return dict(
        fixtures=(row,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,),
        observed_at_ms=1000, query="alpha",
    )


@pytest.mark.parametrize("flag", search._DENIALS)
def test_preinstalled_descriptor_rejected_before_private_hash(
    monkeypatch, flag,
):
    request = _request()
    called = []
    original = vars(search.OfflineContextSearchPreview)[flag]
    monkeypatch.setattr(
        search.OfflineContextSearchPreview,
        flag,
        CounterfeitGetter(original, called),
    )

    def forbidden_hash(*_args, **_kwargs):
        raise AssertionError("private text hashed before denial preflight")

    monkeypatch.setattr(search.hashlib, "sha256", forbidden_hash)
    with pytest.raises(
        search.OfflineContextSearchRejected,
        match="authority descriptor changed",
    ):
        search.search_offline_context(**request)
    assert called == []


@pytest.mark.parametrize("flag", search._DENIALS)
def test_descriptor_installed_during_hash_is_rejected_before_getter(
    monkeypatch, flag,
):
    request = _request()
    called = []
    original = vars(search.OfflineContextSearchPreview)[flag]
    sha256 = search.hashlib.sha256

    def inject(payload=b""):
        monkeypatch.setattr(
            search.OfflineContextSearchPreview,
            flag,
            CounterfeitGetter(original, called),
        )
        return sha256(payload)

    monkeypatch.setattr(search.hashlib, "sha256", inject)
    # The replacement digest cannot run: the codec identity is checked first.
    with pytest.raises(
        search.OfflineContextSearchRejected,
        match="search grammar, budget or codec changed",
    ):
        search.search_offline_context(**request)
    assert called == []


def test_unmodified_search_is_explicitly_non_exporting():
    report = search.search_offline_context(**_request())
    assert report.hits[0].excerpt == "private synthetic alpha"
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False
