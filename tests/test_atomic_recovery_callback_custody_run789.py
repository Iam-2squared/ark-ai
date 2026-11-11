"""Synthetic pre-action recovery refuses altered callbacks before ledger reads.

Neither a local membership result nor a retained digest is WRITE permission.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_recovery_quarantine as recovery
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionSnapshot,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.registry import ToolRegistration, ToolRegistry

_OCCURRENCE = "occ_" + "a" * 64


class NeverExecute:
    def execute(self, _call: ToolCall) -> object:
        raise AssertionError("recovery preview must never execute tools")


def _inputs(tmp_path: Path):
    call = ToolCall("fixture", "local.write", "offline", {"k": "v"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "local.write", Effect.WRITE, "local", NeverExecute()),
    ))
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "preaction.sqlite")
    return ledger, genesis_atomic_preaction_witness(), registry, call


@pytest.mark.parametrize("surface", (
    "ledger_inspect", "derivation", "denial_names", "snapshot_witness",
    "snapshot_hook", "result_denial", "result_field", "result_hook",
))
def test_modified_recovery_control_plane_denied_before_any_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, surface: str,
) -> None:
    ledger, retained, registry, call = _inputs(tmp_path)
    invoked = []

    def poison(*_args: object, **_kwargs: object) -> object:
        invoked.append(surface)
        raise AssertionError("poison callback was invoked")

    with monkeypatch.context() as patch:
        if surface == "ledger_inspect":
            patch.setattr(DisconnectedAtomicPreactionLedger, "inspect", poison)
        elif surface == "derivation":
            patch.setattr(recovery, "derive_registered_atomic_intent", poison)
        elif surface == "denial_names":
            patch.setattr(recovery, "_SNAPSHOT_DENIALS", ())
        elif surface == "snapshot_witness":
            patch.setattr(AtomicPreactionSnapshot, "witness", property(poison))
        elif surface == "snapshot_hook":
            patch.setattr(AtomicPreactionSnapshot, "__getattribute__", poison)
        elif surface == "result_denial":
            patch.setattr(
                recovery.AtomicRecoveryQuarantine,
                "tool_dispatch_authorized", property(poison),
            )
        elif surface == "result_field":
            patch.setattr(
                recovery.AtomicRecoveryQuarantine,
                "locally_recorded", property(poison),
            )
        else:
            patch.setattr(
                recovery.AtomicRecoveryQuarantine,
                "__getattribute__", poison,
            )

        with pytest.raises(
            recovery.AtomicRecoveryQuarantineRejected,
            match="authority definition changed",
        ):
            recovery.review_registered_atomic_recovery(
                ledger, retained, registry, call, occurrence_id=_OCCURRENCE,
            )
    assert invoked == []


def test_original_recovery_path_remains_deny_only(tmp_path: Path) -> None:
    ledger, retained, registry, call = _inputs(tmp_path)
    result = recovery.review_registered_atomic_recovery(
        ledger, retained, registry, call, occurrence_id=_OCCURRENCE,
    )
    assert result.locally_recorded is False
    assert result.retained_count == 0
    assert result.manual_review_required is True
    assert result.binding_proven is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
