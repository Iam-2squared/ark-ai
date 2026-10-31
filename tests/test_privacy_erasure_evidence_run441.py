"""Run441: WAL reclamation claims do not imply forensic erasure."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark import privacy_erasure_evidence_review as mod


@pytest.fixture
def claimed():
    return mod.SyntheticErasureObservations(
        "a" * 64, "absent", "none_claimed", "complete_claimed",
        "on_claimed", "none_claimed", 0,
    )


def test_most_optimistic_observation_still_not_proof(claimed):
    result = mod.review_synthetic_erasure_evidence(claimed)
    assert result.logical_absence_claimed
    assert result.blockers == (
        "independent_storage_attestation_missing", "forensic_scope_not_attested",
    )
    assert not any((result.row_deletion_proven, result.wal_reclamation_proven,
                    result.forensic_erasure_verified, result.cleanup_authorized))


@pytest.mark.parametrize("field,value,reason", [
    ("row_state", "present", "row_absence_unestablished"),
    ("row_state", "unknown", "row_absence_unestablished"),
    ("reader_state", "active", "reader_snapshot_may_retain_bytes"),
    ("reader_state", "unknown", "reader_snapshot_may_retain_bytes"),
    ("checkpoint_state", "busy", "wal_checkpoint_not_confirmed"),
    ("checkpoint_state", "not_run", "wal_checkpoint_not_confirmed"),
    ("wal_bytes_claimed", 2048, "wal_bytes_not_confirmed_zero"),
    ("wal_bytes_claimed", None, "wal_bytes_not_confirmed_zero"),
    ("secure_delete_state", "off", "secure_delete_policy_unconfirmed"),
    ("backup_state", "exist", "backup_or_snapshot_exposure_unresolved"),
    ("backup_state", "unknown", "backup_or_snapshot_exposure_unresolved"),
])
def test_incomplete_local_evidence_has_explicit_blocker(claimed, field, value, reason):
    result = mod.review_synthetic_erasure_evidence(replace(claimed, **{field: value}))
    assert reason in result.blockers
    assert not result.forensic_erasure_verified


@pytest.mark.parametrize("field,value", [
    ("owner_scope_digest", "bad"), ("owner_scope_digest", None),
    ("row_state", True), ("reader_state", "verified"),
    ("checkpoint_state", "success"), ("secure_delete_state", "on"),
    ("backup_state", "deleted"), ("wal_bytes_claimed", True),
    ("wal_bytes_claimed", -1), ("wal_bytes_claimed", 2**63),
])
def test_invalid_observations_rejected(claimed, field, value):
    with pytest.raises(mod.SyntheticErasureRejected):
        mod.review_synthetic_erasure_evidence(replace(claimed, **{field: value}))


def test_output_digest_bound_to_all_fields(claimed):
    baseline = mod.review_synthetic_erasure_evidence(claimed)
    for field, value in (
        ("row_state", "present"), ("reader_state", "active"),
        ("checkpoint_state", "busy"), ("secure_delete_state", "off"),
        ("backup_state", "exist"), ("wal_bytes_claimed", 1),
    ):
        changed = mod.review_synthetic_erasure_evidence(replace(claimed, **{field: value}))
        assert changed.evidence_digest != baseline.evidence_digest


def test_mutation_during_digest_is_rejected(claimed, monkeypatch):
    original = mod.hashlib.sha256
    def reentrant(value):
        object.__setattr__(claimed, "reader_state", "active")
        return original(value)
    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.SyntheticErasureRejected, match="changed"):
        mod.review_synthetic_erasure_evidence(claimed)


def test_exact_type_required():
    with pytest.raises(mod.SyntheticErasureRejected):
        mod.review_synthetic_erasure_evidence(object())
