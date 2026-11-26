"""Privacy erasure claims reject oversized or callback-bearing carriers early.

Caller claims are not erasure evidence. No file is opened, cleaned, checkpointed,
or probed by this offline-only module.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import privacy_erasure_evidence_review as erasure


def _claim() -> erasure.SyntheticErasureObservations:
    return erasure.SyntheticErasureObservations(
        "a" * 64,
        "absent",
        "none_claimed",
        "complete_claimed",
        "on_claimed",
        "none_claimed",
        0,
    )


@pytest.mark.parametrize(
    "field",
    (
        "owner_scope_digest",
        "row_state",
        "reader_state",
        "checkpoint_state",
        "secure_delete_state",
        "backup_state",
    ),
)
def test_oversize_private_evidence_carrier_rejected(field: str) -> None:
    claim = replace(_claim(), **{field: "a" * 100_000})
    with pytest.raises(erasure.SyntheticErasureRejected, match="malformed"):
        erasure.review_synthetic_erasure_evidence(claim)


@pytest.mark.parametrize(
    "field",
    (
        "owner_scope_digest",
        "row_state",
        "reader_state",
        "checkpoint_state",
        "secure_delete_state",
        "backup_state",
    ),
)
def test_foreign_string_hash_and_equality_hooks_not_executed(field: str) -> None:
    class UntrustedText(str):
        def __hash__(self):
            pytest.fail("foreign erasure claim __hash__ executed")

        def __eq__(self, other):
            pytest.fail("foreign erasure claim __eq__ executed")

    claim = replace(_claim(), **{field: UntrustedText("absent")})
    with pytest.raises(erasure.SyntheticErasureRejected, match="malformed"):
        erasure.review_synthetic_erasure_evidence(claim)


def test_valid_synthetic_claim_does_not_authorize_forensic_cleanup() -> None:
    result = erasure.review_synthetic_erasure_evidence(_claim())
    assert result.logical_absence_claimed is True
    assert result.blockers == (
        "independent_storage_attestation_missing",
        "forensic_scope_not_attested",
    )
    assert result.row_deletion_proven is False
    assert result.wal_reclamation_proven is False
    assert result.forensic_erasure_verified is False
    assert result.cleanup_authorized is False
