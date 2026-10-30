"""Privacy fixtures reject constructor substitution that forges authority flags."""

from __future__ import annotations

import hashlib

import pytest

import ark.offline_context_membership_guard as membership
import ark.offline_context_redaction as redaction
import ark.personal_context_offline_preview as context

OWNER = "a" * 64
SCOPE = "b" * 64


class ForgedResult:
    """Caller-substituted constructor with legitimate-looking data fields."""

    def __init__(self, keys: tuple[str, ...], values: tuple[object, ...]):
        for key, value in zip(keys, values, strict=True):
            setattr(self, key, value)

    @property
    def consent_verified(self) -> bool:
        return True

    @property
    def external_export_authorized(self) -> bool:
        return True

    @property
    def disclosure_authorized(self) -> bool:
        return True


def fake_type(*names: str):
    class Substitute(ForgedResult):
        def __init__(self, *args):
            super().__init__(names, args)

    return Substitute


def redact():
    return redaction.preview_offline_redaction(
        "abcd",
        owner_digest=OWNER,
        scope_digest=SCOPE,
        retained_source_sha256=hashlib.sha256(b"abcd").hexdigest(),
        spans=(redaction.OfflineRedactionSpan(0, 4, "PII"),),
    )


def admit():
    return membership.review_offline_context_membership(
        (membership.ContextRecordClaim(
            "ctx_" + "0" * 16, OWNER, SCOPE, "c" * 64, 1, 100,
        ),),
        expected_record_ids=("ctx_" + "0" * 16,),
        owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,),
        scope_vetoes=(membership.ContextScopeVetoClaim(SCOPE, False, 1, "d" * 64),),
        observed_at_ms=10,
        max_claim_age_ms=10,
    )


def preview():
    content = "synthetic private fixture"
    return context.build_offline_context_preview(
        (context.OfflineContextFixture(
            "rec_" + "1" * 32, OWNER, SCOPE, content,
            hashlib.sha256(content.encode()).hexdigest(), 100,
        ),),
        owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,),
        observed_at_ms=10,
    )


@pytest.mark.parametrize("fn", (redact, admit, preview))
def test_original_result_types_retain_deny_only_flags(fn):
    result = fn()
    assert result.consent_verified is False
    if hasattr(result, "external_export_authorized"):
        assert result.external_export_authorized is False
    if hasattr(result, "disclosure_authorized"):
        assert result.disclosure_authorized is False


def test_redacted_preview_cannot_return_forged_authorized_result(monkeypatch):
    monkeypatch.setattr(redaction, "RedactedOfflinePreview", fake_type(
        "owner_digest", "scope_digest", "source_sha256", "masked_text",
        "masked_characters", "complete_masking", "local_digest",
    ))
    with pytest.raises(redaction.OfflineRedactionRejected, match="construction mutated"):
        redact()


def test_membership_cannot_return_forged_authorized_result(monkeypatch):
    monkeypatch.setattr(membership, "OfflineContextMembershipReview", fake_type(
        "owner_digest", "record_count", "scope_count", "membership_sha256",
    ))
    with pytest.raises(membership.OfflineContextAdmissionRejected, match="constructed"):
        admit()


def test_local_context_cannot_return_forged_export_result(monkeypatch):
    monkeypatch.setattr(context, "OfflineContextPreview", fake_type(
        "owner_digest", "record_ids", "canonical_local_json", "local_digest",
    ))
    with pytest.raises(context.OfflineContextPreviewRejected, match="constructed"):
        preview()
