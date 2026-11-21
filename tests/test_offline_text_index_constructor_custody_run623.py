"""Local lexical search cannot run a substituted result/hit initializer.

Inputs are disconnected synthetic literals; no private records or persistence.
"""

import hashlib

import pytest

import ark.offline_text_index as index


def _request():
    text = "alpha beta"
    document = index.OfflineIndexDocument(
        "doc_" + "1" * 16, "a" * 64, "b" * 64,
        hashlib.sha256(text.encode()).hexdigest(), text,
    )
    return index.OfflineIndexQuery(
        "a" * 64, "b" * 64,
        hashlib.sha256(b"alpha").hexdigest(), "alpha",
        (document,), (document.document_id,),
    )


@pytest.mark.parametrize("target", ("result", "hit"))
@pytest.mark.parametrize("phase", ("preinstalled", "during_tokenization"))
def test_untrusted_constructor_cannot_execute(tmp_path, monkeypatch, target, phase):
    request = _request()
    klass = (
        index.OfflineIndexResult if target == "result"
        else index.OfflineIndexHit
    )
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("attempted")
        raise AssertionError("forged index initializer executed")

    with monkeypatch.context() as patch:
        if phase == "preinstalled":
            patch.setattr(klass, "__init__", forbidden)
        else:
            original = index._tokens

            def replace_on_tokenization(text):
                answer = original(text)
                patch.setattr(klass, "__init__", forbidden)
                return answer

            patch.setattr(index, "_tokens", replace_on_tokenization)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)
    assert invoked == []


def test_result_constructor_replaced_during_digest_is_rejected(monkeypatch):
    request = _request()
    invoked = []
    original = index._digest

    def forbidden(*_args, **_kwargs):
        invoked.append("attempted")
        raise AssertionError("forged result initializer executed")

    with monkeypatch.context() as patch:
        def change(label, fields):
            answer = original(label, fields)
            if label == "result":
                patch.setattr(index.OfflineIndexResult, "__init__", forbidden)
            return answer

        patch.setattr(index, "_digest", change)
        with pytest.raises(index.OfflineIndexRejected, match="authority"):
            index.search_offline_text(request)
    assert invoked == []


def test_unmodified_index_preserves_deterministic_denial_only_output():
    result = index.search_offline_text(_request())
    assert result.hits[0].distinct_matches == 1
    assert result.identity_authenticated is False
    assert result.disclosure_authorized is False
    assert result.revocation_verified is False
    assert "alpha beta" not in repr(result)
