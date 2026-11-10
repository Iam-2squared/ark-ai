"""Import-original atomic input preflight has no storage or dispatch rights."""

from __future__ import annotations

import pytest

from ark.agency.disconnected_atomic_input_review import (
    review_atomic_input_carriers,
)
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    genesis_atomic_preaction_witness,
)


def _inputs() -> tuple[AtomicIntentClaim, AtomicPreactionWitness]:
    return (
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64),
        genesis_atomic_preaction_witness(),
    )


def test_exact_input_preflight_is_value_only_without_rights() -> None:
    claim, witness = _inputs()
    fields = review_atomic_input_carriers(claim, witness)
    assert fields == (
        claim.occurrence_id, claim.bound_action_id,
        claim.request_sha256, witness.count, witness.tip_sha256,
    )
    assert type(fields) is tuple
    assert not hasattr(fields, "execute")
    assert not hasattr(fields, "permission_granted")


@pytest.mark.parametrize(("field", "value"), [
    ("occurrence_id", "bad"),
    ("bound_action_id", "bound_" + "x" * 64),
    ("request_sha256", "C" * 64),
    ("count", True),
    ("count", -1),
    ("count", 129),
    ("tip_sha256", "bad"),
])
def test_reflectively_mutated_input_value_rejected(
    field: str, value: object,
) -> None:
    claim, witness = _inputs()
    target = witness if field in ("count", "tip_sha256") else claim
    object.__setattr__(target, field, value)
    with pytest.raises(AtomicPreactionRejected):
        review_atomic_input_carriers(claim, witness)


@pytest.mark.parametrize(("kind", "name"), [
    ("claim", "occurrence_id"),
    ("claim", "bound_action_id"),
    ("claim", "__getattribute__"),
    ("witness", "count"),
    ("witness", "tip_sha256"),
    ("witness", "__getattribute__"),
])
def test_rebound_input_descriptor_does_not_execute(
    kind: str, name: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    claim, witness = _inputs()
    called = []

    def forbidden(*_args: object) -> object:
        called.append(True)
        raise AssertionError("replaced input descriptor was invoked")

    cls = AtomicIntentClaim if kind == "claim" else AtomicPreactionWitness
    with monkeypatch.context() as patch:
        patch.setattr(
            cls, name,
            forbidden if name.startswith("__") else property(forbidden),
        )
        with pytest.raises(
            AtomicPreactionRejected, match="carrier definition changed",
        ):
            review_atomic_input_carriers(claim, witness)
    assert called == []


@pytest.mark.parametrize("which", ["claim", "witness"])
def test_subclass_carrier_refused(which: str) -> None:
    claim, witness = _inputs()
    if which == "claim":
        class SubClaim(AtomicIntentClaim):
            pass

        claim = SubClaim(*(
            claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        ))
    else:
        class SubWitness(AtomicPreactionWitness):
            pass

        witness = SubWitness(witness.count, witness.tip_sha256)
    with pytest.raises(AtomicPreactionRejected, match="exact atomic"):
        review_atomic_input_carriers(claim, witness)
