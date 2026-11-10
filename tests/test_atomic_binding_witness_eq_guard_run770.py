"""Atomic binding recovery must not trust patchable witness equality.

Local digest matching is never consent, dispatch permission, independent audit,
or external effect evidence. The mock backend must remain uninvoked.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_binding_snapshot_review import (
    AtomicBindingSnapshotRejected,
    review_registered_atomic_binding_snapshot,
)
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("recovery review invoked backend")


@pytest.mark.parametrize("stale_tip", (False, True))
def test_witness_equality_rebinding_cannot_accept_a_different_sqlite_tip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stale_tip: bool,
) -> None:
    backend = _NeverExecute()
    call = ToolCall("writer", "fixture.write", "offline", {"item": "v"})
    registry = ToolRegistry((
        ToolRegistration(
            "writer", "fixture.write", Effect.WRITE, "local", backend,
        ),
    ))
    ledger = DisconnectedAtomicPreactionLedger.create(
        tmp_path / "intent.sqlite",
    )
    occurrence = "occ_" + "a" * 64
    witness = ledger.reserve(
        derive_registered_atomic_intent(
            registry, call, occurrence_id=occurrence,
        ),
        retained=genesis_atomic_preaction_witness(),
    )
    retained = AtomicPreactionWitness(
        witness.count, ("f" * 64) if stale_tip else witness.tip_sha256,
    )
    invoked: list[bool] = []

    def forbidden_eq(*_args: object, **_kwargs: object) -> bool:
        invoked.append(True)
        raise AssertionError("untrusted witness __eq__ executed")

    with monkeypatch.context() as patch:
        patch.setattr(AtomicPreactionWitness, "__eq__", forbidden_eq)
        if stale_tip:
            with pytest.raises(
                AtomicBindingSnapshotRejected,
                match="retained snapshot mismatch",
            ):
                review_registered_atomic_binding_snapshot(
                    ledger, retained, registry, call, occurrence_id=occurrence,
                )
        else:
            result = review_registered_atomic_binding_snapshot(
                ledger, retained, registry, call, occurrence_id=occurrence,
            )
            assert result.local_state == "LOCAL_MATCH"
            assert result.binding_proven is False
            assert result.tool_dispatch_authorized is False
            assert result.automatic_replay_authorized is False
            assert result.manual_review_required is True
    assert invoked == []
    assert backend.calls == 0
