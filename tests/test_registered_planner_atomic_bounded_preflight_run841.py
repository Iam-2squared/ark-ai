"""Registered Planner/atomic triage rejects invalid identities before callbacks.

These are intentionally uninitialized *inert* recovery/store placeholders:
malformed WRITE occurrence ingress must not inspect their fields or touch
SQLite, ToolRegistry.resolve, a ToolBackend or private Planner metadata.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_registered_planner_atomic_triage import (
    RegisteredPlannerAtomicTriageRejected,
    review_registered_planner_atomic_triage,
)
from ark.agency.planner_journal_review import SyntheticPlanRecovery
from ark.agency.registry import ToolRegistry

_STEP_A = "step_" + "a" * 16
_STEP_B = "step_" + "b" * 16
_OCC_A = "occ_" + "a" * 64
_OCC_B = "occ_" + "b" * 64


def _preflight_only(
    bindings: tuple[object, ...],
    *,
    witness: AtomicPreactionWitness | None = None,
) -> None:
    registry = ToolRegistry(())
    called: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        called.append("resolver")
        raise AssertionError("invalid input reached registry resolver")

    registry.resolve = forbidden  # type: ignore[method-assign]
    steps = (
        PlanStep(_STEP_A, ToolCall("mock", "offline.write", "local")),
        PlanStep(_STEP_B, ToolCall("mock", "offline.write", "local")),
    )
    recovered = object.__new__(SyntheticPlanRecovery)
    ledger = object.__new__(DisconnectedAtomicPreactionLedger)
    with pytest.raises(RegisteredPlannerAtomicTriageRejected):
        review_registered_planner_atomic_triage(
            recovered, steps, registry, ledger,
            witness if witness is not None else genesis_atomic_preaction_witness(),
            bindings,  # type: ignore[arg-type]
        )
    assert called == []


@pytest.mark.parametrize(
    "bindings",
    (
        ((_STEP_A, "occ_" + "a" * 200_000),),
        ((_STEP_A, "occ_" + "a" * 63),),
        ((_STEP_A, "occ_" + "g" * 64),),
        (("x" * 300_000, _OCC_A),),
        (("🍀" * 100, _OCC_A),),
        (("\ud800", _OCC_A),),
        ((1, _OCC_A),),
        ((_STEP_A, object()),),
        ((_STEP_A, _OCC_A, "extra"),),
        ((_STEP_A, _OCC_A), (_STEP_B, _OCC_A)),
        ((_STEP_A, _OCC_A), (_STEP_A, _OCC_B)),
    ),
)
def test_unbounded_malformed_or_duplicate_write_occurrences_never_reach_reader(
    bindings: tuple[object, ...],
) -> None:
    _preflight_only(bindings)


class ExplosiveValue:
    def __eq__(self, _other: object) -> bool:
        raise AssertionError("mutated witness equality must not execute")

    def __ne__(self, _other: object) -> bool:
        raise AssertionError("mutated witness inequality must not execute")


@pytest.mark.parametrize("field", ("count", "tip_sha256"))
def test_malformed_retained_witness_rejected_before_reader_without_equality(
    field: str,
) -> None:
    valid = genesis_atomic_preaction_witness()
    object.__setattr__(valid, field, ExplosiveValue())
    _preflight_only(((_STEP_A, _OCC_A),), witness=valid)
