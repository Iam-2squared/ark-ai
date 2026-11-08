"""Synthetic erasure diagnostics cannot claim real deletion or gain authority."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.privacy_erasure_evidence_review as erasure


def _observations(*, row="absent"):
    return erasure.SyntheticErasureObservations(
        owner_scope_digest="a" * 64,
        row_state=row,
        reader_state="none_claimed",
        checkpoint_state="complete_claimed",
        secure_delete_state="on_claimed",
        backup_state="none_claimed",
        wal_bytes_claimed=0,
    )


def test_optimistic_caller_claims_never_prove_real_erasure():
    original = _observations()
    report = erasure.review_synthetic_erasure_evidence(original)
    assert report.logical_absence_claimed is True
    assert report.blockers == (
        "independent_storage_attestation_missing",
        "forensic_scope_not_attested",
    )
    assert report.row_deletion_proven is False
    assert report.wal_reclamation_proven is False
    assert report.forensic_erasure_verified is False
    assert report.cleanup_authorized is False
    assert report == erasure.review_synthetic_erasure_evidence(original)


def test_unknown_row_is_never_reported_logically_absent():
    result = erasure.review_synthetic_erasure_evidence(_observations(row="unknown"))
    assert result.logical_absence_claimed is False
    assert "row_absence_unestablished" in result.blockers
    assert result.forensic_erasure_verified is False


@pytest.mark.parametrize("field", (
    "row_deletion_proven", "wal_reclamation_proven",
    "forensic_erasure_verified", "cleanup_authorized",
))
def test_authority_getters_cannot_return_true(monkeypatch, field):
    obs = _observations()
    monkeypatch.setattr(
        erasure.SyntheticErasureAssessment,
        field, property(lambda self: True),
    )
    with pytest.raises(erasure.SyntheticErasureRejected, match="authority"):
        erasure.review_synthetic_erasure_evidence(obs)


@pytest.mark.parametrize("field", (
    "evidence_digest", "blockers", "logical_absence_claimed",
))
def test_false_denial_getter_cannot_rewrite_result(monkeypatch, field):
    obs = _observations()

    def change_result(self):
        if field == "evidence_digest":
            other = (" " + self.evidence_digest)[1:]
            assert other == self.evidence_digest and other is not self.evidence_digest
            object.__setattr__(self, field, other)
        elif field == "blockers":
            cloned = tuple(list(self.blockers))
            assert cloned == self.blockers and cloned is not self.blockers
            object.__setattr__(self, field, cloned)
        else:
            object.__setattr__(self, field, False)
        return False

    monkeypatch.setattr(
        erasure.SyntheticErasureAssessment,
        "cleanup_authorized", property(change_result),
    )
    with pytest.raises(erasure.SyntheticErasureRejected, match="authority"):
        erasure.review_synthetic_erasure_evidence(obs)


def test_false_denial_getter_cannot_replace_original_observation_carrier(monkeypatch):
    obs = _observations()

    def rewrite_observation(self):
        old = obs.row_state
        new = (" " + old)[1:]
        assert new == old and new is not old
        object.__setattr__(obs, "row_state", new)
        return False

    monkeypatch.setattr(
        erasure.SyntheticErasureAssessment,
        "forensic_erasure_verified", property(rewrite_observation),
    )
    # The imported denial descriptor is now rejected BEFORE its callback
    # can mutate the source. This is stronger than the prior late detection.
    with pytest.raises(erasure.SyntheticErasureRejected, match="authority descriptor"):
        erasure.review_synthetic_erasure_evidence(obs)
    assert obs.row_state == "absent"


def test_constructor_cannot_retarget_caller_claims(monkeypatch):
    obs = _observations()
    original = erasure.SyntheticErasureAssessment.__init__

    def mutate(self, *args):
        original(self, *args)
        object.__setattr__(obs, "reader_state", "unknown")

    monkeypatch.setattr(erasure.SyntheticErasureAssessment, "__init__", mutate)
    # Class-level constructor custody rejects a replacement before its body
    # can modify the caller's originally supplied synthetic claims.
    with pytest.raises(erasure.SyntheticErasureRejected, match="authority descriptor changed"):
        erasure.review_synthetic_erasure_evidence(obs)
    assert obs.reader_state == "none_claimed"


@pytest.mark.parametrize("change", (
    {"owner_scope_digest": "not-a-sha"},
    {"wal_bytes_claimed": True},
    {"row_state": "deleted"},
    {"backup_state": "safe"},
))
def test_untrusted_malformed_claims_are_rejected(change):
    observations = replace(_observations(), **change)
    with pytest.raises(erasure.SyntheticErasureRejected, match="malformed"):
        erasure.review_synthetic_erasure_evidence(observations)


def test_erasure_diagnostic_only_accepts_exact_observation_type():
    with pytest.raises(erasure.SyntheticErasureRejected, match="exact"):
        erasure.review_synthetic_erasure_evidence(object())
