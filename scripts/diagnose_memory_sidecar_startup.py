"""Disposable two-process SQLite Memory sidecar startup diagnostic.

Run from a checkout with ARK installed:
    python scripts/diagnose_memory_sidecar_startup.py --iterations 12

No real user databases, credentials, model files, services or paid compute.
Default sequential child bootstrap mirrors the historical CI CAS fixture;
--startup-mode concurrent separately probes simultaneous WAL initialization.
All writes are confined to an owned TemporaryDirectory. Optional real
--operation generation-cas performs lifetime-fenced updates, not creates.
Only aggregate
statuses and path-free filesystem metadata are emitted.
--wal-keeper is an explicit control that holds one read-only-in-effect SQLite
WAL connection open across child exits; it does not turn off any ARK path check. A reproduction is
NOT a reason to retry unsafe paths or weaken alias/sidecar checks.
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

from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASToken, MemoryGenerationCASRejected,
    generation_fenced_memory_update,
)

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
owner, namespace, source, operation, token_json = sys.argv[4:9]
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
        write = MemoryWrite(MemoryScope(owner, namespace), source, "fixture")
        if operation == "generation-cas":
            token = MemoryGenerationCASToken(*json.loads(token_json))
            generation_fenced_memory_update(store, write, retained=token)
        elif operation == "create":
            store.put(write, expected_revision=0)
        else:
            raise ValueError("unknown diagnostic operation")
    except (MemoryConflictError, MemoryGenerationCASRejected):
        print(json.dumps({"status": "CONFLICT"}), flush=True)
    else:
        status = "UPDATED" if operation == "generation-cas" else "CREATED"
        print(json.dumps({"status": status}), flush=True)
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


def _sanitize_child_reply(value: object) -> dict[str, object]:
    """Allowlist fixture subprocess output before it reaches aggregate reports.

    A child JSON payload is not trusted evidence. Never echo arbitrary keys,
    exception messages, private paths, traceback, or identity/token strings.
    """
    invalid = {"status": "INVALID_CHILD_OUTPUT"}
    if type(value) is not dict or type(value.get("status")) is not str:
        return invalid
    status = value["status"]
    if status in ("CREATED", "UPDATED", "CONFLICT"):
        return {"status": status} if set(value) == {"status"} else invalid
    if status in ("SIDECAR_REJECTED", "MEMORY_SCHEMA_REJECTED", "OTHER_ERROR"):
        if type(value.get("phase")) is not str or value["phase"] not in (
            "BOOTSTRAP", "WRITE",
        ):
            return invalid
        if status == "SIDECAR_REJECTED":
            if (
                set(value) != {
                    "status", "phase", "suffix", "file_type", "link_count",
                }
                or type(value.get("suffix")) is not str
                or value["suffix"] not in ("-wal", "-shm", "-journal")
                or type(value.get("file_type")) is not str
                or re.fullmatch(r"0o[0-7]{1,7}", value["file_type"]) is None
                or type(value.get("link_count")) is not int
                or not 0 <= value["link_count"] <= (1 << 63) - 1
            ):
                return invalid
        elif status == "MEMORY_SCHEMA_REJECTED":
            if set(value) != {"status", "phase"}:
                return invalid
        elif (
            set(value) != {"status", "phase", "exception_type"}
            or type(value.get("exception_type")) is not str
            or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", value["exception_type"])
            is None
        ):
            return invalid
        return dict(value)
    return invalid



def _no_duplicate_receipt_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse ambiguous JSON at every object depth, not just top-level keys."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate child receipt key")
        result[key] = value
    return result


def _no_nonfinite_receipt_number(_value: str) -> object:
    raise ValueError("nonfinite child receipt number")


def _parse_child_reply(output: str) -> dict[str, object]:
    """Reject equivocal/unbounded child JSON before applying the allowlist.

    json.loads normally takes the *last* duplicate key and accepts NaN.
    Neither may silently turn a failure receipt into CREATED/UPDATED. The
    raw child reply is never included in a diagnostic or exception message.
    """
    invalid = {"status": "INVALID_CHILD_OUTPUT"}
    if type(output) is not str or len(output) > 4096:
        return invalid
    try:
        decoded = json.loads(
            output,
            object_pairs_hook=_no_duplicate_receipt_keys,
            parse_constant=_no_nonfinite_receipt_number,
        )
    except (ValueError, TypeError, RecursionError):
        return invalid
    return _sanitize_child_reply(decoded)


def _probe(
    path: Path, mode: str, startup_mode: str, operation: str = "create",
    *, wal_keeper: bool = False,
) -> list[dict[str, object]]:
    from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
    from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas

    # The historical failing CI fixture serialized child *bootstrap* and
    # released two ready children together for competing CAS. Default to its
    # exact scheduling boundary; optional simultaneous bootstrap isolates the
    # more aggressive WAL initialization race separately.
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    gate = path.parent / "release"
    first = ("owner-a", "fixture", "source")
    second = {
        "same-identity": first,
        "separate-owner": ("owner-b", "fixture", "source"),
        "separate-namespace": ("owner-a", "other", "source"),
        "separate-source": ("owner-a", "fixture", "other"),
    }[mode]
    # Real CAS needs a preexisting row and its observed lifetime token.
    # Never include either token or private identity in the CLI output.
    tokens: dict[tuple[str, str, str], str] = {}
    if operation == "generation-cas":
        for owner, namespace, source in dict.fromkeys((first, second)):
            scope = MemoryScope(owner, namespace)
            store.put(MemoryWrite(scope, source, "before"))
            token = observe_memory_generation_for_cas(store, scope, source)
            tokens[(owner, namespace, source)] = json.dumps((
                token.memory_id, token.create_event_id, token.last_event_id,
                token.revision, token.event_prefix_sha256, token.row_sha256,
            ), separators=(",", ":"))
    elif operation != "create":
        raise ValueError("unknown disposable diagnostic operation")
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

    keeper: sqlite3.Connection | None = None
    try:
        # Diagnostic control only: preserve the WAL lifecycle across both
        # child processes, matching the stable-keeper regression fixture.
        # The default (no keeper) still exposes last-close sidecar races.
        if wal_keeper:
            keeper = sqlite3.connect(path)
            mode_row = keeper.execute("PRAGMA journal_mode").fetchone()
            if mode_row is None or mode_row[0].lower() != "wal":
                raise RuntimeError("disposable diagnostic WAL keeper unavailable")
        for index, identity in enumerate((first, second)):
            children.append(subprocess.Popen(
                [sys.executable, "-c", _CHILD, str(path), str(gate),
                 str(path.parent / f"ready-{index}"), *identity,
                 operation, tokens.get(identity, "null")],
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
                    # The subprocess is a diagnostic source, not a trusted
                    # serializer. Never forward unexpected JSON fields.
                    item = _parse_child_reply(output)
                if not ready(index) and item["status"] in (
                    "CREATED", "UPDATED", "CONFLICT",
                ):
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
        if keeper is not None:
            keeper.close()



def _verify_disposable_commit(path: Path, mode: str, operation: str) -> bool:
    """Read back child effects before calling a synthetic WAL probe clean.

    A child's CREATED/UPDATED JSON is untrusted. This read-only check uses
    only a disposable fixture path, verifies every row and append event, and
    never exports identity, content, paths or raw database error messages.
    It is NOT external-effect, clock, or authorization evidence.
    """
    from contextlib import closing

    from ark.memory import MemoryScope, deterministic_memory_id

    identities = {
        "same-identity": (("owner-a", "fixture", "source"),),
        "separate-owner": (
            ("owner-a", "fixture", "source"),
            ("owner-b", "fixture", "source"),
        ),
        "separate-namespace": (
            ("owner-a", "fixture", "source"),
            ("owner-a", "other", "source"),
        ),
        "separate-source": (
            ("owner-a", "fixture", "source"),
            ("owner-a", "fixture", "other"),
        ),
    }.get(mode)
    if (
        identities is None
        or operation not in ("create", "generation-cas")
        or not path.is_file()
        or path.is_symlink()
    ):
        return False

    expected_rows = []
    expected_events = []
    revision = 2 if operation == "generation-cas" else 1
    for owner, namespace, source in identities:
        memory_id = deterministic_memory_id(MemoryScope(owner, namespace), source)
        expected_rows.append(
            (memory_id, owner, namespace, source, "fixture", revision)
        )
        expected_events.append((memory_id, owner, namespace, "create", 1))
        if revision == 2:
            expected_events.append((memory_id, owner, namespace, "update", 2))
    try:
        # mode=ro prevents silently creating an empty database; explicit
        # close releases the disposable file handle on Windows.
        uri = path.absolute().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            conn.execute("PRAGMA query_only=ON")
            rows = conn.execute(
                "SELECT memory_id,owner_id,namespace,source_id,content,revision "
                "FROM memories"
            ).fetchall()
            events = conn.execute(
                "SELECT event_id,memory_id,owner_id,namespace,operation,revision "
                "FROM memory_events ORDER BY event_id"
            ).fetchall()
            highwater = conn.execute(
                "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
            ).fetchall()
    except (sqlite3.Error, OSError, ValueError):
        return False
    return (
        sorted(rows) == sorted(expected_rows)
        and sorted(event[1:] for event in events) == sorted(expected_events)
        and [event[0] for event in events] == list(range(1, len(expected_events) + 1))
        and highwater == [(len(expected_events),)]
    )


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
    parser.add_argument(
        "--operation", choices=("create", "generation-cas"),
        default="create",
    )
    parser.add_argument(
        "--wal-keeper", action="store_true",
        help="retain one disposable WAL connection across child execution",
    )
    args = parser.parse_args(argv)
    counts: Counter[str] = Counter()
    sidecar_evidence: list[dict[str, object]] = []
    unexpected = 0
    with tempfile.TemporaryDirectory(prefix="ark-disposable-memory-") as root:
        for attempt in range(args.iterations):
            case = Path(root) / f"case-{attempt}"
            case.mkdir()
            outcome = _probe(
                case / "memory.sqlite", args.mode, args.startup_mode, args.operation,
                wal_keeper=args.wal_keeper,
            )
            statuses = sorted(item["status"] for item in outcome)
            for item in outcome:
                counts[str(item["status"])] += 1
                if item["status"] == "SIDECAR_REJECTED":
                    sidecar_evidence.append(item)
            success = "UPDATED" if args.operation == "generation-cas" else "CREATED"
            expected = (
                ["CONFLICT", success] if args.mode == "same-identity"
                else [success, success]
            )
            if statuses != expected or not _verify_disposable_commit(
                case / "memory.sqlite", args.mode, args.operation,
            ):
                unexpected += 1
    print(json.dumps({
        "mode": args.mode, "startup_mode": args.startup_mode,
        "operation": args.operation, "wal_keeper": args.wal_keeper,
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
