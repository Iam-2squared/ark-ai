"""One local WAL snapshot for multiple registry-bound synthetic WRITEs.

This fixture neither calls tool backends nor upgrades local matching to human
consent, independent custody, effect proof or permission to retry.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_batch_binding_snapshot_review import (
    AtomicBatchBindingSnapshotReview,
    review_registered_atomic_binding_batch_snapshot,
)
from ark.agency.disconnected_atomic_binding_snapshot_review import (
    AtomicBindingSnapshotRejected,
)
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.registry import ToolRegistration, ToolRegistry

_A = "occ_" + "a" * 64
_B = "occ_" + "b" * 64
_C = "occ_" + "c" * 64


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("batch review must remain disconnected")


def _registry(effect: Effect = Effect.WRITE) -> tuple[ToolRegistry, NeverExecute]:
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", effect, "local", backend),
    ))
    return registry, backend


def _call(payload: str) -> ToolCall:
    return ToolCall("writer", "fixture.write", "offline", {"payload": payload})


def test_three_states_from_one_coherent_read_only_snapshot(tmp_path: Path) -> None:
    registry, backend = _registry()
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    first, second, missing = _call("one"), _call("two"), _call("three")
    a = derive_registered_atomic_intent(registry, first, occurrence_id=_A)
    b = derive_registered_atomic_intent(registry, second, occurrence_id=_B)
    tip = store.reserve(a, retained=genesis_atomic_preaction_witness())
    tip = store.reserve(
        AtomicIntentClaim(_B, "bound_" + "f" * 64, b.request_sha256),
        retained=tip,
    )
    before = path.read_bytes()
    review = review_registered_atomic_binding_batch_snapshot(
        store, tip, registry, ((_A, first), (_B, second), (_C, missing)),
    )
    assert type(review) is AtomicBatchBindingSnapshotReview
    assert review.local_states == (
        (_A, "LOCAL_MATCH"), (_B, "LOCAL_CONFLICT"), (_C, "ABSENT"),
    )
    assert review.retained_count == 2
    for name in (
        "tool_dispatch_authorized", "automatic_replay_authorized",
        "external_effect_proven", "independently_authenticated",
    ):
        assert getattr(review, name) is False
    assert review.manual_review_required is True
    assert path.read_bytes() == before
    assert backend.calls == 0


@pytest.mark.parametrize("problem", ("stale", "tampered_audit", "extra_schema"))
def test_stale_or_corrupt_history_is_refused_for_entire_batch(
    tmp_path: Path, problem: str,
) -> None:
    registry, backend = _registry()
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    first = _call("one")
    tip = store.reserve(
        derive_registered_atomic_intent(registry, first, occurrence_id=_A),
        retained=genesis,
    )
    if problem == "tampered_audit":
        with sqlite3.connect(path) as conn:
            conn.execute(
                "UPDATE preaction_audit SET audit_sha256=?", ("0" * 64,),
            )
    elif problem == "extra_schema":
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE TABLE extra_table (id INTEGER)")
    witness = genesis if problem == "stale" else tip
    with pytest.raises(AtomicBindingSnapshotRejected):
        review_registered_atomic_binding_batch_snapshot(
            store, witness, registry, ((_A, first), (_B, _call("two"))),
        )
    assert backend.calls == 0


@pytest.mark.parametrize("problem", ("duplicate", "read", "subclass", "empty"))
def test_invalid_batch_fails_closed_without_dispatch(
    tmp_path: Path, problem: str,
) -> None:
    registry, backend = _registry(
        effect=Effect.READ if problem == "read" else Effect.WRITE,
    )
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    first = _call("one")
    requests = ((_A, first),)
    if problem == "duplicate":
        requests = ((_A, first), (_A, _call("two")))
    elif problem == "subclass":
        requests = ((_A, first),)
        requests = list(requests)
    elif problem == "empty":
        requests = ()
    with pytest.raises(AtomicBindingSnapshotRejected):
        review_registered_atomic_binding_batch_snapshot(
            store, genesis_atomic_preaction_witness(), registry, requests,
        )
    assert backend.calls == 0


def test_bound_request_change_remains_local_conflict(tmp_path: Path) -> None:
    registry, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    original = _call("before")
    tip = store.reserve(
        derive_registered_atomic_intent(registry, original, occurrence_id=_A),
        retained=genesis_atomic_preaction_witness(),
    )
    result = review_registered_atomic_binding_batch_snapshot(
        store, tip, registry, ((_A, _call("after")),),
    )
    assert result.local_states == ((_A, "LOCAL_CONFLICT"),)
    assert result.automatic_replay_authorized is False
    assert backend.calls == 0
