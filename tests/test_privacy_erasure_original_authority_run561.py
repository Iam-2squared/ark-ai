"""Import-original erasure authority is required before synthetic evidence hashing.

No tests or reviews establish real erasure, consent, or cleanup authority.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark import privacy_erasure_evidence_review as mod


def observations():
    return mod.SyntheticErasureObservations(
        "a" * 64, "absent", "none_claimed", "complete_claimed",
        "on_claimed", "none_claimed", 0,
    )


@pytest.mark.parametrize("name", (
    "row_deletion_proven", "wal_reclamation_proven",
    "forensic_erasure_verified", "cleanup_authorized",
))
def test_preinstalled_false_descriptor_rejected_before_callback(monkeypatch, name):
    seen = []

    def fake_denial(_result):
        seen.append(name)
        return False

    monkeypatch.setattr(
        mod.SyntheticErasureAssessment, name, property(fake_denial),
    )
    with pytest.raises(mod.SyntheticErasureRejected, match="authority descriptor"):
        mod.review_synthetic_erasure_evidence(observations())
    assert seen == []


def test_hash_callback_cannot_install_false_descriptor(monkeypatch):
    original = mod.hashlib.sha256
    seen = []

    def reentrant(data):
        monkeypatch.setattr(
            mod.SyntheticErasureAssessment, "cleanup_authorized",
            property(lambda _result: seen.append("invoked") or False),
        )
        return original(data)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    # Refuse the substituted digest BEFORE it can alter a denial descriptor.
    with pytest.raises(mod.SyntheticErasureRejected, match="digest implementation changed"):
        mod.review_synthetic_erasure_evidence(observations())
    assert seen == []


def test_untouched_erasure_assessment_remains_deny_only():
    result = mod.review_synthetic_erasure_evidence(observations())
    assert result.logical_absence_claimed is True
    assert result.blockers == (
        "independent_storage_attestation_missing",
        "forensic_scope_not_attested",
    )
    assert result.row_deletion_proven is False
    assert result.wal_reclamation_proven is False
    assert result.forensic_erasure_verified is False
    assert result.cleanup_authorized is False
