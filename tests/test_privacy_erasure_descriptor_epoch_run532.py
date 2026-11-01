"""Offline erasure assessment cannot gain an earlier authority descriptor."""

from __future__ import annotations

import pytest

import ark.privacy_erasure_evidence_review as mod


def _review():
    return mod.review_synthetic_erasure_evidence(
        mod.SyntheticErasureObservations(
            "a" * 64, "absent", "none_claimed", "complete_claimed",
            "on_claimed", "none_claimed", 0,
        ),
    )


def test_erasure_diagnostic_has_no_cleanup_or_forensic_authority():
    result = _review()
    assert result.logical_absence_claimed is True
    assert result.row_deletion_proven is False
    assert result.wal_reclamation_proven is False
    assert result.forensic_erasure_verified is False
    assert result.cleanup_authorized is False
    assert "independent_storage_attestation_missing" in result.blockers
    assert "forensic_scope_not_attested" in result.blockers


@pytest.mark.parametrize("prior", (
    "row_deletion_proven", "wal_reclamation_proven",
    "forensic_erasure_verified",
))
def test_false_final_getter_cannot_replace_earlier_authority_descriptor(
    monkeypatch, prior,
):
    def rewrite_and_deny(_assessment):
        monkeypatch.setattr(
            mod.SyntheticErasureAssessment, prior,
            property(lambda record: True),
        )
        return False

    monkeypatch.setattr(
        mod.SyntheticErasureAssessment, "cleanup_authorized",
        property(rewrite_and_deny),
    )
    with pytest.raises(mod.SyntheticErasureRejected, match="authority"):
        _review()


def test_false_first_getter_cannot_replace_cleanup_descriptor(monkeypatch):
    def rewrite_and_deny(_assessment):
        monkeypatch.setattr(
            mod.SyntheticErasureAssessment, "cleanup_authorized",
            property(lambda record: True),
        )
        return False

    monkeypatch.setattr(
        mod.SyntheticErasureAssessment, "row_deletion_proven",
        property(rewrite_and_deny),
    )
    with pytest.raises(mod.SyntheticErasureRejected, match="authority"):
        _review()


def test_last_getter_cannot_replace_earlier_false_descriptor_with_new_false(
    monkeypatch,
):
    def rewrite_and_deny(_assessment):
        monkeypatch.setattr(
            mod.SyntheticErasureAssessment, "row_deletion_proven",
            property(lambda record: False),
        )
        return False

    monkeypatch.setattr(
        mod.SyntheticErasureAssessment, "cleanup_authorized",
        property(rewrite_and_deny),
    )
    with pytest.raises(mod.SyntheticErasureRejected, match="authority"):
        _review()
