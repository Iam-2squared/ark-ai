"""Detached private context checks are non-disclosing and non-authorizing."""

import hashlib
from dataclasses import replace

import pytest

import ark.personal_context_offline_preview as mod

OWNER = "a" * 64
SCOPE = "b" * 64


def fixture(text="秘密のローカル情報", number=1):
    return mod.OfflineContextFixture(
        f"rec_{number:032x}", OWNER, SCOPE, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 2000,
    )


def build(rows):
    return mod.build_offline_context_preview(
        rows, owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,), observed_at_ms=1000,
    )


def verify(receipt, rows, retained):
    return mod.verify_offline_context_preview(
        receipt, rows, owner_digest=OWNER,
        allowed_scope_digests=(SCOPE,), observed_at_ms=1000,
        retained_local_digest=retained,
    )


def test_explicit_synthetic_fixture_roundtrip_is_never_consent():
    rows = (fixture(), fixture("another local fixture", 2))
    original = build(rows)
    assert verify(original, rows, original.local_digest) is None
    assert original.consent_verified is False
    assert original.external_export_authorized is False
    assert original.tool_dispatch_authorized is False
    assert original.retention_authorized is False


@pytest.mark.parametrize("field,bad", [
    ("owner_digest", "f" * 64),
    ("record_ids", ("rec_" + "f" * 32,)),
    ("record_ids", [True]),
    ("canonical_local_json", "{}"),
    ("canonical_local_json", True),
    ("local_digest", "f" * 64),
    ("local_digest", True),
])
def test_dataclass_equality_spoof_does_not_allow_private_payload_drift(
    monkeypatch, field, bad,
):
    rows = (fixture(),)
    original = build(rows)
    forged = replace(original, **{field: bad})
    monkeypatch.setattr(
        mod.OfflineContextPreview, "__eq__", lambda self, other: True,
    )
    with pytest.raises(mod.OfflineContextPreviewRejected, match="mismatch"):
        verify(forged, rows, original.local_digest)


@pytest.mark.parametrize("mutation", ["receipt", "input"])
def test_last_authority_denial_can_never_conceal_mutation(
    monkeypatch, mutation,
):
    row = fixture()
    rows = (row,)
    original = build(rows)

    def late_denial(self):
        if self is original:
            if mutation == "receipt":
                object.__setattr__(self, "canonical_local_json", "{}")
            else:
                object.__setattr__(row, "content", "unreviewed")
        return False

    monkeypatch.setattr(
        mod.OfflineContextPreview, "retention_authorized",
        property(late_denial),
    )
    with pytest.raises(mod.OfflineContextPreviewRejected, match="changed"):
        verify(original, rows, original.local_digest)


def test_no_stale_retained_digest_accepted():
    rows = (fixture(),)
    original = build(rows)
    altered = (fixture("changed"),)
    with pytest.raises(mod.OfflineContextPreviewRejected, match="mismatch"):
        verify(original, altered, original.local_digest)


@pytest.mark.parametrize("retained", [True, "A" * 64, "f" * 64, "bad"])
def test_external_retained_digest_must_be_exact(retained):
    rows = (fixture(),)
    original = build(rows)
    with pytest.raises(mod.OfflineContextPreviewRejected):
        verify(original, rows, retained)


def test_sensitive_content_does_not_appear_in_failure_diagnostics():
    rows = (fixture(),)
    original = build(rows)
    with pytest.raises(mod.OfflineContextPreviewRejected) as error:
        verify(original, rows, "f" * 64)
    assert "秘密のローカル情報" not in str(error.value)
