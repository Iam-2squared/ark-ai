"""Erasure assessments refuse changed input/output class descriptors.

All inputs are synthetic claims. No case performs deletion or attests
reclaimed WAL, backup erasure, consent, or forensic privacy completion.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from types import SimpleNamespace

import pytest

import ark.privacy_erasure_evidence_review as mod


def _observations():
    return mod.SyntheticErasureObservations(
        "a" * 64, "absent", "none_claimed", "complete_claimed",
        "on_claimed", "none_claimed", 0,
    )


@contextmanager
def _poison(cls, field: str, touched: list[str]):
    original = vars(cls).get(field)
    missing = field not in vars(cls)

    def malicious(*_args, **_kwargs):
        touched.append(field)
        raise AssertionError("reflected erasure class descriptor executed")

    replacement = (
        property(malicious)
        if field in {
            "owner_scope_digest", "row_state", "reader_state",
            "checkpoint_state", "secure_delete_state", "backup_state",
            "wal_bytes_claimed", "evidence_digest", "blockers",
            "logical_absence_claimed",
        } else malicious
    )
    setattr(cls, field, replacement)
    try:
        yield
    finally:
        if missing:
            delattr(cls, field)
        else:
            setattr(cls, field, original)


@pytest.mark.parametrize(
    ("which", "field"),
    (
        ("observation", "owner_scope_digest"),
        ("observation", "row_state"),
        ("observation", "reader_state"),
        ("observation", "checkpoint_state"),
        ("observation", "secure_delete_state"),
        ("observation", "backup_state"),
        ("observation", "wal_bytes_claimed"),
        ("observation", "__init__"),
        ("observation", "__getattribute__"),
        ("observation", "__getattr__"),
        ("assessment", "evidence_digest"),
        ("assessment", "blockers"),
        ("assessment", "logical_absence_claimed"),
        ("assessment", "__init__"),
        ("assessment", "__getattribute__"),
        ("assessment", "__getattr__"),
    ),
)
def test_preinstalled_carrier_refused_before_first_field_access(
    which: str, field: str,
) -> None:
    original = _observations()
    touched: list[str] = []
    cls = (
        mod.SyntheticErasureObservations
        if which == "observation"
        else mod.SyntheticErasureAssessment
    )
    with _poison(cls, field, touched):
        with pytest.raises(mod.SyntheticErasureRejected, match="authority descriptor changed"):
            mod.review_synthetic_erasure_evidence(original)
    assert touched == []


@pytest.mark.parametrize(
    ("which", "field"),
    (
        ("observation", "row_state"),
        ("observation", "__getattribute__"),
        ("assessment", "blockers"),
        ("assessment", "__init__"),
    ),
)
def test_reentrant_digest_cannot_install_counterfeit_carrier(
    monkeypatch: pytest.MonkeyPatch, which: str, field: str,
) -> None:
    source = _observations()
    touched: list[str] = []
    cls = (
        mod.SyntheticErasureObservations
        if which == "observation"
        else mod.SyntheticErasureAssessment
    )
    original_sha256 = mod.hashlib.sha256

    with ExitStack() as stack:
        def reentrant(data: bytes):
            # Leave the mutation installed until the caller's post-digest
            # epoch check; temporary restoration would not exercise it.
            stack.enter_context(_poison(cls, field, touched))
            return original_sha256(data)

        monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
        # The import-original digest fence now refuses the patched hash
        # BEFORE its callback can install a counterfeit descriptor.
        with pytest.raises(
            mod.SyntheticErasureRejected, match="digest implementation changed",
        ):
            mod.review_synthetic_erasure_evidence(source)
    assert touched == []


def test_original_carriers_still_return_explicit_non_authorizing_blockers() -> None:
    result = mod.review_synthetic_erasure_evidence(_observations())
    assert result.logical_absence_claimed is True
    assert result.blockers == (
        "independent_storage_attestation_missing", "forensic_scope_not_attested",
    )
    assert result.cleanup_authorized is False
    assert result.forensic_erasure_verified is False
