"""Private offline context receipts reject overlong digest and identity ingress."""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

import ark.personal_context_offline_preview as preview
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreviewRejected,
    build_offline_context_preview,
    verify_offline_context_preview,
)

_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "c" * 32
_CONTENT = "private local fixture"
_SHA = hashlib.sha256(_CONTENT.encode("utf-8")).hexdigest()


def _fixture() -> OfflineContextFixture:
    return OfflineContextFixture(_RECORD, _OWNER, _SCOPE, _CONTENT, _SHA, 5000)


def _build(**kwargs: object) -> preview.OfflineContextPreview:
    options = {
        "fixtures": (_fixture(),),
        "owner_digest": _OWNER,
        "allowed_scope_digests": (_SCOPE,),
        "observed_at_ms": 1000,
    }
    options.update(kwargs)
    return build_offline_context_preview(**options)


def test_valid_synthetic_preview_remains_private_and_deny_only() -> None:
    report = _build()
    assert report.record_ids == (_RECORD,)
    assert report.consent_verified is False
    assert report.external_export_authorized is False
    assert report.tool_dispatch_authorized is False
    assert report.retention_authorized is False
    assert verify_offline_context_preview(
        report, (_fixture(),), owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
        retained_local_digest=report.local_digest,
    ) is None


@pytest.mark.parametrize("field", ["owner_digest", "allowed_scope_digests"])
@pytest.mark.parametrize("count", [65, 65536])
def test_overlong_owner_or_allowlist_digest_rejected(field: str, count: int) -> None:
    value = "f" * count
    bad = (value,) if field == "allowed_scope_digests" else value
    with pytest.raises(OfflineContextPreviewRejected):
        _build(**{field: bad})


@pytest.mark.parametrize("field", ["record_id", "content_sha256"])
@pytest.mark.parametrize("count", [65, 65536])
def test_overlong_fixture_label_rejected(field: str, count: int) -> None:
    fixture = replace(_fixture(), **{field: "f" * count})
    with pytest.raises(OfflineContextPreviewRejected):
        _build(fixtures=(fixture,))


@pytest.mark.parametrize(
    "field",
    ["owner_digest", "local_digest", "canonical_local_json", "record_ids"],
)
def test_malformed_retained_receipt_rejected_before_private_rebuild(
    field: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _build()
    bad = ("rec_" + "f" * 65536,) if field == "record_ids" else "f" * 65536
    forged = replace(report, **{field: bad})

    def must_not_rebuild(*args: object, **kwargs: object) -> None:
        pytest.fail("malformed public receipt reached private fixture rebuild")

    with monkeypatch.context() as guard:
        guard.setattr(preview, "build_offline_context_preview", must_not_rebuild)
        with pytest.raises(OfflineContextPreviewRejected):
            verify_offline_context_preview(
                forged, (_fixture(),), owner_digest=_OWNER,
                allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
                retained_local_digest=report.local_digest,
            )


@pytest.mark.parametrize("count", [65, 65536])
def test_overlong_retained_digest_rejected_before_rebuilding(
    count: int, monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = _build()

    def must_not_rebuild(*args: object, **kwargs: object) -> None:
        pytest.fail("invalid digest reached private fixture rebuild")

    with monkeypatch.context() as guard:
        guard.setattr(preview, "build_offline_context_preview", must_not_rebuild)
        with pytest.raises(OfflineContextPreviewRejected):
            verify_offline_context_preview(
                report, (_fixture(),), owner_digest=_OWNER,
                allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
                retained_local_digest="f" * count,
            )


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("canonical_local_json", "f" * 65536),
        ("canonical_local_json", "{} "),
        ("canonical_local_json", "\u005cud800"),
        ("canonical_local_json", "é" * 32769),
        ("record_ids", ("rec_" + "g" * 32,)),
        ("owner_digest", "G" * 64),
        ("local_digest", "G" * 64),
    ],
)
def test_malformed_retained_receipt_never_rebuilds_private_fixtures(
    field: str, invalid: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _build()
    forged = replace(receipt, **{field: invalid})

    def forbidden_private_rebuild(*args: object, **kwargs: object) -> None:
        pytest.fail("malformed receipt reached private context fixtures")

    with monkeypatch.context() as guard:
        guard.setattr(preview, "build_offline_context_preview", forbidden_private_rebuild)
        with pytest.raises(OfflineContextPreviewRejected):
            verify_offline_context_preview(
                forged, (_fixture(),), owner_digest=_OWNER,
                allowed_scope_digests=(_SCOPE,), observed_at_ms=1000,
                retained_local_digest=receipt.local_digest,
            )
