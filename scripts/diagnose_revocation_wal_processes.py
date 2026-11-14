"""Disposable two-process revocation/WAL last-close diagnostic.

This deliberately uses a fresh TemporaryDirectory, a synthetic scope, and
bounded aggregate outcomes. It never retries a refused sidecar, changes a
privacy fence, authenticates consent, or touches a real user database.

Run explicitly: python scripts/diagnose_revocation_wal_processes.py --iterations 4
Use --wal-keeper to compare with a connection held open through both children.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections import Counter
from contextlib import closing
from pathlib import Path

_SCOPE_DIGEST = hashlib.sha256(
    b"ARK-context-revocation-scope-v1\0"
    + b'["synthetic-diagnostic","profile"]'
).hexdigest()

_CHILD = r"""
import json
import pathlib
import sys
import time
from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger, SyntheticContextRevocationRejected,
)

path, gate, ready = map(pathlib.Path, sys.argv[1:4])
phase = "BOOTSTRAP"
try:
    ledger = SyntheticContextRevocationLedger(path, require_existing=True)
    ready.touch()
    deadline = time.monotonic() + 12
    while not gate.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("diagnostic gate expired")
        time.sleep(0.01)
    phase = "REVOKE"
    try:
        ledger.revoke(MemoryScope("synthetic-diagnostic", "profile"), at_ms=2000)
    except SyntheticContextRevocationRejected as exc:
        message = str(exc)
        if message == "scope already revoked":
            status = "ALREADY"
        elif message == "unsafe revocation SQLite sidecar":
            status = "SIDECAR_REFUSED"
        else:
            status = "OTHER_DENIAL"
    else:
        status = "REVOKED"
except SyntheticContextRevocationRejected as exc:
    status = (
        "SIDECAR_REFUSED"
        if str(exc) == "unsafe revocation SQLite sidecar"
        else "OTHER_DENIAL"
    )
except Exception:
    status = "OTHER_ERROR"
print(json.dumps({"status": status, "phase": phase}), flush=True)
"""

_ALLOWED = frozenset({
    "REVOKED", "ALREADY", "SIDECAR_REFUSED", "OTHER_DENIAL", "OTHER_ERROR",
    "EXIT_FAILURE", "TIMEOUT", "INVALID_REPLY",
})


def _iterations(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("iterations must be 1..12") from exc
    if not 1 <= parsed <= 12:
        raise argparse.ArgumentTypeError("iterations must be 1..12")
    return parsed


def _pairs_unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous diagnostic reply")
        result[key] = value
    return result


def _reject_nonfinite(_value: str) -> object:
    raise ValueError("nonfinite diagnostic reply")


def _parse_reply(output: str) -> dict[str, str]:
    invalid = {"status": "INVALID_REPLY", "phase": "UNKNOWN"}
    if type(output) is not str or len(output) > 512:
        return invalid
    try:
        decoded = json.loads(
            output, object_pairs_hook=_pairs_unique,
            parse_constant=_reject_nonfinite,
        )
    except (ValueError, TypeError, RecursionError):
        return invalid
    if (
        type(decoded) is not dict
        or set(decoded) != {"status", "phase"}
        or type(decoded["status"]) is not str
        or type(decoded["phase"]) is not str
        or decoded["status"] not in _ALLOWED
        or decoded["status"] in {"EXIT_FAILURE", "TIMEOUT", "INVALID_REPLY"}
        or decoded["phase"] not in {"BOOTSTRAP", "REVOKE"}
    ):
        return invalid
    return decoded


def _verify_row(path: Path) -> bool:
    """Independent read-only verification; a child's status is not proof."""
    if path.is_symlink() or not path.is_file():
        return False
    try:
        with closing(sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)) as conn:
            conn.execute("PRAGMA query_only=ON")
            conn.execute("BEGIN")
            version = conn.execute("PRAGMA user_version").fetchone()
            rows = conn.execute(
                "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
            ).fetchall()
            objects = conn.execute(
                "SELECT type,name,tbl_name FROM sqlite_master ORDER BY type,name"
            ).fetchall()
            check = conn.execute("PRAGMA quick_check").fetchall()
        return (
            version == (1,)
            and rows == [(_SCOPE_DIGEST, 2000)]
            and objects == [
                ("index", "sqlite_autoindex_synthetic_context_revocations_1",
                 "synthetic_context_revocations"),
                ("table", "synthetic_context_revocations",
                 "synthetic_context_revocations"),
            ]
            and check == [("ok",)]
        )
    except (sqlite3.Error, OSError, TypeError, ValueError):
        return False


def _probe(path: Path, *, wal_keeper: bool = False) -> tuple[list[dict[str, str]], bool]:
    from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

    SyntheticContextRevocationLedger(path)
    with closing(sqlite3.connect(path)) as setup:
        if setup.execute("PRAGMA journal_mode=WAL").fetchone() != ("wal",):
            raise RuntimeError("disposable WAL unavailable")
    gate = path.parent / "release"
    keeper: sqlite3.Connection | None = None
    children: list[subprocess.Popen[str]] = []
    try:
        if wal_keeper:
            keeper = sqlite3.connect(path)
            if keeper.execute("PRAGMA journal_mode").fetchone() != ("wal",):
                raise RuntimeError("disposable WAL keeper unavailable")
            # Keep a true WAL reader snapshot alive through both revocation
            # process exits. This is a controlled disposable lifecycle fixture,
            # not proof of consent, external deletion or authorized replay.
            keeper.execute("BEGIN")
            keeper.execute(
                "SELECT COUNT(*) FROM synthetic_context_revocations"
            ).fetchone()
        for index in range(2):
            children.append(subprocess.Popen(
                [
                    sys.executable, "-c", _CHILD, str(path), str(gate),
                    str(path.parent / f"ready-{index}"),
                ],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            ))
            deadline = time.monotonic() + 12
            marker = path.parent / f"ready-{index}"
            while not marker.exists() and children[index].poll() is None:
                if time.monotonic() > deadline:
                    break
                time.sleep(0.01)
        gate.touch()
        replies: list[dict[str, str]] = []
        for child in children:
            try:
                stdout, _ = child.communicate(timeout=18)
                replies.append(
                    _parse_reply(stdout)
                    if child.returncode == 0
                    else {"status": "EXIT_FAILURE", "phase": "UNKNOWN"}
                )
            except subprocess.TimeoutExpired:
                child.kill()
                child.communicate()
                replies.append({"status": "TIMEOUT", "phase": "UNKNOWN"})
        return replies, _verify_row(path)
    finally:
        gate.touch()
        for child in children:
            if child.poll() is None:
                child.kill()
                child.communicate()
        if keeper is not None:
            keeper.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=_iterations, default=4)
    parser.add_argument("--wal-keeper", action="store_true")
    options = parser.parse_args(argv)
    counts: Counter[str] = Counter()
    anomalies = 0
    with tempfile.TemporaryDirectory(prefix="ark-disposable-revocation-") as directory:
        for index in range(options.iterations):
            case = Path(directory) / f"case-{index}"
            case.mkdir()
            replies, durable = _probe(
                case / "revocation.sqlite", wal_keeper=options.wal_keeper,
            )
            for reply in replies:
                counts[reply["status"]] += 1
            if sorted(item["status"] for item in replies) != ["ALREADY", "REVOKED"] or not durable:
                anomalies += 1
    print(json.dumps({
        "iterations": options.iterations,
        "wal_keeper": options.wal_keeper,
        "status_counts": dict(sorted(counts.items())),
        "anomalous_iterations": anomalies,
        "private_paths_exported": False,
        "safety_checks_relaxed": False,
        "automatic_retry": False,
    }, sort_keys=True))
    return 1 if anomalies else 0


if __name__ == "__main__":
    raise SystemExit(main())
