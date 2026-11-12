"""Two-process disposable SQLite action-audit WAL startup diagnostic.

Run explicitly from an installed ARK checkout:
    python scripts/diagnose_audit_sidecar_startup.py --iterations 4

Never opens a user database, invokes a backend, executes a real tool, deletes
evidence or retries an unsafe SQLite path. Diagnostic child receipts are NOT
consent, trustworthy timestamps, audited external actions or proof of cause.
A keeper option controls WAL last-connection lifetime without weakening guards.
Only bounded status and sidecar type/link metadata leave the fixture.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

_CHILD = r"""
import json
import pathlib
import re
import sys
import time

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ActionAuditSchemaError, ToolCall

path, gate, ready = map(pathlib.Path, sys.argv[1:4])
index = sys.argv[4]
phase = "BOOTSTRAP"
try:
    audit = SQLiteActionAudit(path, clock_ms=lambda: 2000)
    ready.touch()
    deadline = time.monotonic() + 15
    while not gate.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("disposable action audit gate expired")
        time.sleep(0.01)
    phase = "APPEND"
    audit.append(
        ToolCall("offline", "local.write", "synthetic", {"index": index}),
        outcome="synthetic_preaction_only",
    )
    print(json.dumps({"status": "AUDITED"}), flush=True)
except ActionAuditSchemaError as exc:
    evidence = re.search(
        r"\(suffix=(-wal|-shm|-journal), file_type=(0o[0-7]+), "
        r"link_count=([0-9]+)\)\Z", str(exc),
    )
    if evidence is None:
        result = {"status": "AUDIT_SCHEMA_REJECTED", "phase": phase}
    else:
        result = {
            "status": "SIDECAR_REJECTED", "phase": phase,
            "suffix": evidence.group(1),
            "file_type": evidence.group(2),
            "link_count": int(evidence.group(3)),
        }
    print(json.dumps(result), flush=True)
except Exception as exc:
    print(json.dumps({
        "status": "OTHER_ERROR", "phase": phase,
        "exception_type": type(exc).__name__,
    }), flush=True)
"""


def _positive_iterations(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("iterations must be 1..30") from exc
    if not 1 <= value <= 30:
        raise argparse.ArgumentTypeError("iterations must be 1..30")
    return value


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate audit diagnostic receipt key")
        result[name] = value
    return result


def _nonfinite(_token: str) -> object:
    raise ValueError("nonfinite audit diagnostic receipt")


def _parse_child_reply(value: object) -> dict[str, object]:
    invalid = {"status": "INVALID_CHILD_OUTPUT"}
    if type(value) is not str or not 0 < len(value) <= 4096:
        return invalid
    try:
        data = json.loads(
            value, object_pairs_hook=_unique, parse_constant=_nonfinite,
        )
    except (ValueError, TypeError, OverflowError, RecursionError):
        return invalid
    if type(data) is not dict or type(data.get("status")) is not str:
        return invalid
    status = data["status"]
    if status == "AUDITED":
        return {"status": status} if set(data) == {"status"} else invalid
    if status not in ("SIDECAR_REJECTED", "AUDIT_SCHEMA_REJECTED", "OTHER_ERROR"):
        return invalid
    if type(data.get("phase")) is not str or data["phase"] not in (
        "BOOTSTRAP", "APPEND",
    ):
        return invalid
    if status == "SIDECAR_REJECTED":
        if (
            set(data) != {"status", "phase", "suffix", "file_type", "link_count"}
            or type(data.get("suffix")) is not str
            or data["suffix"] not in ("-wal", "-shm", "-journal")
            or type(data.get("file_type")) is not str
            or re.fullmatch(r"0o[0-7]{1,7}", data["file_type"]) is None
            or type(data.get("link_count")) is not int
            or not 0 <= data["link_count"] <= (1 << 63) - 1
        ):
            return invalid
    elif status == "AUDIT_SCHEMA_REJECTED":
        if set(data) != {"status", "phase"}:
            return invalid
    elif (
        set(data) != {"status", "phase", "exception_type"}
        or type(data.get("exception_type")) is not str
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", data["exception_type"])
        is None
    ):
        return invalid
    return data


def _probe(path: Path, startup_mode: str, *, wal_keeper: bool = False) -> list[dict[str, object]]:
    from ark.agency.audit import SQLiteActionAudit

    SQLiteActionAudit(path, clock_ms=lambda: 1000)
    gate = path.parent / "release"
    children: list[subprocess.Popen[str]] = []
    keeper: sqlite3.Connection | None = None

    def ready(index: int) -> bool:
        return (path.parent / f"ready-{index}").exists()

    def await_ready(indices: range) -> bool:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if all(ready(i) for i in indices):
                return True
            if any(children[i].poll() is not None for i in indices):
                return False
            time.sleep(0.01)
        return False

    try:
        if wal_keeper:
            keeper = sqlite3.connect(path)
            mode = keeper.execute("PRAGMA journal_mode").fetchone()
            if mode is None or mode[0].lower() != "wal":
                raise RuntimeError("disposable WAL keeper unavailable")
        for index in range(2):
            children.append(subprocess.Popen(
                [sys.executable, "-c", _CHILD, str(path), str(gate),
                 str(path.parent / f"ready-{index}"), str(index)],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            ))
            if startup_mode == "sequential" and not await_ready(range(index, index + 1)):
                break
        if startup_mode == "concurrent" and len(children) == 2:
            await_ready(range(2))
        gate.touch()
        results: list[dict[str, object]] = []
        for index, child in enumerate(children):
            try:
                stdout, _ = child.communicate(timeout=20)
                item = (
                    _parse_child_reply(stdout)
                    if child.returncode == 0
                    else {"status": "EXIT_FAILURE"}
                )
                if item["status"] == "AUDITED" and not ready(index):
                    item = {"status": "MISSING_READY_MARKER"}
                results.append(item)
            except (subprocess.TimeoutExpired, TypeError, ValueError):
                child.kill()
                child.communicate()
                results.append({"status": "TIMEOUT_OR_INVALID_CHILD_OUTPUT"})
        return results
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
    parser.add_argument("--iterations", type=_positive_iterations, default=4)
    parser.add_argument(
        "--startup-mode", choices=("sequential", "concurrent"),
        default="sequential",
    )
    parser.add_argument("--wal-keeper", action="store_true")
    args = parser.parse_args(argv)
    counts: Counter[str] = Counter()
    details: list[dict[str, object]] = []
    anomalous = 0
    with tempfile.TemporaryDirectory(prefix="ark-disposable-audit-") as root:
        for index in range(args.iterations):
            case = Path(root) / f"case-{index}"
            case.mkdir()
            outcomes = _probe(
                case / "audit.sqlite", args.startup_mode,
                wal_keeper=args.wal_keeper,
            )
            for item in outcomes:
                counts[str(item["status"])] += 1
                if item["status"] == "SIDECAR_REJECTED":
                    details.append(item)
            if len(outcomes) != 2 or any(item["status"] != "AUDITED" for item in outcomes):
                anomalous += 1
            else:
                # This is a disposable SQLite count, not a proof of trusted
                # audit chronology or an externally executed side effect.
                with sqlite3.connect(case / "audit.sqlite") as conn:
                    events = conn.execute(
                        "SELECT event_id FROM action_events ORDER BY event_id"
                    ).fetchall()
                if events != [(1,), (2,)]:
                    anomalous += 1
    print(json.dumps({
        "startup_mode": args.startup_mode, "wal_keeper": args.wal_keeper,
        "iterations": args.iterations,
        "status_counts": dict(sorted(counts.items())),
        "anomalous_iterations": anomalous,
        "sidecar_metadata_only": details[:30],
        "private_paths_exported": False, "safety_checks_relaxed": False,
        "real_actions_executed": False,
    }, sort_keys=True, ensure_ascii=True))
    return 1 if anomalous else 0


if __name__ == "__main__":
    raise SystemExit(main())
