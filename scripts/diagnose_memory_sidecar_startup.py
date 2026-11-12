"""Disposable two-process SQLite Memory sidecar startup diagnostic.

Run from a checkout with ARK installed:
    python scripts/diagnose_memory_sidecar_startup.py --iterations 12

No real user databases, credentials, model files, services or paid compute.
Default sequential child bootstrap mirrors the historical CI CAS fixture;
--startup-mode concurrent separately probes simultaneous WAL initialization.
All writes are confined to an owned TemporaryDirectory. Only aggregate
statuses and path-free filesystem metadata are emitted. A reproduction is
NOT a reason to retry unsafe paths or weaken alias/sidecar checks.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

# Separate interpreters are essential: the SQLite bootstrap lock is
# process-local, and a same-process test would not reproduce that boundary.
_CHILD = r'''
import json
import pathlib
import re
import sys
import time

from ark.memory import (
    MemoryConflictError, MemorySchemaError, MemoryScope, MemoryWrite,
    SQLiteMemoryStore,
)

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
owner, namespace, source = sys.argv[4:7]
phase = "BOOTSTRAP"
try:
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    ready.touch()
    deadline = time.monotonic() + 12
    while not gate.exists():
        if time.monotonic() > deadline:
            raise TimeoutError("disposable fixture gate timed out")
        time.sleep(0.01)
    phase = "WRITE"
    try:
        store.put(
            MemoryWrite(MemoryScope(owner, namespace), source, "fixture"),
            expected_revision=0,
        )
    except MemoryConflictError:
        print(json.dumps({"status": "CONFLICT"}), flush=True)
    else:
        print(json.dumps({"status": "CREATED"}), flush=True)
except MemorySchemaError as exc:
    # Match only the new bounded metadata suffix. Never expose the pathname,
    # original message, traceback, row data or other runtime identifiers.
    evidence = re.search(
        r"\(suffix=(-wal|-shm|-journal), file_type=(0o[0-7]+), "
        r"link_count=([0-9]+)\)\Z", str(exc),
    )
    if evidence:
        print(json.dumps({
            "status": "SIDECAR_REJECTED", "phase": phase,
            "suffix": evidence.group(1),
            "file_type": evidence.group(2), "link_count": int(evidence.group(3)),
        }), flush=True)
    else:
        print(json.dumps({"status": "MEMORY_SCHEMA_REJECTED", "phase": phase}), flush=True)
except Exception as exc:
    print(json.dumps({"status": "OTHER_ERROR", "phase": phase,
                          "exception_type": type(exc).__name__}),
          flush=True)
'''


def _positive_bounded_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("iterations must be 1..30") from exc
    if not 1 <= value <= 30:
        raise argparse.ArgumentTypeError("iterations must be 1..30")
    return value


def _probe(
    path: Path, mode: str, startup_mode: str,
) -> list[dict[str, object]]:
    from ark.memory import SQLiteMemoryStore

    # The historical failing CI fixture serialized child *bootstrap* and
    # released two ready children together for competing CAS. Default to its
    # exact scheduling boundary; optional simultaneous bootstrap isolates the
    # more aggressive WAL initialization race separately.
    SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    gate = path.parent / "release"
    first = ("owner-a", "fixture", "source")
    second = {
        "same-identity": first,
        "separate-owner": ("owner-b", "fixture", "source"),
        "separate-namespace": ("owner-a", "other", "source"),
        "separate-source": ("owner-a", "fixture", "other"),
    }[mode]
    children: list[subprocess.Popen[str]] = []

    def ready(index: int) -> bool:
        return (path.parent / f"ready-{index}").exists()

    def await_ready(indices: range) -> bool:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            if all(ready(index) for index in indices):
                return True
            if any(children[index].poll() is not None for index in indices):
                return False
            time.sleep(0.01)
        return False

    try:
        for index, identity in enumerate((first, second)):
            children.append(subprocess.Popen(
                [sys.executable, "-c", _CHILD, str(path), str(gate),
                 str(path.parent / f"ready-{index}"), *identity],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            ))
            if startup_mode == "sequential" and not await_ready(range(index, index + 1)):
                break
        # A bootstrap refusal is an observed result, not a reason to retry.
        if startup_mode == "concurrent" and len(children) == 2:
            await_ready(range(2))
        gate.touch()
        results: list[dict[str, object]] = []
        for index, child in enumerate(children):
            try:
                output, _ = child.communicate(timeout=15)
                if child.returncode != 0:
                    item = {"status": "EXIT_FAILURE"}
                else:
                    item = json.loads(output)
                    if type(item) is not dict or type(item.get("status")) is not str:
                        item = {"status": "INVALID_CHILD_OUTPUT"}
                if not ready(index) and item["status"] in ("CREATED", "CONFLICT"):
                    item = {"status": "MISSING_READY_MARKER"}
                results.append(item)
            except (subprocess.TimeoutExpired, ValueError, TypeError):
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=_positive_bounded_int, default=4)
    parser.add_argument(
        "--mode", choices=("same-identity", "separate-owner",
                           "separate-namespace", "separate-source"),
        default="separate-owner",
    )
    parser.add_argument(
        "--startup-mode", choices=("sequential", "concurrent"),
        default="sequential",
    )
    args = parser.parse_args(argv)
    counts: Counter[str] = Counter()
    sidecar_evidence: list[dict[str, object]] = []
    unexpected = 0
    with tempfile.TemporaryDirectory(prefix="ark-disposable-memory-") as root:
        for attempt in range(args.iterations):
            case = Path(root) / f"case-{attempt}"
            case.mkdir()
            outcome = _probe(case / "memory.sqlite", args.mode, args.startup_mode)
            statuses = sorted(item["status"] for item in outcome)
            for item in outcome:
                counts[str(item["status"])] += 1
                if item["status"] == "SIDECAR_REJECTED":
                    sidecar_evidence.append(item)
            expected = (
                ["CONFLICT", "CREATED"] if args.mode == "same-identity"
                else ["CREATED", "CREATED"]
            )
            if statuses != expected:
                unexpected += 1
    print(json.dumps({
        "mode": args.mode, "startup_mode": args.startup_mode,
        "iterations": args.iterations,
        "status_counts": dict(sorted(counts.items())),
        "anomalous_iterations": unexpected,
        "sidecar_metadata_only": sidecar_evidence[:30],
        "private_paths_exported": False,
        "safety_checks_relaxed": False,
    }, ensure_ascii=True, sort_keys=True))
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
