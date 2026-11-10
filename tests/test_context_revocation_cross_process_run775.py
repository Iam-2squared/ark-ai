"""Independent interpreters cannot re-grant a durable synthetic privacy veto.

Only disposable SQLite and synthetic scope digests are used. A local veto is
not authenticated consent or proof of deletion in other systems.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

_CHILD = """
import sys
import time
from pathlib import Path
from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger, SyntheticContextRevocationRejected,
)
db, owner, ready, gate = sys.argv[1:]
ledger = SyntheticContextRevocationLedger(Path(db), require_existing=True)
Path(ready).touch()
deadline = time.monotonic() + 25
while not Path(gate).exists():
    if time.monotonic() > deadline:
        sys.exit("revocation gate timed out")
    time.sleep(0.02)
try:
    ledger.revoke(MemoryScope(owner, "private"), at_ms=100)
except SyntheticContextRevocationRejected:
    sys.exit(4)
"""


@pytest.mark.parametrize("same_scope", (True, False))
def test_disconnected_revocation_competing_processes_preserve_veto(
    tmp_path: Path, same_scope: bool,
) -> None:
    path = tmp_path / "revocations.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    genesis = review_revocation_continuity(ledger)
    assert genesis.rows == ()
    owners = ("owner-a", "owner-a" if same_scope else "owner-b")
    gate = tmp_path / "start"
    processes: list[subprocess.Popen[str]] = []
    # Keep an ordinary SQLite handle while starting two separate interpreters;
    # each child opens its existing-only veto DB before the revoke race begins.
    with closing(sqlite3.connect(path)) as keeper:
        assert keeper.execute("PRAGMA journal_mode").fetchone() is not None
        try:
            for index, owner in enumerate(owners):
                ready = tmp_path / f"ready-{index}"
                process = subprocess.Popen(
                    [
                        sys.executable, "-c", _CHILD, str(path), owner,
                        str(ready), str(gate),
                    ],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                )
                processes.append(process)
                deadline = time.monotonic() + 25
                while not ready.exists():
                    if process.poll() is not None:
                        output = process.communicate()
                        raise AssertionError(
                            f"child {index} failed before veto race: {output}"
                        )
                    if time.monotonic() >= deadline:
                        raise AssertionError("child never reached veto race")
                    time.sleep(0.02)
            gate.touch()
            outputs = [p.communicate(timeout=35) for p in processes]
        finally:
            gate.touch()
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
    assert sorted(p.returncode for p in processes) == (
        [0, 4] if same_scope else [0, 0]
    ), outputs
    restarted = SyntheticContextRevocationLedger(
        path, require_existing=True,
    )
    witness = review_revocation_continuity(restarted, retained=genesis)
    assert len(witness.rows) == (1 if same_scope else 2)
    assert witness.witness_id != genesis.witness_id
    assert review_revocation_continuity(restarted, retained=witness) == witness
    for owner in set(owners):
        with pytest.raises(SyntheticContextRevocationRejected):
            restarted.assert_not_revoked((MemoryScope(owner, "private"),))
    # Absence in the local veto table is a denial-only observation, not consent.
    restarted.assert_not_revoked((MemoryScope("unrelated", "private"),))
