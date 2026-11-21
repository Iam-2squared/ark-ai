"""Synthetic private search denies executable result/hit constructor substitution."""

import hashlib
from types import SimpleNamespace

import pytest

import ark.offline_context_search as context


def _fixture():
    private = "local private alpha"
    row = context.OfflineContextSearchRecord(
        "rec_" + "1" * 32, "a" * 64, "b" * 64, private,
        hashlib.sha256(private.encode()).hexdigest(), 2000,
    )
    return (row,)


def _search():
    return context.search_offline_context(
        _fixture(), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,),
        observed_at_ms=1000, query="alpha",
    )


@pytest.mark.parametrize("klass_name", ("OfflineContextSearchPreview", "OfflineContextSearchHit"))
@pytest.mark.parametrize("phase", ("preinstalled", "during_query_utf8"))
def test_private_search_never_invokes_forged_constructor(
    monkeypatch, klass_name, phase,
):
    klass = getattr(context, klass_name)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("called")
        raise AssertionError("untrusted constructor must not run")

    with monkeypatch.context() as patch:
        if phase == "preinstalled":
            patch.setattr(klass, "__init__", forbidden)
        else:
            original = context._utf8

            def mutate_on_query(text):
                result = original(text)
                if text == "alpha":
                    patch.setattr(klass, "__init__", forbidden)
                return result

            patch.setattr(context, "_utf8", mutate_on_query)
        with pytest.raises(
            context.OfflineContextSearchRejected,
            match="result changed|search grammar, budget or codec changed",
        ):
            _search()
    assert invoked == []


def test_post_hash_result_initializer_injection_is_denied(monkeypatch):
    original = hashlib.sha256
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append("called")
        raise AssertionError("forged initializer must not run")

    with monkeypatch.context() as patch:
        def fake_hash(data=b"", *args, **kwargs):
            if type(data) is bytes and data.startswith(context._DOMAIN):
                patch.setattr(context.OfflineContextSearchPreview, "__init__", forbidden)
            return original(data, *args, **kwargs)

        patch.setattr(context, "hashlib", SimpleNamespace(sha256=fake_hash))
        with pytest.raises(
            context.OfflineContextSearchRejected,
            match="result changed|search grammar, budget or codec changed",
        ):
            _search()
    assert invoked == []


def test_original_preview_remains_local_and_denial_only():
    preview = _search()
    assert preview.hits[0].score == 1
    assert preview.consent_verified is False
    assert preview.external_export_authorized is False
    assert preview.tool_dispatch_authorized is False
    assert preview.retention_authorized is False
