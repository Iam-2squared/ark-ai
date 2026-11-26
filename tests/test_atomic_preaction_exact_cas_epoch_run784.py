"""Exact-scalar CAS rejects forged witness equality and reentrant witness drift.

Only disposable local intent/audit SQLite is involved. Neither a matching
snapshot nor a local commit grants dispatch, replay or human permission.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as atomic
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(seed: str) -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64)


def test_forged_witness_equality_never_bypasses_read_or_write_cas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    old = genesis_atomic_preaction_witness()
    current = ledger.reserve(_claim("a"), retained=old)

    with monkeypatch.context() as patch:
        patch.setattr(AtomicPreactionWitness, "__eq__", lambda _a, _b: True)
        with pytest.raises(AtomicPreactionRejected, match="stale or mismatched"):
            ledger.inspect(old)
        with pytest.raises(AtomicPreactionRejected, match="CAS mismatch"):
            ledger.reserve(_claim("d"), retained=old)

    reopened = DisconnectedAtomicPreactionLedger(path)
    assert reopened.inspect(current).occurrence_ids == (_claim("a").occurrence_id,)
    with pytest.raises(AtomicPreactionRejected):
        reopened.inspect(old)


@pytest.mark.parametrize("operation", ("inspect", "reserve"))
def test_retained_witness_retarget_during_sqlite_scan_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, operation: str,
) -> None:
    path = tmp_path / "atomic.sqlite"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    retained = genesis_atomic_preaction_witness()
    original_scan = atomic._scan

    def mutate_after_scan(conn: object) -> atomic.AtomicPreactionSnapshot:
        result = original_scan(conn)
        object.__setattr__(retained, "tip_sha256", "f" * 64)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(atomic, "_scan", mutate_after_scan)
        with pytest.raises(AtomicPreactionRejected, match="stale or mismatched|CAS mismatch"):
            if operation == "inspect":
                ledger.inspect(retained)
            else:
                ledger.reserve(_claim("a"), retained=retained)

    assert ledger.inspect(genesis_atomic_preaction_witness()).occurrence_ids == ()
    next_tip = ledger.reserve(
        _claim("d"), retained=genesis_atomic_preaction_witness(),
    )
    recovered = DisconnectedAtomicPreactionLedger(path).inspect(next_tip)
    assert recovered.occurrence_ids == (_claim("d").occurrence_id,)
    assert recovered.tool_dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
