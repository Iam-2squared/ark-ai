"""Offline lexical fixtures deny substituted codec, normalizer and budgets.

Only synthetic local text is used; neither source identity nor a returned hit
is consent, authentication, revocation proof or permission to export.
"""

import hashlib

import pytest

import ark.offline_text_index as index


def _request():
    text = "private alpha fixture"
    doc = index.OfflineIndexDocument(
        "doc_" + "1" * 16, "a" * 64, "b" * 64,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), text,
    )
    query = "alpha"
    return index.OfflineIndexQuery(
        "a" * 64, "b" * 64,
        hashlib.sha256(query.encode("utf-8")).hexdigest(), query,
        (doc,), (doc.document_id,),
    )


@pytest.mark.parametrize(
    "name,substitute",
    [
        ("_WORD", object()),
        ("_SHA", object()),
        ("_DOC", object()),
        ("_DOMAIN", b"unreviewed-domain"),
        ("_MAX_DOCS", 33),
        ("_MAX_QUERY_BYTES", True),
        ("Counter", object()),
        ("hashlib", object()),
        ("json", object()),
        ("unicodedata", object()),
    ],
)
def test_preinstalled_local_codec_substitution_refused_before_private_text(
    monkeypatch, name, substitute,
):
    request = _request()
    with monkeypatch.context() as patch:
        patch.setattr(index, name, substitute)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)


@pytest.mark.parametrize("dependency", ["sha256", "dumps", "normalize"])
def test_dependency_function_replacement_never_receives_private_text(
    monkeypatch, dependency,
):
    request = _request()
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("substituted private text processor ran")

    module = {
        "sha256": index.hashlib,
        "dumps": index.json,
        "normalize": index.unicodedata,
    }[dependency]
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, forbidden)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)
    assert invoked == []


def test_tokenizer_callback_cannot_install_a_late_digest_dependency(monkeypatch):
    request = _request()
    original_tokens = index._tokens
    invoked = []

    def forged_digest(*_args, **_kwargs):
        invoked.append("forbidden")
        raise AssertionError("forged digest ran")

    with monkeypatch.context() as patch:
        def late_change(text):
            tokens = original_tokens(text)
            patch.setattr(index.hashlib, "sha256", forged_digest)
            return tokens

        patch.setattr(index, "_tokens", late_change)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)
    assert invoked == []


def test_original_codec_still_returns_only_denial_metadata():
    result = index.search_offline_text(_request())
    assert len(result.hits) == 1
    assert result.hits[0].distinct_matches == 1
    assert result.identity_authenticated is False
    assert result.disclosure_authorized is False
    assert result.revocation_verified is False
    assert "private alpha fixture" not in repr(result)
