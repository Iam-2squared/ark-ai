"""Run956: registry-bound WRITE remains quarantined across cold local replay.

The only committed data are synthetic SQLite intent and digest-only audit.
The process-local grant/token is not durable consent or execution authority;
no connected backend is ever called.
"""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    ToolCall,
)
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registered backend must remain disconnected")


def _registered():
    backend = _NeverExecute()
    call = ToolCall(
        "fixture.write", "fixture.capability", "scope:private",
        {"synthetic": True},
    )
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "fixture.capability", Effect.WRITE,
            "disconnected.v1", backend,
        ),
    ))
    return backend, call, registry


@pytest.mark.parametrize("replay", (
    "same-occurrence",
    "changed-occurrence-stale-prefix",
    "same-occurrence-new-token",
))
def test_cold_registered_write_never_replays_or_dispatches(
    tmp_path, replay: str,
) -> None:
    backend, call, registry = _registered()
    token = OneShotAuthorization("synthetic-one-shot", call.request_id, 200)
    grant = CapabilityGrant("fixture.capability", "scope:private")
    initial = PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=token,
    )
    occ = "occ_" + hashlib.sha256(b"original occurrence").hexdigest()
    claim = derive_registered_atomic_intent(
        registry, call, occurrence_id=occ,
    )
    assert initial.bound_action_id == claim.bound_action_id

    path = tmp_path / "synthetic-registered-preaction.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    committed = ledger.reserve(claim, retained=genesis)
    before = None
    with sqlite3.connect(path) as conn:
        before = (
            conn.execute("SELECT * FROM intents ORDER BY seq").fetchall(),
            conn.execute("SELECT * FROM preaction_audit ORDER BY seq").fetchall(),
        )

    # The next process can recreate a local PermissionGate, but cannot turn
    # the committed pre-action digest into an external execution receipt.
    restarted_gate = PermissionGate()
    restarted_token = (
        OneShotAuthorization("synthetic-second-token", call.request_id, 200)
        if replay == "same-occurrence-new-token" else token
    )
    local = restarted_gate.authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=restarted_token,
    )
    assert local.bound_action_id == claim.bound_action_id
    other_occ = "occ_" + hashlib.sha256(b"different occurrence").hexdigest()
    replay_claim = derive_registered_atomic_intent(
        registry, call,
        occurrence_id=other_occ if replay == "changed-occurrence-stale-prefix" else occ,
    )
    cold = DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        cold.reserve(
            replay_claim,
            retained=genesis if replay == "changed-occurrence-stale-prefix"
            else committed,
        )

    snapshot = cold.inspect(committed)
    assert snapshot.occurrence_ids == (occ,)
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.external_effect_proven is False
    assert snapshot.trusted_approval_verified is False
    assert snapshot.independent_custody_proven is False
    assert backend.calls == 0

    with sqlite3.connect(path) as conn:
        assert (
            conn.execute("SELECT * FROM intents ORDER BY seq").fetchall(),
            conn.execute("SELECT * FROM preaction_audit ORDER BY seq").fetchall(),
        ) == before


def test_independent_python_process_cannot_replay_committed_occurrence(
    tmp_path,
) -> None:
    backend, call, registry = _registered()
    occurrence = "occ_" + hashlib.sha256(b"child replay").hexdigest()
    original = derive_registered_atomic_intent(
        registry, call, occurrence_id=occurrence,
    )
    path = tmp_path / "disconnected-cross-process.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    tip = ledger.reserve(original, retained=genesis_atomic_preaction_witness())
    child = """
import sys
from pathlib import Path
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.disconnected_atomic_registry_bridge import derive_registered_atomic_intent
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected, AtomicPreactionWitness, DisconnectedAtomicPreactionLedger,
)
class Backend:
    def execute(self, _call):
        raise AssertionError("must not execute")
call = ToolCall("fixture.write", "fixture.capability", "scope:private", {"synthetic": True})
reg = ToolRegistry((ToolRegistration(
    "fixture.write", "fixture.capability", Effect.WRITE, "disconnected.v1", Backend(),
),))
claim = derive_registered_atomic_intent(reg, call, occurrence_id=sys.argv[2])
tip = AtomicPreactionWitness(1, sys.argv[3])
store = DisconnectedAtomicPreactionLedger(Path(sys.argv[1]))
try:
    store.reserve(claim, retained=tip)
except AtomicPreactionRejected:
    snapshot = store.inspect(tip)
    if snapshot.tool_dispatch_authorized or snapshot.automatic_replay_authorized:
        raise AssertionError("local result became execution authority")
    sys.exit(0)
raise AssertionError("duplicate occurrence was reserved")
"""
    result = subprocess.run(
        [sys.executable, "-c", child, str(path), occurrence, tip.tip_sha256],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert backend.calls == 0
    assert len(ledger.inspect(tip).occurrence_ids) == 1
