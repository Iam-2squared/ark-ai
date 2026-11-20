"""Run1012: independent processes contend for the final privacy-veto slot.

Only synthetic MemoryScope identities and disposable local SQLite are used.
The ledger is a negative-use fence, never consent or proof of erasure.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ark import personal_context_revocation_review as revocation
from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)


_CHILD = """
import sys
import time
from pathlib import Path
import ark.personal_context_revocation_review as module
from ark.memory.contracts import MemoryScope

database, ready_name, release_name, namespace = sys.argv[1:]
module._MAX_REVOCATION_ROWS = 1
ledger = module.SyntheticContextRevocationLedger(
    Path(database), require_existing=True,
)
ready = Path(ready_name)
release = Path(release_name)
ready.touch()
deadline = time.monotonic() + 25
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit(8)
    time.sleep(0.01)
try:
    ledger.revoke(
        MemoryScope("synthetic-owner", namespace),
        at_ms=100,
    )
except module.SyntheticContextRevocationRejected as exc:
    if "capacity exhausted" in str(exc):
        sys.exit(4)
    raise
sys.exit(0)
"""


def test_two_processes_cannot_overrun_the_last_revocation_capacity_slot(
    tmp_path: Path,
) -> None:
    path = tmp_path / "synthetic-revocation-capacity.sqlite3"
    initial_ledger = revocation.SyntheticContextRevocationLedger(path)
    retained = review_revocation_continuity(initial_ledger)
    assert retained.rows == ()

    release = tmp_path / "release"
    ready = (tmp_path / "ready-a", tmp_path / "ready-b")
    namespaces = ("context-a", "context-b")
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(ready[index]),
                str(release), namespaces[index],
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all(marker.exists() for marker in ready):
            if any(process.poll() is not None for process in processes):
                outputs = [process.communicate(timeout=5) for process in processes]
                raise AssertionError(f"revocation worker exited before barrier: {outputs}")
            if time.monotonic() >= deadline:
                raise AssertionError("revocation workers did not reach barrier")
            time.sleep(0.01)
        release.touch()
        outputs = [process.communicate(timeout=35) for process in processes]
        assert sorted(process.returncode for process in processes) == [0, 4], outputs
    finally:
        release.touch()
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest,revoked_at_ms "
            "FROM synthetic_context_revocations ORDER BY scope_digest"
        ).fetchall()
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert len(rows) == 1
    assert len(rows[0][0]) == 64
    assert rows[0][1] == 100
    raw = path.read_bytes()
    assert b"synthetic-owner" not in raw
    assert b"context-a" not in raw
    assert b"context-b" not in raw

    cold = revocation.SyntheticContextRevocationLedger(
        path, require_existing=True,
    )
    observed = review_revocation_continuity(cold, retained=retained)
    assert len(observed.rows) == 1
    assert observed.rows[0][1] == 100

    candidates = tuple(
        MemoryScope("synthetic-owner", namespace) for namespace in namespaces
    )
    revoked = tuple(
        scope for scope in candidates
        if revocation._scope_digest(scope) == rows[0][0]
    )
    allowed_only_as_unrevoked_fixture = tuple(
        scope for scope in candidates
        if revocation._scope_digest(scope) != rows[0][0]
    )
    assert len(revoked) == len(allowed_only_as_unrevoked_fixture) == 1
    with pytest.raises(revocation.SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked(revoked)
    cold.assert_not_revoked(allowed_only_as_unrevoked_fixture)
