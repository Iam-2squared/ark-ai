"""Original erasure getters cannot replace a later authority descriptor.

No report in this synthetic review proves real deletion or authorizes cleanup.
"""

import pytest

import ark.privacy_erasure_evidence_review as erasure


def _observations():
    return erasure.SyntheticErasureObservations(
        "a" * 64, "absent", "none_claimed",
        "complete_claimed", "on_claimed", "none_claimed", 0,
    )


@pytest.mark.parametrize("source,target", (
    ("row_deletion_proven", "wal_reclamation_proven"),
    ("wal_reclamation_proven", "forensic_erasure_verified"),
    ("forensic_erasure_verified", "cleanup_authorized"),
    ("cleanup_authorized", "row_deletion_proven"),
))
def test_last_original_getter_cannot_invoke_substituted_denial(
    monkeypatch, source, target,
):
    touched = []
    original = erasure.SyntheticErasureAssessment.__getattribute__

    def counterfeit(_result):
        touched.append("unreviewed getter invoked")
        return False

    with monkeypatch.context() as patch:
        def injected_getattribute(self, name):
            value = original(self, name)
            if name == source:
                patch.setattr(
                    erasure.SyntheticErasureAssessment,
                    target,
                    property(counterfeit),
                )
            return value

        patch.setattr(
            erasure.SyntheticErasureAssessment, "__getattribute__",
            injected_getattribute,
        )
        with pytest.raises(erasure.SyntheticErasureRejected, match="descriptor"):
            erasure.review_synthetic_erasure_evidence(_observations())
    assert touched == []


def test_original_denial_getter_cannot_mutate_observation_before_next_getter(
    monkeypatch,
):
    observations = _observations()
    original = erasure.SyntheticErasureAssessment.__getattribute__
    touched = []

    def counterfeit(_result):
        touched.append("later getter")
        return False

    with monkeypatch.context() as patch:
        def injected_getattribute(self, name):
            value = original(self, name)
            if name == "row_deletion_proven":
                object.__setattr__(observations, "row_state", "unknown")
                patch.setattr(
                    erasure.SyntheticErasureAssessment,
                    "wal_reclamation_proven",
                    property(counterfeit),
                )
            return value

        patch.setattr(
            erasure.SyntheticErasureAssessment, "__getattribute__",
            injected_getattribute,
        )
        with pytest.raises(erasure.SyntheticErasureRejected):
            erasure.review_synthetic_erasure_evidence(observations)
    assert touched == []


def test_unchanged_erasure_report_remains_deny_only():
    result = erasure.review_synthetic_erasure_evidence(_observations())
    assert result.logical_absence_claimed is True
    assert result.blockers == (
        "independent_storage_attestation_missing",
        "forensic_scope_not_attested",
    )
    for name in erasure._AUTHORITY_NAMES:
        assert getattr(result, name) is False
