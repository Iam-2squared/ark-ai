"""Detached plan membership cannot be inferred from the bundle it checks.

All cases are isolated metadata fixtures. No SQLite, backend or permissions.
"""

from dataclasses import FrozenInstanceError

import pytest

import ark.agency.synthetic_expected_write_membership_review as membership

_TOPOLOGY = "plan_" + "a" * 64


def _expected():
    return membership.capture_expected_write_membership(
        _TOPOLOGY, ("first", "last"),
    )


def test_original_independently_retained_membership_has_no_authority():
    retained = _expected()
    membership.assert_expected_write_membership(
        retained, topology_digest=_TOPOLOGY,
        recovered_step_ids=("first", "last"),
    )
    assert retained.digest.startswith("expectedwrites_")
    assert not retained.dispatch_authorized
    assert not retained.automatic_replay_authorized
    assert not retained.external_outcome_known
    with pytest.raises(FrozenInstanceError):
        retained.digest = "forged"


@pytest.mark.parametrize("steps", (
    ("first",), ("last",), ("first", "last", "third"),
    ("last", "first"), ("first", "first"),
))
def test_missing_extra_reordered_or_duplicated_archive_is_rejected(steps):
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.assert_expected_write_membership(
            _expected(), topology_digest=_TOPOLOGY, recovered_step_ids=steps,
        )


def test_same_membership_different_topology_is_rejected():
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.assert_expected_write_membership(
            _expected(), topology_digest="plan_" + "b" * 64,
            recovered_step_ids=("first", "last"),
        )


@pytest.mark.parametrize("steps", (
    (), ("first", "first"), ("last", "first"),
    ("",), ("unbounded" * 40,), ("bad\ud800",),
    ("step",) * 129,
), ids=("empty", "duplicate", "unsorted", "blank", "overlong", "surrogate", "too-many"))
def test_invalid_original_membership_is_rejected(steps):
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.capture_expected_write_membership(_TOPOLOGY, steps)


@pytest.mark.parametrize("bad", (None, True, "first", ["first", "last"]))
def test_non_tuple_archive_carriers_fail_closed(bad):
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.assert_expected_write_membership(
            _expected(), topology_digest=_TOPOLOGY, recovered_step_ids=bad,
        )


def test_retained_membership_with_locally_recomputed_digest_is_not_independent():
    # A locally self-rehashed omitted list could be structurally well-formed,
    # but cannot match the independently held complete list.
    corrupted = membership.capture_expected_write_membership(
        _TOPOLOGY, ("first",),
    )
    membership.assert_expected_write_membership(
        corrupted, topology_digest=_TOPOLOGY, recovered_step_ids=("first",),
    )
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.assert_expected_write_membership(
            _expected(), topology_digest=_TOPOLOGY, recovered_step_ids=("first",),
        )


def test_tampered_digest_rejected_even_when_membership_matches():
    witness = _expected()
    object.__setattr__(witness, "digest", "expectedwrites_" + "0" * 64)
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.assert_expected_write_membership(
            witness, topology_digest=_TOPOLOGY,
            recovered_step_ids=("first", "last"),
        )


def test_reflective_witness_swap_during_hash_is_rejected(monkeypatch):
    witness = _expected()
    old = membership._digest

    def mutate(data):
        object.__setattr__(witness, "step_ids", tuple(["first", "last"]))
        return old(data)

    monkeypatch.setattr(membership, "_digest", mutate)
    with pytest.raises(membership.SyntheticExpectedWriteMembershipRejected):
        membership.assert_expected_write_membership(
            witness, topology_digest=_TOPOLOGY,
            recovered_step_ids=("first", "last"),
        )
