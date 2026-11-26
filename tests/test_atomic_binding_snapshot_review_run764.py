"""Synthetic exact-row recovery is read-only and never grants a WRITE."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_binding_snapshot_review import (
    AtomicBindingSnapshotRejected,
    review_registered_atomic_binding_snapshot,
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

_OCC = "occ_" + "a" * 64
_OTHER = "occ_" + "b" * 64


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("read-only inspection must not dispatch")


def _registry(
    *, name: str = "writer", effect: Effect = Effect.WRITE,
    payload: str = "v",
) -> tuple[ToolRegistry, ToolCall, NeverExecute]:
    backend = NeverExecute()
    call = ToolCall(name, "fixture.write", "offline", {"k": payload})
    registry = ToolRegistry((
        ToolRegistration(name, "fixture.write", effect, "local", backend),
    ))
    return registry, call, backend


def _inspect(store, witness, registry, call, occurrence=_OCC):
    return review_registered_atomic_binding_snapshot(
        store, witness, registry, call, occurrence_id=occurrence,
    )


@pytest.mark.parametrize("present", [False, True])
def test_local_match_or_absence_never_authorizes(
    tmp_path: Path, present: bool,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    witness = genesis_atomic_preaction_witness()
    if present:
        witness = store.reserve(
            derive_registered_atomic_intent(
                registry, call, occurrence_id=_OCC,
            ), retained=witness,
        )
    result = _inspect(store, witness, registry, call)
    assert result.local_state == ("LOCAL_MATCH" if present else "ABSENT")
    assert result.local_binding_matches is present
    assert result.occurrence_id == _OCC
    assert result.retained_count == int(present)
    assert result.manual_review_required is True
    for name in (
        "binding_proven", "tool_dispatch_authorized",
        "automatic_replay_authorized", "external_effect_proven",
        "independent_custody_proven",
    ):
        assert getattr(result, name) is False
    assert not hasattr(result, "execute")
    assert backend.calls == 0


@pytest.mark.parametrize("conflict", ["registry", "request", "tool"])
def test_same_occurrence_mismatched_binding_stays_quarantined(
    tmp_path: Path, conflict: str,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    original = derive_registered_atomic_intent(
        registry, call, occurrence_id=_OCC,
    )
    if conflict == "registry":
        stored = AtomicIntentClaim(
            original.occurrence_id, "bound_" + "f" * 64,
            original.request_sha256,
        )
    elif conflict == "request":
        stored = AtomicIntentClaim(
            original.occurrence_id, original.bound_action_id, "f" * 64,
        )
    else:
        other_registry, other_call, other_backend = _registry(name="other")
        stored = derive_registered_atomic_intent(
            other_registry, other_call, occurrence_id=_OCC,
        )
        assert other_backend.calls == 0
    witness = store.reserve(stored, retained=genesis_atomic_preaction_witness())
    result = _inspect(store, witness, registry, call)
    assert result.local_state == "LOCAL_CONFLICT"
    assert result.local_binding_matches is False
    assert result.binding_proven is False
    assert result.tool_dispatch_authorized is False
    assert result.manual_review_required is True
    assert backend.calls == 0


def test_retained_epoch_stale_refused_not_best_effort(tmp_path: Path) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    genesis = genesis_atomic_preaction_witness()
    store.reserve(
        derive_registered_atomic_intent(registry, call, occurrence_id=_OCC),
        retained=genesis,
    )
    with pytest.raises(AtomicBindingSnapshotRejected):
        _inspect(store, genesis, registry, call)
    assert backend.calls == 0


def test_read_registration_refused_before_storage_inspection(
    tmp_path: Path,
) -> None:
    registry, call, backend = _registry(effect=Effect.READ)
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    with pytest.raises(AtomicBindingSnapshotRejected):
        _inspect(store, genesis_atomic_preaction_witness(), registry, call)
    assert backend.calls == 0


def test_tampered_claim_row_rejected_by_full_chain_scan(tmp_path: Path) -> None:
    registry, call, backend = _registry()
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    witness = store.reserve(
        derive_registered_atomic_intent(registry, call, occurrence_id=_OCC),
        retained=genesis_atomic_preaction_witness(),
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE intents SET request_sha256=? WHERE occurrence_id=?",
            ("f" * 64, _OCC),
        )
    with pytest.raises(AtomicBindingSnapshotRejected):
        _inspect(store, witness, registry, call)
    assert backend.calls == 0


@pytest.mark.parametrize("component", ["scan", "open"])
def test_replaced_storage_reader_cannot_run(
    tmp_path: Path, component: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, call, backend = _registry()
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    invoked = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        invoked.append(True)
        raise AssertionError("replaced reader executed")

    with monkeypatch.context() as patch:
        if component == "scan":
            patch.setattr(atomic_module, "_scan", forbidden)
        else:
            patch.setattr(DisconnectedAtomicPreactionLedger, "_open", forbidden)
        with pytest.raises(
            AtomicBindingSnapshotRejected,
            match="reader definition changed",
        ):
            _inspect(store, genesis_atomic_preaction_witness(), registry, call)
    assert invoked == []
    assert backend.calls == 0


def test_retained_tip_checks_all_rows_not_just_target(tmp_path: Path) -> None:
    registry, call, backend = _registry()
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    witness = store.reserve(
        derive_registered_atomic_intent(registry, call, occurrence_id=_OCC),
        retained=genesis_atomic_preaction_witness(),
    )
    witness = store.reserve(
        derive_registered_atomic_intent(
            registry, call, occurrence_id=_OTHER,
        ), retained=witness,
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE preaction_audit SET audit_sha256=? WHERE occurrence_id=?",
            ("0" * 64, _OTHER),
        )
    with pytest.raises(AtomicBindingSnapshotRejected):
        _inspect(store, witness, registry, call)
    assert backend.calls == 0


def test_corrupt_sqlite_schema_refused(tmp_path: Path) -> None:
    registry, call, backend = _registry()
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unexpected (id INTEGER PRIMARY KEY)")
    with pytest.raises(AtomicBindingSnapshotRejected):
        _inspect(store, genesis_atomic_preaction_witness(), registry, call)
    assert backend.calls == 0
