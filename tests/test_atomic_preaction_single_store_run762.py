"""Disconnected atomic pre-action ledger regression (no backend dispatch)."""

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim(seed: str = "a") -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64)


def test_inert_atomic_reservation_restart_and_no_dispatch(tmp_path: Path) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    assert store.inspect(genesis).occurrence_ids == ()
    claim = _claim()
    tip = store.reserve(claim, retained=genesis)
    assert tip.count == 1 and tip != genesis
    recovered = DisconnectedAtomicPreactionLedger(path).inspect(tip)
    assert recovered.occurrence_ids == (claim.occurrence_id,)
    for property_name in (
        "tool_dispatch_authorized", "automatic_replay_authorized",
        "external_effect_proven", "trusted_approval_verified",
        "independent_custody_proven",
    ):
        assert getattr(recovered, property_name) is False
    assert not hasattr(store, "execute")
    with pytest.raises(AtomicPreactionRejected):
        store.reserve(claim, retained=tip)
    with pytest.raises(AtomicPreactionRejected):
        store.reserve(_claim("d"), retained=genesis)


@pytest.mark.parametrize("mutation", [
    "DELETE FROM preaction_audit",
    "UPDATE preaction_audit SET audit_sha256='bad'",
    "UPDATE intents SET chain_sha256='bad'",
    "DELETE FROM intents",
])
def test_missing_or_tampered_preaction_row_fails_closed(
    tmp_path: Path, mutation: str,
) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    tip = store.reserve(_claim(), retained=genesis_atomic_preaction_witness())
    with sqlite3.connect(path) as conn:
        conn.execute(mutation)
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path).inspect(tip)


def test_crash_with_uncommitted_intent_does_not_leave_half_audit(tmp_path: Path) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    child = (
        "import os,sqlite3,sys;"
        "c=sqlite3.connect(sys.argv[1]);"
        "c.execute('BEGIN IMMEDIATE');"
        "c.execute('INSERT INTO intents VALUES (1,?,?,?,?)',"
        "('occ_'+'d'*64,'bound_'+'b'*64,'c'*64,'f'*64));"
        "os._exit(27)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", child, str(path)],
        check=False, capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 27, proc.stderr
    assert store.inspect(genesis_atomic_preaction_witness()).occurrence_ids == ()
    assert DisconnectedAtomicPreactionLedger(path).inspect(
        genesis_atomic_preaction_witness()
    ).witness.count == 0


def test_lost_response_after_commit_requires_manual_review(tmp_path: Path) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    child = (
        "import os,sys;"
        "from pathlib import Path;"
        "from ark.agency.disconnected_atomic_preaction_ledger import "
        "DisconnectedAtomicPreactionLedger,AtomicIntentClaim,"
        "genesis_atomic_preaction_witness;"
        "c=AtomicIntentClaim('occ_'+'a'*64,'bound_'+'b'*64,'c'*64);"
        "s=DisconnectedAtomicPreactionLedger(Path(sys.argv[1]));"
        "s.reserve(c,retained=genesis_atomic_preaction_witness());"
        "os._exit(31)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", child, str(path)],
        check=False, capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 31, proc.stderr
    with pytest.raises(AtomicPreactionRejected):
        store.inspect(genesis_atomic_preaction_witness())
    with pytest.raises(AtomicPreactionRejected):
        store.reserve(_claim(), retained=genesis_atomic_preaction_witness())
    # This local DB read is NOT an independently authenticated witness.
    with sqlite3.connect(path) as conn:
        count, tip = conn.execute(
            "SELECT seq,chain_sha256 FROM intents ORDER BY seq DESC LIMIT 1"
        ).fetchone()
    recovered = store.inspect(AtomicPreactionWitness(count, tip))
    assert recovered.occurrence_ids == (_claim().occurrence_id,)
    assert recovered.automatic_replay_authorized is False


def test_competing_independent_writers_only_one_commits(tmp_path: Path) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    child = (
        "import sys;"
        "from pathlib import Path;"
        "from ark.agency.disconnected_atomic_preaction_ledger import "
        "DisconnectedAtomicPreactionLedger,AtomicIntentClaim,"
        "genesis_atomic_preaction_witness,AtomicPreactionRejected;"
        "s=DisconnectedAtomicPreactionLedger(Path(sys.argv[1]));"
        "s.reserve(AtomicIntentClaim('occ_'+sys.argv[2]*64,"
        "'bound_'+'b'*64,'c'*64),retained=genesis_atomic_preaction_witness())"
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", child, str(path), seed],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        ) for seed in ("a", "d")
    ]
    results = [process.communicate(timeout=20) for process in processes]
    assert sum(process.returncode == 0 for process in processes) == 1, results
    with sqlite3.connect(path) as conn:
        count, tip = conn.execute(
            "SELECT seq,chain_sha256 FROM intents ORDER BY seq DESC LIMIT 1"
        ).fetchone()
    assert count == 1
    recovered = store.inspect(AtomicPreactionWitness(count, tip))
    assert len(recovered.occurrence_ids) == 1
    assert recovered.external_effect_proven is False


def test_exact_inputs_schema_and_fresh_file_gate(tmp_path: Path) -> None:
    path = tmp_path / "atomic.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger.create(path)
    with pytest.raises(AtomicPreactionRejected):
        store.reserve(_claim(), retained=AtomicPreactionWitness(True, "a" * 64))
    with pytest.raises(AtomicPreactionRejected):
        store.reserve(AtomicIntentClaim("oops", "bound_" + "b" * 64, "c" * 64),
                      retained=genesis)
    assert store.inspect(genesis).witness == genesis
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unexpected (x INTEGER)")
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)


def test_no_accidental_process_or_filesystem_authority(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    with pytest.raises(AtomicPreactionRejected):
        DisconnectedAtomicPreactionLedger(path)
    assert not path.exists()
    assert os.path.exists(tmp_path)
