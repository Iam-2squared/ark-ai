"""Disposable SQLite sidecar descriptor/last-close lifecycle probe.

This intentionally measures *held-FD* link counts, unlike pathname-only
sidecar inventories. It opens only its own TemporaryDirectory and uses one
separate local Python interpreter to observe final-connection cleanup.
No ARK user database, real ToolBackend, consent, authority or automatic replay.
An unlinked -shm FD can be an ordinary SQLite lifecycle event, not evidence
that an unsafe or aliased file should be accepted by production guards.

Run: python scripts/diagnose_sqlite_sidecar_fd_lifecycle.py --iterations 2
     python scripts/diagnose_sqlite_sidecar_fd_lifecycle.py --keeper
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
from pathlib import Path

_CHILD = """
import sqlite3
import sys
import time
from pathlib import Path
path, ready, release = (Path(item) for item in sys.argv[1:4])
try:
    connection = sqlite3.connect(path)
    connection.execute("SELECT COUNT(*) FROM specimen").fetchone()
    ready.touch()
    deadline = time.monotonic() + 8
    while not release.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("disposable child release timed out")
        time.sleep(0.01)
    connection.close()
except Exception:
    sys.exit(2)
"""


def _bounded_iterations(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("iterations must be 1..8") from exc
    if not 1 <= number <= 8:
        raise argparse.ArgumentTypeError("iterations must be 1..8")
    return number


def _descriptor_category(fd: int) -> str:
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode):
        return "NONREGULAR"
    if metadata.st_nlink == 0:
        return "UNLINKED"
    if metadata.st_nlink == 1:
        return "SINGLE_LINK"
    return "MULTILINK"


def _name_category(path: Path) -> str:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return "ABSENT"
    except OSError:
        return "UNAVAILABLE"
    if not stat.S_ISREG(metadata.st_mode):
        return "NONREGULAR"
    if metadata.st_nlink == 1:
        return "SINGLE_LINK"
    return "OTHER_LINKS"


def probe_disposable_last_close(*, keeper: bool) -> dict[str, object]:
    """Return only bounded categories from a disposable WAL reader lifecycle.

    This is a Linux/POSIX forensic observation, not a replacement for ARK's
    fail-closed descriptor, no-follow, single-link or schema validation.
    """
    if (
        os.name != "posix"
        or not getattr(os, "O_NOFOLLOW", 0)
        or not getattr(os, "O_CLOEXEC", 0)
    ):
        return {"status": "UNSUPPORTED", "keeper": keeper}
    with tempfile.TemporaryDirectory(prefix="ark-disposable-fd-") as root:
        path = Path(root) / "specimen.sqlite"
        sidecar = Path(str(path) + "-shm")
        ready = Path(root) / "ready"
        release = Path(root) / "release"
        connection: sqlite3.Connection | None = None
        child: subprocess.Popen[bytes] | None = None
        fd: int | None = None
        try:
            connection = sqlite3.connect(path)
            if connection.execute("PRAGMA journal_mode=WAL").fetchone() != ("wal",):
                return {"status": "NO_WAL", "keeper": keeper}
            connection.execute("CREATE TABLE specimen(value INTEGER NOT NULL)")
            connection.execute("INSERT INTO specimen VALUES (1)")
            connection.commit()
            # Explicit read transaction keeps a keeper WAL snapshot active.
            if keeper:
                connection.execute("BEGIN")
            connection.execute("SELECT COUNT(*) FROM specimen").fetchone()
            if _name_category(sidecar) != "SINGLE_LINK":
                return {"status": "NO_SHM", "keeper": keeper}
            fd = os.open(sidecar, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            if _descriptor_category(fd) != "SINGLE_LINK":
                return {"status": "INITIAL_IDENTITY_REFUSED", "keeper": keeper}
            child = subprocess.Popen(
                [sys.executable, "-c", _CHILD, str(path), str(ready), str(release)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            deadline = time.monotonic() + 8
            while not ready.exists() and child.poll() is None:
                if time.monotonic() > deadline:
                    break
                time.sleep(0.01)
            if not ready.exists():
                return {"status": "CHILD_NOT_READY", "keeper": keeper}
            # In no-keeper mode, the child is the remaining SQLite client.
            if not keeper:
                connection.close()
                connection = None
            before = _descriptor_category(fd)
            release.touch()
            try:
                exit_code = child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                return {"status": "CHILD_TIMEOUT", "keeper": keeper}
            if exit_code != 0:
                return {"status": "CHILD_FAILED", "keeper": keeper}
            after_child = _descriptor_category(fd)
            after_child_name = _name_category(sidecar)
            if connection is not None:
                connection.close()
                connection = None
            after_final = _descriptor_category(fd)
            after_final_name = _name_category(sidecar)
            observed_normal_unlink = (
                before == "SINGLE_LINK"
                and after_final == "UNLINKED"
                and after_final_name == "ABSENT"
            )
            return {
                "status": "OK",
                "keeper": keeper,
                "before_child_close_fd": before,
                "after_child_close_fd": after_child,
                "after_child_close_name": after_child_name,
                "after_final_close_fd": after_final,
                "after_final_close_name": after_final_name,
                "normal_last_close_unlink_observed": observed_normal_unlink,
                "safety_checks_relaxed": False,
                "real_actions_executed": False,
                "private_paths_exported": False,
            }
        except (OSError, sqlite3.Error, ValueError):
            return {"status": "FIXTURE_ERROR", "keeper": keeper}
        finally:
            release.touch()
            if child is not None and child.poll() is None:
                child.kill()
                child.wait()
            if connection is not None:
                connection.close()
            if fd is not None:
                os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", default=1, type=_bounded_iterations)
    parser.add_argument("--keeper", action="store_true")
    args = parser.parse_args(argv)
    runs = [probe_disposable_last_close(keeper=args.keeper)
            for _ in range(args.iterations)]
    # No ephemeral path, row content, FD number or raw exception is emitted.
    report = {
        "schema_version": 1, "keeper": args.keeper,
        "iterations": args.iterations, "observations": runs,
        "automatic_retry_authorized": False,
        "tool_execution_authorized": False,
    }
    print(json.dumps(report, sort_keys=True, ensure_ascii=True))
    return 0 if all(item["status"] in ("OK", "UNSUPPORTED") for item in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
