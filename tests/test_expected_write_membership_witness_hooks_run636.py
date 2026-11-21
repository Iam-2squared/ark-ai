"""Detached WRITE membership rejects replaced constructors and field hooks.

Proof remains a caller-retained local hash, never human permission, trusted
clock, a complete external action attestation or authority to replay.
"""

from __future__ import annotations

import pytest

from ark.agency import synthetic_expected_write_membership_review as witness

_TOPOLOGY = "plan_" + "c" * 64
_MEMBERS = ("a", "b")


def _capture():
    return witness.capture_expected_write_membership(_TOPOLOGY, _MEMBERS)


@pytest.mark.parametrize(
    "changed",
    ("constructor", "field", "denial", "lookup_hook"),
)
def test_retained_witness_rejects_replaced_reflection_without_execution(
    monkeypatch, changed,
):
    retained = _capture()
    executions = []

    def forbidden(*_args, **_kwargs):
        executions.append("ran")
        raise AssertionError("untrusted field was invoked")

    klass = witness.SyntheticExpectedWriteMembership
    if changed == "constructor":
        monkeypatch.setattr(klass, "__init__", forbidden)
    elif changed == "field":
        monkeypatch.setattr(klass, "digest", property(forbidden))
    elif changed == "denial":
        monkeypatch.setattr(klass, "dispatch_authorized", property(forbidden))
    else:
        monkeypatch.setattr(klass, "__getattribute__", forbidden)

    with pytest.raises(
        witness.SyntheticExpectedWriteMembershipRejected,
        match="witness constructor or authority changed",
    ):
        witness.assert_expected_write_membership(
            retained, topology_digest=_TOPOLOGY, recovered_step_ids=_MEMBERS,
        )
    assert executions == []


def test_hash_callback_cannot_substitute_constructor_before_capture(
    monkeypatch,
):
    native_digest = witness._digest
    attempts = []

    def forbidden(*_args, **_kwargs):
        attempts.append("constructor")
        raise AssertionError("substituted witness constructor ran")

    def change_on_digest(data):
        monkeypatch.setattr(
            witness.SyntheticExpectedWriteMembership, "__init__", forbidden,
        )
        return native_digest(data)

    monkeypatch.setattr(witness, "_digest", change_on_digest)
    with pytest.raises(
        witness.SyntheticExpectedWriteMembershipRejected,
        match="witness constructor or authority changed",
    ):
        _capture()
    assert attempts == []


def test_original_witness_retains_all_denials():
    retained = _capture()
    witness.assert_expected_write_membership(
        retained, topology_digest=_TOPOLOGY, recovered_step_ids=_MEMBERS,
    )
    assert retained.dispatch_authorized is False
    assert retained.automatic_replay_authorized is False
    assert retained.external_outcome_known is False
