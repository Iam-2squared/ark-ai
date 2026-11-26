"""Disconnected recovery compares retained scalars without patchable equality.

No local receipt authenticates consent, replays a WRITE, or dispatches a Tool.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_recovery_quarantine as recovery
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import derive_registered_atomic_intent
from ark.agency.registry import ToolRegistration, ToolRegistry

_OCC = "occ_" + "a" * 64


class NoExecution:
    calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("no real or mock backend dispatch in recovery")


def _fixture(path: Path, *, recorded: bool):
    backend = NoExecution()
    call = ToolCall("writer", "fixture.write", "offline", {"test": "only"})
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "local", backend),
    ))
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    witness = genesis_atomic_preaction_witness()
    if recorded:
        intent = derive_registered_atomic_intent(registry, call, occurrence_id=_OCC)
        witness = ledger.reserve(intent, retained=witness)
    return ledger, witness, registry, call, backend


@pytest.mark.parametrize("recorded", [False, True])
def test_witness_equality_callback_is_never_invoked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, recorded: bool,
) -> None:
    ledger, witness, registry, call, backend = _fixture(
        tmp_path / "atomic.sqlite", recorded=recorded,
    )
    def forbidden(_left: object, _right: object) -> bool:
        raise AssertionError("mutable witness __eq__ must not be used")

    with monkeypatch.context() as patch:
        patch.setattr(AtomicPreactionWitness, "__eq__", forbidden)
        result = recovery.review_registered_atomic_recovery(
            ledger, witness, registry, call, occurrence_id=_OCC,
        )
    assert result.locally_recorded is recorded
    assert result.retained_count == int(recorded)
    assert result.manual_review_required is True
    assert result.tool_dispatch_authorized is False
    assert backend.calls == 0


@pytest.mark.parametrize("surface", (
    "witness_image_callback", "witness_count_descriptor", "witness_lookup_hook",
))
def test_recovery_rejects_replaced_witness_protocol_before_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, surface: str,
) -> None:
    ledger, witness, registry, call, backend = _fixture(
        tmp_path / "atomic.sqlite", recorded=False,
    )
    touched = []

    def forbidden(*_args: object, **_kwargs: object) -> object:
        touched.append("called")
        raise AssertionError("untrusted callback ran before rejection")

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "_open", forbidden)
        if surface == "witness_image_callback":
            patch.setattr(recovery, "_witness_image", forbidden)
        elif surface == "witness_count_descriptor":
            patch.setattr(AtomicPreactionWitness, "count", property(forbidden))
        else:
            patch.setattr(AtomicPreactionWitness, "__getattribute__", forbidden)
        with pytest.raises(
            recovery.AtomicRecoveryQuarantineRejected,
            match="authority definition changed",
        ):
            recovery.review_registered_atomic_recovery(
                ledger, witness, registry, call, occurrence_id=_OCC,
            )
    assert touched == []
    assert backend.calls == 0
