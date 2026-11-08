"""Synthetic approval claims reject substituted digest machinery before use.

Only process-local diagnostic identities are checked. These tests do not
authenticate a human approval, grant authority, or call a tool backend.
"""

from __future__ import annotations

import pytest

from ark.agency import synthetic_approval_claim_review as claim


@pytest.mark.parametrize("dependency", ["hashlib", "json"])
@pytest.mark.parametrize("entry", ["make", "review"])
def test_replaced_digest_dependency_rejected_before_claim_data_access(
    monkeypatch, dependency, entry,
):
    calls = []

    def poison(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("untrusted digest function was invoked")

    with monkeypatch.context() as patch:
        if dependency == "hashlib":
            patch.setattr(claim.hashlib, "sha256", poison)
        else:
            patch.setattr(claim.json, "dumps", poison)

        with pytest.raises(
            claim.SyntheticApprovalRejected, match="carrier changed",
        ):
            if entry == "make":
                claim.make_synthetic_approval_claim(
                    object(), object(),
                    issuer_digest="0" * 64,
                    subject_digest="1" * 64,
                    purpose_digest="2" * 64,
                    recipient_digest="3" * 64,
                    nonce_digest="4" * 64,
                    issued_at_ms=1,
                    expires_at_ms=2,
                )
            else:
                claim.review_synthetic_approval_claim(
                    object(), object(), object(),
                    issuer_digest="0" * 64,
                    subject_digest="1" * 64,
                    purpose_digest="2" * 64,
                    recipient_digest="3" * 64,
                    now_ms=1,
                    cancelled_ids=frozenset(),
                )
    assert calls == []


def test_original_synthetic_claim_digest_remains_inert():
    claim._require_original_claim_carriers()
    digest = claim._identity(("example", "fixture"))
    assert digest.startswith("approval_")
    assert len(digest) == len("approval_") + 64
    claim._require_original_claim_carriers()
