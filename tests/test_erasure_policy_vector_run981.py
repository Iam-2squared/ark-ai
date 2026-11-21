"""Synthetic privacy-erasure review rejects shortened or rebound policy vectors.

The claims are untrusted, and this test performs no deletion, filesystem I/O,
SQLite checkpoint, forensic proof, or authorization.
"""

from __future__ import annotations

import pytest

from ark import privacy_erasure_evidence_review as erasure


def _claim() -> erasure.SyntheticErasureObservations:
    return erasure.SyntheticErasureObservations(
        "a" * 64, "absent", "none_claimed", "complete_claimed",
        "on_claimed", "none_claimed", 0,
    )


@pytest.mark.parametrize("vector", (
    "_AUTHORITY_NAMES", "_OBSERVATION_FIELDS", "_ASSESSMENT_FIELDS",
    "_CARRIER_HOOKS",
))
@pytest.mark.parametrize("mutation", ("empty", "reversed", "equal_rebound"))
def test_erasure_policy_vector_rebind_rejected_before_claim_inspection(
    monkeypatch, vector, mutation,
):
    original = getattr(erasure, vector)
    assert len(original) >= 2
    if mutation == "empty":
        changed = ()
    elif mutation == "reversed":
        changed = tuple(reversed(original))
    else:
        changed = tuple(list(original))
        assert changed == original and changed is not original
    monkeypatch.setattr(erasure, vector, changed)
    with pytest.raises(erasure.SyntheticErasureRejected, match="policy vector changed"):
        erasure.review_synthetic_erasure_evidence(_claim())


def test_shortened_denials_cannot_hide_forged_cleanup_getter(monkeypatch):
    invoked = []

    def forged(self):
        invoked.append(True)
        return False

    monkeypatch.setattr(erasure, "_AUTHORITY_NAMES", ())
    monkeypatch.setattr(
        erasure.SyntheticErasureAssessment, "cleanup_authorized", property(forged),
    )
    with pytest.raises(erasure.SyntheticErasureRejected, match="policy vector changed"):
        erasure.review_synthetic_erasure_evidence(_claim())
    assert invoked == []


def test_shortened_carrier_hook_vector_cannot_invoke_claim_getter(monkeypatch):
    invoked = []

    def forged(self, name):
        invoked.append(name)
        raise AssertionError("unreviewed private erasure claim getter executed")

    monkeypatch.setattr(erasure, "_CARRIER_HOOKS", ())
    monkeypatch.setattr(
        erasure.SyntheticErasureObservations, "__getattribute__", forged,
    )
    with pytest.raises(erasure.SyntheticErasureRejected, match="policy vector changed"):
        erasure.review_synthetic_erasure_evidence(_claim())
    assert invoked == []


def test_original_policy_still_denies_cleanup_and_forensic_certification():
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
