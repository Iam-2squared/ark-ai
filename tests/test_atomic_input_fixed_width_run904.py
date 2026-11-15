"""Detached pre-action admission bounds reflected identities before regex.

Inert synthetic values only: no SQLite, approval, clock, backend, action,
external effect, retry or Candidate inference is invoked.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_atomic_input_review import review_atomic_input_carriers
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    genesis_atomic_preaction_witness,
)


def _claim() -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)


def test_canonical_inert_inputs_remain_admitted_without_effect_authority():
    claim = _claim()
    witness = genesis_atomic_preaction_witness()
    assert review_atomic_input_carriers(claim, witness) == (
        claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        witness.count, witness.tip_sha256,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("occurrence_id", "occ_" + "a" * 262_144),
        ("bound_action_id", "bound_" + "b" * 262_144),
        ("request_sha256", "c" * 262_144),
        ("occurrence_id", "occ_" + "a" * 63),
        ("bound_action_id", "bound_" + "b" * 65),
        ("request_sha256", "é" * 64),
    ),
    ids=(
        "huge-occurrence", "huge-bound-id", "huge-request-hash",
        "short-occurrence", "long-bound-id", "multibyte-digest",
    ),
)
def test_reflected_claim_identity_width_rejected(field, value):
    claim = _claim()
    object.__setattr__(claim, field, value)
    with pytest.raises(AtomicPreactionRejected, match="invalid bounded"):
        review_atomic_input_carriers(claim, genesis_atomic_preaction_witness())


def test_reflected_witness_digest_width_rejected():
    claim = _claim()
    witness = genesis_atomic_preaction_witness()
    object.__setattr__(witness, "tip_sha256", "f" * 262_144)
    with pytest.raises(AtomicPreactionRejected, match="invalid bounded"):
        review_atomic_input_carriers(claim, witness)


def test_foreign_string_subclass_refused_without_hash_callback():
    class Hostile(str):
        def __hash__(self):
            raise AssertionError("untrusted hash callback reached")

    claim = _claim()
    object.__setattr__(claim, "occurrence_id", Hostile("occ_" + "a" * 64))
    with pytest.raises(AtomicPreactionRejected, match="invalid bounded"):
        review_atomic_input_carriers(claim, genesis_atomic_preaction_witness())
