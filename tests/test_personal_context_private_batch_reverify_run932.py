"""Synthetic Personal Context preview: batch privacy is fail-all, never partial.

All records are fabricated strings. An allowlist or receipt is not consent,
authenticated ownership, live Memory evidence, or permission to export.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    OfflineContextPreviewRejected,
    build_offline_context_preview,
    verify_offline_context_preview,
)

_OWNER = "a" * 64
_OTHER_OWNER = "d" * 64
_SCOPE_ONE = "b" * 64
_SCOPE_TWO = "c" * 64
_UNLISTED_SCOPE = "e" * 64
_ALLOWED = (_SCOPE_ONE, _SCOPE_TWO)
_PRIVATE = "SYNTHETIC-NOT-A-REAL-USER-SECRET"


def _fixture(
    number: int, *, owner=_OWNER, scope=_SCOPE_ONE,
    content=_PRIVATE, expires=1000,
) -> OfflineContextFixture:
    return OfflineContextFixture(
        "rec_" + f"{number:032x}",
        owner,
        scope,
        content,
        hashlib.sha256(content.encode("utf-8")).hexdigest(),
        expires,
    )


def _preview(rows, *, now=100):
    return build_offline_context_preview(
        tuple(rows), owner_digest=_OWNER,
        allowed_scope_digests=_ALLOWED, observed_at_ms=now,
    )


def test_two_scope_synthetic_preview_is_deterministic_but_not_consent() -> None:
    rows = (_fixture(1), _fixture(2, scope=_SCOPE_TWO, content="synthetic-second"))
    first = _preview(rows)
    assert first == _preview(rows)
    assert first.record_ids == (rows[0].record_id, rows[1].record_id)
    assert first.owner_digest == _OWNER
    assert _PRIVATE not in repr(first)
    assert "synthetic-second" not in repr(first)
    assert first.consent_verified is False
    assert first.external_export_authorized is False
    assert first.tool_dispatch_authorized is False
    assert first.retention_authorized is False
    assert verify_offline_context_preview(
        first, rows, owner_digest=_OWNER,
        allowed_scope_digests=_ALLOWED, observed_at_ms=100,
        retained_local_digest=first.local_digest,
    ) is None


@pytest.mark.parametrize(
    "problem",
    (
        "owner_drift", "scope_drift", "expires_at_observation",
        "content_sha_mismatch", "duplicate_record_id", "unordered_record_ids",
    ),
)
def test_private_batch_mismatch_never_returns_subset(
    problem: str,
) -> None:
    first = _fixture(1)
    second = _fixture(2, scope=_SCOPE_TWO, content="synthetic-second")
    if problem == "owner_drift":
        second = replace(second, owner_digest=_OTHER_OWNER)
    elif problem == "scope_drift":
        second = replace(second, scope_digest=_UNLISTED_SCOPE)
    elif problem == "expires_at_observation":
        second = replace(second, expires_at_ms=100)
    elif problem == "content_sha_mismatch":
        second = replace(second, content_sha256="f" * 64)
    elif problem == "duplicate_record_id":
        second = replace(second, record_id=first.record_id)
    else:
        first, second = second, first
    with pytest.raises(OfflineContextPreviewRejected) as failure:
        _preview((first, second))
    assert _PRIVATE not in str(failure.value)
    assert "synthetic-second" not in str(failure.value)


@pytest.mark.parametrize(
    "retained_kind",
    ("wrong_digest", "wrong_owner", "expired_at_verify", "wrong_allowed_scopes"),
)
def test_detached_preview_verification_fails_on_retained_context_drift(
    retained_kind: str,
) -> None:
    rows = (_fixture(1), _fixture(2, scope=_SCOPE_TWO, content="synthetic-second"))
    original = _preview(rows)
    digest = original.local_digest
    owner = _OWNER
    now = 100
    scopes = _ALLOWED
    if retained_kind == "wrong_digest":
        digest = "f" * 64
    elif retained_kind == "wrong_owner":
        owner = _OTHER_OWNER
    elif retained_kind == "expired_at_verify":
        now = 1000
    else:
        scopes = (_SCOPE_ONE,)
    with pytest.raises(OfflineContextPreviewRejected) as failure:
        verify_offline_context_preview(
            original, rows, owner_digest=owner,
            allowed_scope_digests=scopes, observed_at_ms=now,
            retained_local_digest=digest,
        )
    assert _PRIVATE not in str(failure.value)
