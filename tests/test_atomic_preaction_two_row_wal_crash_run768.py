"""Pre-action reservation rollback is atomic at each SQLite write boundary.

Only synthetic local SQLite rows and child Python processes are used.
A local reservation is not evidence of an external tool effect or consent.
"""

from __future__ import annotations

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


def _claim(seed: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64,
    )


@pytest.mark.parametrize("insert_audit", (False, True))
def test_killed_second_reservation_rolls_back_both_tables(
    tmp_path: Path, insert_audit: bool,
) -> None:
    path = tmp_path / "preaction.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    first = _claim("a")
    retained = store.reserve(
        first, retained=genesis_atomic_preaction_witness(),
    )
    child = (
        "import os,sqlite3,sys;"
        "c=sqlite3.connect(sys.argv[1]);"
        "c.execute('BEGIN IMMEDIATE');"
        "c.execute('INSERT INTO intents VALUES (2,?,?,?,?)',"
        "('occ_'+'d'*64,'bound_'+'b'*64,'c'*64,'f'*64));"
        "c.execute('INSERT INTO preaction_audit VALUES (2,?,?)',"
        "('occ_'+'d'*64,'e'*64)) if sys.argv[2]=='yes' else None;"
        "os._exit(47)"
    )
    result = subprocess.run(
        [sys.executable, "-c", child, str(path), "yes" if insert_audit else "no"],
        check=False, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 47, result.stderr
    reopened = DisconnectedAtomicPreactionLedger(path)
    assert reopened.inspect(retained).occurrence_ids == (first.occurrence_id,)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM intents").fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM preaction_audit"
        ).fetchone()[0] == 1
    new_tip = reopened.reserve(_claim("d"), retained=retained)
    assert new_tip.count == 2
    verified = DisconnectedAtomicPreactionLedger(path).inspect(new_tip)
    assert verified.occurrence_ids == (
        first.occurrence_id, _claim("d").occurrence_id,
    )
    assert verified.tool_dispatch_authorized is False
    assert verified.automatic_replay_authorized is False


def test_second_reservation_committed_but_response_lost_is_not_retryable(
    tmp_path: Path,
) -> None:
    path = tmp_path / "preaction.sqlite"
    store = DisconnectedAtomicPreactionLedger.create(path)
    prior = store.reserve(
        _claim("a"), retained=genesis_atomic_preaction_witness(),
    )
    child = (
        "import os,sys;"
        "from pathlib import Path;"
        "from ark.agency.disconnected_atomic_preaction_ledger import "
        "AtomicPreactionWitness,AtomicIntentClaim,"
        "DisconnectedAtomicPreactionLedger;"
        "s=DisconnectedAtomicPreactionLedger(Path(sys.argv[1]));"
        "s.reserve(AtomicIntentClaim('occ_'+'d'*64,"
        "'bound_'+'b'*64,'c'*64),"
        "retained=AtomicPreactionWitness(1,sys.argv[2]));"
        "os._exit(48)"
    )
    result = subprocess.run(
        [sys.executable, "-c", child, str(path), prior.tip_sha256],
        check=False, capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 48, result.stderr
    reopened = DisconnectedAtomicPreactionLedger(path)
    with pytest.raises(AtomicPreactionRejected):
        reopened.reserve(_claim("d"), retained=prior)
    with pytest.raises(AtomicPreactionRejected):
        reopened.inspect(prior)
    # A same-file read can diagnose an ambiguous commit but cannot attribute
    # it to the crashed caller or authorize external dispatch/replay.
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT seq,chain_sha256 FROM intents ORDER BY seq DESC LIMIT 1"
        ).fetchone()
    observed = reopened.inspect(AtomicPreactionWitness(*row))
    assert observed.occurrence_ids == (
        _claim("a").occurrence_id, _claim("d").occurrence_id,
    )
    assert observed.external_effect_proven is False
    assert observed.trusted_approval_verified is False
    assert observed.automatic_replay_authorized is False
