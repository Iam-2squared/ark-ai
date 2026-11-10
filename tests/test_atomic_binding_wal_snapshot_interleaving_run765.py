"""Concurrent WAL writes must not create a mixed local binding read epoch.

Disposable synthetic fixtures only; local equality is never action consent.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as ledger_module
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

_TARGET = "occ_" + "a" * 64
_OTHER = "occ_" + "b" * 64


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("read-only inspection cannot dispatch")


@pytest.mark.parametrize(
    ("initial_target", "concurrent", "old_state", "new_state"),
    [
        (False, "matching", "ABSENT", "LOCAL_MATCH"),
        (False, "conflicting", "ABSENT", "LOCAL_CONFLICT"),
        (False, "unrelated", "ABSENT", "ABSENT"),
        (True, "unrelated", "LOCAL_MATCH", "LOCAL_MATCH"),
    ],
)
def test_reader_never_joins_two_wal_epochs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    initial_target: bool,
    concurrent: str,
    old_state: str,
    new_state: str,
) -> None:
    backend = _NeverExecute()
    call = ToolCall("writer", "fixture.write", "offline", {"k": "v"})
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
    ))
    path = tmp_path / "atomic-snapshot.sqlite"
    reader = DisconnectedAtomicPreactionLedger.create(path)
    writer = DisconnectedAtomicPreactionLedger(path)
    target = derive_registered_atomic_intent(
        registry, call, occurrence_id=_TARGET,
    )
    retained = genesis_atomic_preaction_witness()
    if initial_target:
        retained = reader.reserve(target, retained=retained)
    if concurrent == "matching":
        concurrent_claim = target
    elif concurrent == "conflicting":
        concurrent_claim = AtomicIntentClaim(
            _TARGET, target.bound_action_id, "f" * 64,
        )
    else:
        concurrent_claim = derive_registered_atomic_intent(
            registry, call, occurrence_id=_OTHER,
        )

    original_schema = ledger_module._schema
    fired = False
    next_witness = None

    def inject_at_first_scan(conn) -> None:
        nonlocal fired, next_witness
        if not fired:
            fired = True
            # First SQL read following BEGIN pins the reader's WAL snapshot.
            old_count = conn.execute(
                "SELECT COUNT(*) FROM intents"
            ).fetchone()[0]
            assert old_count == retained.count
            # Commit on an independent connection while reader BEGIN is active.
            # The guard prevents recursion through writer.reserve's _scan.
            next_witness = writer.reserve(concurrent_claim, retained=retained)
        original_schema(conn)

    with monkeypatch.context() as patch:
        patch.setattr(ledger_module, "_schema", inject_at_first_scan)
        old = review_registered_atomic_binding_snapshot(
            reader, retained, registry, call, occurrence_id=_TARGET,
        )
    assert fired is True
    assert next_witness is not None
    assert old.local_state == old_state
    assert old.retained_count == retained.count
    assert old.tool_dispatch_authorized is False
    assert old.automatic_replay_authorized is False
    assert old.manual_review_required is True

    # A later inspection of the advanced epoch must use its new witness.
    with pytest.raises(AtomicBindingSnapshotRejected):
        review_registered_atomic_binding_snapshot(
            reader, retained, registry, call, occurrence_id=_TARGET,
        )
    newer = review_registered_atomic_binding_snapshot(
        reader, next_witness, registry, call, occurrence_id=_TARGET,
    )
    assert newer.local_state == new_state
    assert newer.retained_count == retained.count + 1
    assert newer.tool_dispatch_authorized is False
    assert newer.external_effect_proven is False
    assert newer.independent_custody_proven is False
    assert newer.manual_review_required is True
    assert backend.calls == 0
