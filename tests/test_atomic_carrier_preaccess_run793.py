"""Fail-closed intent, witness and receipt carrier custody without tool dispatch.

All SQLite files are disposable local fixtures. A dataclass field or denial
getter replaced after module import must not execute before rejection.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionSnapshot,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim() -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)


@pytest.mark.parametrize("slot", ("occurrence_id", "bound_action_id", "request_sha256"))
def test_claim_descriptor_replacement_denied_before_getter_and_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, slot: str,
) -> None:
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "intent.sqlite")
    claim = _claim()
    called: list[str] = []

    def hostile(_self: object) -> str:
        called.append(slot)
        raise AssertionError("forged claim getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(AtomicIntentClaim, slot, property(hostile))
        with pytest.raises(AtomicPreactionRejected, match="carrier definition"):
            ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
    # The witness constructor is deliberately checked too. The failure must
    # occur without touching this substituted getter or inserting an intent.
    assert called == []
    assert ledger.inspect(genesis_atomic_preaction_witness()).occurrence_ids == ()


@pytest.mark.parametrize("slot", ("count", "tip_sha256"))
def test_witness_descriptor_replacement_denied_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, slot: str,
) -> None:
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "intent.sqlite")
    witness = genesis_atomic_preaction_witness()
    called: list[str] = []

    def hostile(_self: object) -> object:
        called.append(slot)
        raise AssertionError("forged witness getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(AtomicPreactionWitness, slot, property(hostile))
        patch.setattr(ledger, "_open", lambda **_kw: pytest.fail("SQLite opened"))
        with pytest.raises(AtomicPreactionRejected, match="carrier definition"):
            ledger.inspect(witness)
    assert called == []
    assert ledger.inspect(witness).occurrence_ids == ()


@pytest.mark.parametrize(
    "slot",
    (
        "tool_dispatch_authorized", "automatic_replay_authorized",
        "external_effect_proven", "trusted_approval_verified",
        "independent_custody_proven",
    ),
)
def test_snapshot_denial_replacement_rejected_before_private_scan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, slot: str,
) -> None:
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "intent.sqlite")
    witness = genesis_atomic_preaction_witness()
    called: list[str] = []

    def hostile(_self: object) -> bool:
        called.append(slot)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(AtomicPreactionSnapshot, slot, property(hostile))
        patch.setattr(atomic, "_schema", lambda _conn: pytest.fail("schema scanned"))
        with pytest.raises(AtomicPreactionRejected, match="carrier definition"):
            ledger.inspect(witness)
    assert called == []
    assert ledger.inspect(witness).tool_dispatch_authorized is False


def test_ordinary_atomic_cas_and_restart_remain_inert(tmp_path: Path) -> None:
    path = tmp_path / "intent.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    previous = genesis_atomic_preaction_witness()
    new_tip = ledger.reserve(_claim(), retained=previous)
    assert new_tip.count == 1
    snapshot = DisconnectedAtomicPreactionLedger(path).inspect(new_tip)
    assert snapshot.occurrence_ids == (_claim().occurrence_id,)
    assert snapshot.tool_dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    with pytest.raises(AtomicPreactionRejected):
        ledger.reserve(_claim(), retained=new_tip)
