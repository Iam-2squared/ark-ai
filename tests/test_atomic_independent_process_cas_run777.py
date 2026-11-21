"""Two independent processes cannot consume one pre-action CAS witness twice.

All operations are on temporary local audit/intent SQLite; no ToolBackend,
approval, credential, notification or physical device is involved.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)

_CHILD = """
import sys
from pathlib import Path
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim, AtomicPreactionRejected,
    DisconnectedAtomicPreactionLedger, genesis_atomic_preaction_witness,
)
ledger = DisconnectedAtomicPreactionLedger(Path(sys.argv[1]))
print("ready", flush=True)
if sys.stdin.readline().strip() != "go":
    raise RuntimeError("synthetic barrier not released")
try:
    witness = ledger.reserve(
        AtomicIntentClaim(sys.argv[2], sys.argv[3], sys.argv[4]),
        retained=genesis_atomic_preaction_witness(),
    )
except AtomicPreactionRejected:
    print("rejected", flush=True)
else:
    print("committed", witness.count, witness.tip_sha256, flush=True)
"""


@pytest.mark.parametrize("same_occurrence", (False, True))
def test_independent_processes_single_atomic_witness_winner(
    tmp_path: Path, same_occurrence: bool,
) -> None:
    path = tmp_path / "intent.sqlite"
    DisconnectedAtomicPreactionLedger.create(path)
    occurrences = (
        "occ_" + "a" * 64,
        "occ_" + ("a" if same_occurrence else "b") * 64,
    )
    bound = "bound_" + "c" * 64
    request = "d" * 64
    children: list[subprocess.Popen[str]] = []
    results: list[str] = []

    # Retain a live WAL connection so neither child can unlink the sidecars
    # between independent startup and the actual competing BEGIN IMMEDIATE.
    with closing(sqlite3.connect(path)) as keeper:
        assert keeper.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert keeper.execute("SELECT COUNT(*) FROM intents").fetchone()[0] == 0
        try:
            # Construct and validate both independent ledger handles BEFORE
            # releasing the race, not during the sidecar bootstrap window.
            for occurrence in occurrences:
                child = subprocess.Popen(
                    [sys.executable, "-c", _CHILD, str(path), occurrence,
                     bound, request],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True,
                )
                children.append(child)
                assert child.stdout is not None
                assert child.stdout.readline().strip() == "ready"
            for child in children:
                assert child.stdin is not None
                child.stdin.write("go\n")
                child.stdin.flush()
            for child in children:
                output, stderr = child.communicate(timeout=35)
                assert child.returncode == 0, (output, stderr)
                results.append(output.strip())
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=15)

    committed = [value for value in results if value.startswith("committed ")]
    assert len(committed) == 1, results
    assert results.count("rejected") == 1, results
    _, count, sha = committed[0].split()
    assert count == "1"
    ledger = DisconnectedAtomicPreactionLedger(path)
    observed = ledger.inspect(AtomicPreactionWitness(1, sha))
    assert observed.occurrence_ids in (
        (occurrences[0],), (occurrences[1],),
    )
    assert observed.tool_dispatch_authorized is False
    assert observed.automatic_replay_authorized is False
    assert observed.external_effect_proven is False
    with pytest.raises(AtomicPreactionRejected):
        ledger.inspect(genesis_atomic_preaction_witness())
