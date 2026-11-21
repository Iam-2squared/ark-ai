"""Privacy erasure review's codec and vocabulary are input custody boundaries.

No evidence here proves physical deletion, live authorization or storage
provenance; the tests only process caller-supplied synthetic claims.
"""

from __future__ import annotations

import re

import pytest

from ark import privacy_erasure_evidence_review as erasure


def _claims():
    return erasure.SyntheticErasureObservations(
        "a" * 64, "absent", "none_claimed", "complete_claimed",
        "on_claimed", "none_claimed", 0,
    )


@pytest.mark.parametrize(
    "dependency",
    (
        "sha256", "dumps", "hex", "domain",
        "row", "readers", "checkpoint", "secure_delete", "backups",
    ),
)
def test_replaced_codec_domain_or_vocabulary_denied_before_digest(
    monkeypatch, dependency,
):
    callbacks = []

    def poison(*args, **kwargs):
        callbacks.append((args, kwargs))
        raise AssertionError("unreviewed erasure callback executed")

    if dependency == "sha256":
        monkeypatch.setattr(erasure.hashlib, "sha256", poison)
    elif dependency == "dumps":
        monkeypatch.setattr(erasure.json, "dumps", poison)
    elif dependency == "hex":
        monkeypatch.setattr(erasure, "_HEX", re.compile(r".*\\Z"))
    elif dependency == "domain":
        copy = bytes(bytearray(erasure._DOMAIN))
        assert copy == erasure._DOMAIN and copy is not erasure._DOMAIN
        monkeypatch.setattr(erasure, "_DOMAIN", copy)
    else:
        name = {
            "row": "_ROW", "readers": "_READERS",
            "checkpoint": "_CHECKPOINT", "secure_delete": "_SECURE_DELETE",
            "backups": "_BACKUPS",
        }[dependency]
        original = getattr(erasure, name)
        copied = frozenset(list(original))
        assert copied == original and copied is not original
        monkeypatch.setattr(erasure, name, copied)

    with pytest.raises(
        erasure.SyntheticErasureRejected,
        match="digest implementation changed",
    ):
        erasure.review_synthetic_erasure_evidence(_claims())
    assert callbacks == []


def test_original_erasure_evidence_is_still_only_a_non_authorizing_claim():
    review = erasure.review_synthetic_erasure_evidence(_claims())
    assert review.logical_absence_claimed is True
    assert review.blockers == (
        "independent_storage_attestation_missing",
        "forensic_scope_not_attested",
    )
    assert review.row_deletion_proven is False
    assert review.wal_reclamation_proven is False
    assert review.forensic_erasure_verified is False
    assert review.cleanup_authorized is False
