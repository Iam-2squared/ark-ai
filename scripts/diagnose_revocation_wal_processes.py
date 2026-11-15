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
import stat
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
# Independent diagnostic oracle for the frozen synthetic v1 schema. A table
# with the same name/autoindex but weakened NOT NULL constraints must NOT
# be accepted as a durable veto merely because the one expected row exists.
_EXPECTED_DDL = """CREATE TABLE synthetic_context_revocations(
    scope_digest TEXT PRIMARY KEY NOT NULL,
    revoked_at_ms INTEGER NOT NULL
)"""

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
        # A child cannot report a completed (or duplicate) revocation before
        # it crossed its synthetic REVOKE gate. Treat such a reply as invalid
        # even when both scalar fields have otherwise recognized values.
        or (
            decoded["status"] in {"REVOKED", "ALREADY"}
            and decoded["phase"] != "REVOKE"
        )
    ):
        return invalid
    return decoded


def _sidecars_are_single_link_files(path: Path) -> bool:
    """Refuse synthetic WAL/SHM aliases before and after independent readback.

    Sidecars may legitimately appear or disappear as SQLite readers close;
    their pathname presence is not itself evidence of a durable veto. This
    is deliberately only lexical/path preflight, not atomic handle custody.
    """
    try:
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = path.with_name(path.name + suffix)
            try:
                metadata = sidecar.lstat()
            except FileNotFoundError:
                continue
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
                return False
    except (OSError, ValueError):
        return False
    return True


def _verify_row(path: Path) -> bool:
    """Independent read-only verification; a child's status is not proof."""
    # Only two rows, three catalog objects and two quick-check messages
    # are sufficient to disprove this disposable one-row/two-object claim.
    # Never hydrate an unbounded foreign SQLite catalog into diagnostics.
    try:
        # Refuse a hard-linked synthetic ledger, not just a symlink. A matching
        # row in an aliased file is not custody of this disposable case.
        # These path probes are intentionally NOT atomic open-handle identity.
        initial = path.lstat()
        if (
            not stat.S_ISREG(initial.st_mode)
            or initial.st_nlink != 1
            or not _sidecars_are_single_link_files(path)
        ):
            return False
        with closing(sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)) as conn:
            conn.execute("PRAGMA query_only=ON")
            conn.execute("BEGIN")
            version = conn.execute("PRAGMA user_version").fetchone()
            rows = conn.execute(
                "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
            ).fetchmany(2)
            objects = conn.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
            ).fetchmany(3)
            check = conn.execute("PRAGMA quick_check").fetchmany(2)
        # A different pathname target after verification must not be
        # reported as the same durable veto. This does not resolve races
        # where the pathname is replaced and restored between inspections.
        final = path.lstat()
        if (
            not stat.S_ISREG(final.st_mode)
            or final.st_nlink != 1
            or (initial.st_dev, initial.st_ino) != (final.st_dev, final.st_ino)
            or not _sidecars_are_single_link_files(path)
        ):
            return False
        return (
            version == (1,)
            and rows == [(_SCOPE_DIGEST, 2000)]
            and objects == [
                ("index", "sqlite_autoindex_synthetic_context_revocations_1",
                 "synthetic_context_revocations", None),
                ("table", "synthetic_context_revocations",
                 "synthetic_context_revocations", _EXPECTED_DDL),
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



def _admit_probe_result(result: object) -> tuple[list[dict[str, str]], bool]:
    """Bound every diagnostic aggregation key, even if a probe is substituted.

    Raw child replies pass through _parse_reply, but a diagnostic hook can
    replace the whole probe result. Never echo arbitrary path/private text as
    a Counter key or mistake an integer truth value for durable evidence.
    This is a synthetic diagnostics guard, NOT an authenticated readback.
    """
    invalid = {"status": "INVALID_REPLY", "phase": "UNKNOWN"}
    if type(result) is not tuple or len(result) != 2:
        return [invalid.copy(), invalid.copy()], False
    replies, durable = result
    if type(replies) is not list or len(replies) != 2:
        return [invalid.copy(), invalid.copy()], False
    admitted: list[dict[str, str]] = []
    for reply in replies:
        if (
            type(reply) is not dict
            or len(reply) != 2
            or any(type(key) is not str for key in reply)
            or set(reply) != {"status", "phase"}
        ):
            admitted.append(invalid.copy())
            continue
        status, phase = reply["status"], reply["phase"]
        if (
            type(status) is not str
            or type(phase) is not str
            or status not in _ALLOWED
            or (
                status in {"REVOKED", "ALREADY"} and phase != "REVOKE"
            )
            or (
                status in {"SIDECAR_REFUSED", "OTHER_DENIAL", "OTHER_ERROR"}
                and phase not in {"BOOTSTRAP", "REVOKE"}
            )
            or (
                status in {"EXIT_FAILURE", "TIMEOUT", "INVALID_REPLY"}
                and phase != "UNKNOWN"
            )
        ):
            admitted.append(invalid.copy())
        else:
            admitted.append({"status": status, "phase": phase})
    return admitted, durable if type(durable) is bool else False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=_iterations, default=4)
    parser.add_argument("--wal-keeper", action="store_true")
    options = parser.parse_args(argv)
    counts: Counter[str] = Counter()
    # Phase-labelled aggregates distinguish an unsafe bootstrap/open from
    # denial after the child crossed its synthetic revocation gate. The
    # report never includes private paths, raw stderr or child payloads.
    phase_counts: Counter[str] = Counter()
    # A durable veto can coexist with a losing process that refused at the
    # WAL/SHM gate. Keep only bounded phase/status *categories*, never child
    # payloads, exception texts, paths or personal scope identifiers. This
    # distinguishes durable-but-ambiguous from absent readback evidence.
    durable_ambiguous_patterns: Counter[str] = Counter()
    unverified_patterns: Counter[str] = Counter()
    durable_verified = 0
    durable_ambiguous = 0
    anomalies = 0
    with tempfile.TemporaryDirectory(prefix="ark-disposable-revocation-") as directory:
        for index in range(options.iterations):
            case = Path(directory) / f"case-{index}"
            case.mkdir()
            replies, durable = _admit_probe_result(_probe(
                case / "revocation.sqlite", wal_keeper=options.wal_keeper,
            ))
            for reply in replies:
                counts[reply["status"]] += 1
                phase_counts[f'{reply["phase"]}:{reply["status"]}'] += 1
            expected = sorted(item["status"] for item in replies) == [
                "ALREADY", "REVOKED",
            ]
            # Only a pair of fixed allowlisted child status/phase labels can
            # enter this aggregate; there is no user/path-derived dimension.
            pattern = " + ".join(sorted(
                f'{item["phase"]}:{item["status"]}' for item in replies
            ))
            if durable:
                durable_verified += 1
                if not expected:
                    durable_ambiguous += 1
                    durable_ambiguous_patterns[pattern] += 1
            else:
                unverified_patterns[pattern] += 1
            if not expected or not durable:
                anomalies += 1
    print(json.dumps({
        "iterations": options.iterations,
        "wal_keeper": options.wal_keeper,
        "status_counts": dict(sorted(counts.items())),
        "status_phase_counts": dict(sorted(phase_counts.items())),
        "durable_verified_iterations": durable_verified,
        "durable_with_ambiguous_reply_iterations": durable_ambiguous,
        "durable_ambiguous_phase_patterns": dict(sorted(
            durable_ambiguous_patterns.items()
        )),
        "unverified_phase_patterns": dict(sorted(unverified_patterns.items())),
        "anomalous_iterations": anomalies,
        "private_paths_exported": False,
        "safety_checks_relaxed": False,
        "automatic_retry": False,
    }, sort_keys=True))
    return 1 if anomalies else 0


if __name__ == "__main__":
    raise SystemExit(main())
