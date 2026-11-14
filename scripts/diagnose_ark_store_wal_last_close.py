"""Disposable actual ARK Memory/ActionAudit/revocation WAL last-close diagnostic.

This is a path-free, disconnected two-process fixture. It uses only new
TemporaryDirectory databases and preexisting READ APIs; no backend, approval,
external effect, user database, repair, deletion or automatic write retry.
Observed SQLite sidecar unlink is NOT permission to relax alias checks.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
from contextlib import closing
from pathlib import Path

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

_CHILD = """
import sqlite3
import sys
import time
from pathlib import Path
db, table, ready, release = sys.argv[1:]
conn = sqlite3.connect(db)
try:
    conn.execute("BEGIN")
    conn.execute("SELECT COUNT(*) FROM " + table).fetchone()
    Path(ready).touch()
    deadline = time.monotonic() + 8
    while not Path(release).exists():
        if time.monotonic() >= deadline:
            sys.exit(3)
        time.sleep(0.01)
finally:
    conn.close()
"""
_TABLES = {
    "memory": "memory_events",
    "audit": "action_events",
    "revocation": "synthetic_context_revocations",
}


def bounded_count(raw: str) -> int:
    if type(raw) is not str:
        raise argparse.ArgumentTypeError("iterations must be 1..4")
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("iterations must be 1..4") from exc
    if not 1 <= value <= 4:
        raise argparse.ArgumentTypeError("iterations must be 1..4")
    return value


def _category(info: os.stat_result) -> str:
    if not stat.S_ISREG(info.st_mode):
        return "NONREGULAR"
    if info.st_nlink == 0:
        return "UNLINKED"
    if info.st_nlink == 1:
        return "SINGLE_LINK"
    return "MULTILINK"


def probe_ark_store(*, kind: str, keeper: bool) -> dict[str, object]:
    """Measure last SQLite client close using an actual inert ARK v1 schema."""
    # Refuse caller-defined equality/hash and truth-value hooks before
    # creating even a disposable database or subprocess. CLI parsing already
    # supplies exact str/bool values; direct fixture users get the same fence.
    if type(kind) is not str or kind not in _TABLES:
        raise ValueError("unknown disposable store kind")
    if type(keeper) is not bool:
        raise ValueError("keeper must be an exact boolean")
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        return {"status": "UNSUPPORTED", "kind": kind, "keeper": keeper}
    with tempfile.TemporaryDirectory(prefix="ark-disposable-wal-") as root:
        db = Path(root) / "fixture.sqlite"
        shm = Path(str(db) + "-shm")
        ready = Path(root) / "ready"
        release = Path(root) / "release"
        conn: sqlite3.Connection | None = None
        child: subprocess.Popen[bytes] | None = None
        held_fd: int | None = None
        try:
            if kind == "memory":
                store = SQLiteMemoryStore(db, clock_ms=lambda: 100)
                scope = MemoryScope("disposable-owner")
                original = store.put(MemoryWrite(scope, "source", "inert"))
            elif kind == "audit":
                store = SQLiteActionAudit(db, clock_ms=lambda: 100)
                original = store.append(
                    ToolCall("fixture.read", "fixture.read", "fixture-scope", {}),
                    outcome="synthetic_only",
                )
            else:
                # Only this disposable fixture opts the normally non-WAL veto
                # ledger into WAL, so a last-client-close race can be measured
                # without changing production persistence or authorization.
                store = SyntheticContextRevocationLedger(db)
                scope = MemoryScope("disposable-owner", "profile")
                with closing(sqlite3.connect(db)) as setup:
                    if setup.execute("PRAGMA journal_mode=WAL").fetchone() != ("wal",):
                        return {"status": "NO_WAL", "kind": kind, "keeper": keeper}
                original = store.revoke(scope, at_ms=100)
            conn = sqlite3.connect(db)
            if conn.execute("PRAGMA journal_mode").fetchone() != ("wal",):
                return {"status": "NO_WAL", "kind": kind, "keeper": keeper}
            conn.execute("BEGIN")
            count = conn.execute(
                "SELECT COUNT(*) FROM " + _TABLES[kind]
            ).fetchone()[0]
            if count != 1 or not shm.is_file():
                return {"status": "NO_SHM", "kind": kind, "keeper": keeper}
            held_fd = os.open(shm, os.O_RDONLY | os.O_NOFOLLOW)
            if _category(os.fstat(held_fd)) != "SINGLE_LINK":
                return {"status": "NONSTANDARD_SHM", "kind": kind, "keeper": keeper}
            child = subprocess.Popen(
                [
                    sys.executable, "-c", _CHILD, str(db), _TABLES[kind],
                    str(ready), str(release),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            deadline = time.monotonic() + 8
            while not ready.exists() and child.poll() is None:
                if time.monotonic() > deadline:
                    break
                time.sleep(0.01)
            if not ready.exists():
                return {"status": "CHILD_NOT_READY", "kind": kind, "keeper": keeper}
            if not keeper:
                conn.close()
                conn = None
            before = _category(os.fstat(held_fd))
            release.touch()
            try:
                child_exit = child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                return {"status": "CHILD_TIMEOUT", "kind": kind, "keeper": keeper}
            if child_exit != 0:
                return {"status": "CHILD_FAILED", "kind": kind, "keeper": keeper}
            after_child = _category(os.fstat(held_fd))
            if conn is not None:
                conn.close()
                conn = None
            after_final = _category(os.fstat(held_fd))
            # Inspect these before a subsequent WAL reopen can create another
            # pathname. An unlinked old descriptor is not a retained witness.
            final_name_absent = not shm.exists()
            if kind == "memory":
                cold = SQLiteMemoryStore(db, clock_ms=lambda: 101)
                recovered = cold.get(original.memory_id, scope, include_expired=True)
                data_intact = recovered == original
            elif kind == "audit":
                cold = SQLiteActionAudit(db, clock_ms=lambda: 101)
                restored = cold.events()
                data_intact = len(restored) == 1 and restored[0] == original
            else:
                # A cold restart must still veto the exact synthetic scope.
                # A durable marker never authorizes an automatic replay.
                cold = SyntheticContextRevocationLedger(db, require_existing=True)
                try:
                    cold.assert_not_revoked((scope,))
                except SyntheticContextRevocationRejected as error:
                    data_intact = "revoked" in str(error) and len(original) == 64
                else:
                    data_intact = False
            return {
                "status": "OK", "kind": kind, "keeper": keeper,
                "before_child_close": before,
                "after_child_close": after_child,
                "after_final_close": after_final,
                "final_path_absent": final_name_absent,
                "cold_read_intact": data_intact,
                "auto_retry_authorized": False,
                "real_tool_dispatched": False,
                "alias_checks_relaxed": False,
                "user_paths_exported": False,
            }
        except (OSError, sqlite3.Error, ValueError, RuntimeError):
            return {"status": "PROBE_ERROR", "kind": kind, "keeper": keeper}
        finally:
            release.touch()
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=8)
            if conn is not None:
                conn.close()
            if held_fd is not None:
                os.close(held_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=tuple(_TABLES), required=True)
    parser.add_argument("--keeper", action="store_true")
    parser.add_argument("--iterations", type=bounded_count, default=1)
    args = parser.parse_args(argv)
    observations = [
        probe_ark_store(kind=args.kind, keeper=args.keeper)
        for _ in range(args.iterations)
    ]
    print(json.dumps({
        "schema_version": 1,
        "observations": observations,
        "automatic_retry_authorized": False,
        "tool_execution_authorized": False,
        "private_paths_exported": False,
    }, sort_keys=True))
    return 0 if all(x["status"] in ("OK", "UNSUPPORTED") for x in observations) else 1


if __name__ == "__main__":
    raise SystemExit(main())
