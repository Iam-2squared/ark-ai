"""Retained private preview verification bounds its fixture input pre-access.

Detached, synthetic data only. These tests do not authenticate consent,
revocation freshness or permission to export context.
"""

from __future__ import annotations

import hashlib

import pytest

import ark.personal_context_offline_preview as preview

_OWNER = "a" * 64
_SCOPE = "b" * 64


def _fixture() -> preview.OfflineContextFixture:
    content = "秘密: synthetic local-only context"
    return preview.OfflineContextFixture(
        "rec_" + "0" * 32, _OWNER, _SCOPE, content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(), 2000,
    )


def _verify(
    receipt: preview.OfflineContextPreview, rows: tuple[object, ...],
) -> None:
    preview.verify_offline_context_preview(
        receipt, rows, owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
        retained_local_digest=receipt.local_digest,
    )


@pytest.mark.parametrize("size", (0, 2, 33, 4096))
def test_mismatched_fixture_batch_denied_before_private_rebuild(
    monkeypatch, size: int,
) -> None:
    row = _fixture()
    receipt = preview.build_offline_context_preview(
        (row,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
    )

    def forbidden_builder(*_args, **_kwargs):
        raise AssertionError("private context builder invoked for invalid batch")

    with monkeypatch.context() as patch:
        patch.setattr(preview, "build_offline_context_preview", forbidden_builder)
        with pytest.raises(
            preview.OfflineContextPreviewRejected,
            match="exact retained context preview required",
        ) as failure:
            _verify(receipt, (row,) * size)
    assert "秘密" not in str(failure.value)


def test_nonexact_fixture_refused_before_private_rebuild(monkeypatch) -> None:
    receipt = preview.build_offline_context_preview(
        (_fixture(),), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
    )

    class CallerObject:
        def __getattr__(self, name: str):
            raise AssertionError(f"unexpected caller-owned field access: {name}")

    with monkeypatch.context() as patch:
        patch.setattr(
            preview, "build_offline_context_preview",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("private preview builder invoked"),
            ),
        )
        with pytest.raises(
            preview.OfflineContextPreviewRejected,
            match="exact retained context preview required",
        ):
            _verify(receipt, (CallerObject(),))


def test_exact_one_record_retained_fixture_still_verifies() -> None:
    row = _fixture()
    receipt = preview.build_offline_context_preview(
        (row,), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
    )
    assert _verify(receipt, (row,)) is None
    assert receipt.external_export_authorized is False
