"""Append-only local Planner journal with fail-closed deterministic recovery.

The journal stores only plan/step identities, state transitions and digests. It
never stores ToolCall arguments or tool results and never grants execution,
consent, trusted-time or automatic-replay authority.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .contracts import PlanConflictError, PlanStep, StepState
from .planner import PlanGraph

_SCHEMA_VERSION = 1
_MAX_SQLITE_INT = (1 << 63) - 1
_MAX_PLAN_ID_BYTES = 256
_MAX_STEP_ID_BYTES = 4096
_MAX_EVENTS = 100_000
_DOMAIN = b"ARK-planner-journal-v1\0"
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_TOPOLOGY = re.compile(r"plan_[0-9a-f]{64}\Z")
_STATUS = re.compile(r"pstate_[0-9a-f]{64}\Z")
_STATES = frozenset(state.value for state in StepState)
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps

_META_SQL = """
CREATE TABLE planner_journal_meta (
    plan_id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL CHECK(schema_version = 1),
    topology_digest TEXT NOT NULL CHECK(length(topology_digest) = 69),
    genesis_status_digest TEXT NOT NULL CHECK(length(genesis_status_digest) = 71),
    last_sequence INTEGER NOT NULL CHECK(last_sequence >= 0),
    last_event_hash TEXT NOT NULL CHECK(length(last_event_hash) = 64)
) STRICT
"""

_EVENTS_SQL = """
CREATE TABLE planner_journal_events (
    plan_id TEXT NOT NULL
        REFERENCES planner_journal_meta(plan_id) ON DELETE RESTRICT,
    sequence INTEGER NOT NULL CHECK(sequence BETWEEN 1 AND 9223372036854775807),
    step_id TEXT NOT NULL CHECK(length(step_id) BETWEEN 1 AND 4096),
    from_state TEXT NOT NULL
        CHECK(from_state IN ('pending', 'running', 'succeeded', 'failed', 'blocked', 'cancelled')),
    to_state TEXT NOT NULL
        CHECK(to_state IN ('pending', 'running', 'succeeded', 'failed', 'blocked', 'cancelled')),
    expected_revision INTEGER NOT NULL
        CHECK(expected_revision BETWEEN 0 AND 9223372036854775806),
    result_status_digest TEXT NOT NULL CHECK(length(result_status_digest) = 71),
    previous_event_hash TEXT NOT NULL CHECK(length(previous_event_hash) = 64),
    event_hash TEXT NOT NULL CHECK(length(event_hash) = 64),
    PRIMARY KEY(plan_id, sequence)
) STRICT
"""

_EXPECTED_SCHEMA = {
    "planner_journal_meta": _META_SQL,
    "planner_journal_events": _EVENTS_SQL,
}


class PlannerJournalError(RuntimeError):
    """Base class for local Planner journal failures."""


class PlannerJournalSchemaError(PlannerJournalError):
    """The journal schema or SQLite storage contract is not exact."""


class PlannerJournalCorruptError(PlannerJournalError):
    """Persisted journal rows, chain or replay state failed validation."""


class PlannerJournalConflictError(PlannerJournalError):
    """A stale graph, revision or sequence attempted to append a transition."""


class PlannerJournalNotFoundError(PlannerJournalError):
    """The requested plan has no journal genesis record."""


class PlannerJournalCommitUnknown(PlannerJournalError):
    """A SQLite COMMIT outcome is uncertain; callers must recover, never retry."""


@dataclass(frozen=True, slots=True)
class PlannerJournalReceipt:
    plan_id: str
    sequence: int
    topology_digest: str
    status_digest: str
    previous_event_hash: str
    event_hash: str
    step_id: str | None = None
    from_state: str | None = None
    to_state: str | None = None
    expected_revision: int | None = None

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PlannerJournalRecovery:
    plan_id: str
    graph: PlanGraph
    sequence: int
    last_event_hash: str
    ambiguous_running_step_ids: tuple[str, ...]

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class PlannerJournalTransition:
    graph: PlanGraph
    receipt: PlannerJournalReceipt

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _normalize_sql(value: str) -> str:
    return " ".join(value.lower().split())


def _require_digest_protocol() -> None:
    if hashlib.sha256 is not _ORIGINAL_SHA256 or json.dumps is not _ORIGINAL_DUMPS:
        raise PlannerJournalError("Planner journal digest dependencies changed")


def _canonical(payload: object) -> bytes:
    _require_digest_protocol()
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise PlannerJournalError("Planner journal payload is not canonical") from exc
    _require_digest_protocol()
    return encoded


def _digest(payload: object) -> str:
    _require_digest_protocol()
    value = hashlib.sha256(_DOMAIN + _canonical(payload)).hexdigest()
    _require_digest_protocol()
    return value


def _identity_text(value: object, label: str, maximum_bytes: int) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be an exact string")
    if not value or not value.strip():
        raise ValueError(f"{label} must be non-empty")
    if any(
        ord(character) < 32
        or 0x7F <= ord(character) <= 0x9F
        or ord(character) in (0x061C, 0x200E, 0x200F, 0x2028, 0x2029)
        or 0x202A <= ord(character) <= 0x202E
        or 0x2066 <= ord(character) <= 0x2069
        for character in value
    ):
        raise ValueError(f"{label} contains a control character")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8") from exc
    if size > maximum_bytes:
        raise ValueError(f"{label} exceeds its UTF-8 byte budget")
    return value


def _validate_plan_id(plan_id: object) -> str:
    return _identity_text(plan_id, "plan_id", _MAX_PLAN_ID_BYTES)


def _validate_graph(graph: object) -> tuple[tuple[PlanStep, ...], str, str]:
    if type(graph) is not PlanGraph:
        raise TypeError("graph must be an exact PlanGraph")
    steps = tuple(graph.steps.values())
    topology = graph.topology_digest()
    status = graph.status_digest()
    if graph.topology_digest() != topology or graph.status_digest() != status:
        raise PlannerJournalConflictError("PlanGraph changed during snapshot admission")
    if type(steps) is not tuple or not steps or any(type(step) is not PlanStep for step in steps):
        raise PlannerJournalConflictError("PlanGraph step snapshot is invalid")
    return steps, topology, status


def _validate_steps(steps: object) -> tuple[PlanStep, ...]:
    if type(steps) is not tuple or not steps or any(type(step) is not PlanStep for step in steps):
        raise TypeError("steps must be a non-empty tuple of exact PlanStep values")
    # PlanGraph performs the authoritative DAG, identity and resource admission.
    PlanGraph(steps)
    return steps


def _genesis_hash(plan_id: str, topology: str, status: str) -> str:
    return _digest(
        {
            "kind": "genesis",
            "schema_version": _SCHEMA_VERSION,
            "plan_id": plan_id,
            "topology_digest": topology,
            "initial_status_digest": status,
        }
    )


def _event_hash(
    *,
    plan_id: str,
    sequence: int,
    topology_digest: str,
    step_id: str,
    from_state: str,
    to_state: str,
    expected_revision: int,
    result_status_digest: str,
    previous_event_hash: str,
) -> str:
    return _digest(
        {
            "kind": "transition",
            "schema_version": _SCHEMA_VERSION,
            "plan_id": plan_id,
            "sequence": sequence,
            "topology_digest": topology_digest,
            "step_id": step_id,
            "from_state": from_state,
            "to_state": to_state,
            "expected_revision": expected_revision,
            "result_status_digest": result_status_digest,
            "previous_event_hash": previous_event_hash,
        }
    )


class PlannerJournal:
    """Append-only local journal; transition returns a new recovered PlanGraph.

    The caller must replace its prior graph with the returned graph after a
    successful transition. A failed or uncertain append never authorizes retry
    or external execution; recover the durable state and quarantine RUNNING
    steps whose external outcome cannot be established.
    """

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path) or type(path) is not type(Path(".")):
            raise TypeError("path must be a native pathlib Path")
        path_value = os.fspath(path)
        if type(path_value) is not str or not path_value or "\0" in path_value:
            raise ValueError("journal path is invalid")
        self._path = path_value
        self._bootstrap()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._path,
            timeout=10.0,
            isolation_level=None,
        )
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def _validate_schema(self, connection: sqlite3.Connection) -> None:
        version = connection.execute("PRAGMA user_version").fetchone()
        if (
            type(version) is not tuple
            or len(version) != 1
            or type(version[0]) is not int
            or version[0] != _SCHEMA_VERSION
        ):
            raise PlannerJournalSchemaError("Planner journal schema version is invalid")

        rows = connection.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        if any(type(row) is not tuple or len(row) != 3 for row in rows):
            raise PlannerJournalSchemaError("Planner journal schema catalog is malformed")
        if any(row[0] != "table" or type(row[1]) is not str or type(row[2]) is not str for row in rows):
            raise PlannerJournalSchemaError("unexpected Planner journal schema object")
        actual = {row[1]: row[2] for row in rows}
        if set(actual) != set(_EXPECTED_SCHEMA):
            raise PlannerJournalSchemaError("Planner journal managed tables changed")
        for name, expected_sql in _EXPECTED_SCHEMA.items():
            if _normalize_sql(actual[name]) != _normalize_sql(expected_sql):
                raise PlannerJournalSchemaError(f"Planner journal table changed: {name}")

    def _bootstrap(self) -> None:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            version_row = connection.execute("PRAGMA user_version").fetchone()
            if (
                type(version_row) is not tuple
                or len(version_row) != 1
                or type(version_row[0]) is not int
                or version_row[0] < 0
            ):
                raise PlannerJournalSchemaError("Planner journal user_version is invalid")
            if version_row[0] == 0:
                existing = connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    raise PlannerJournalSchemaError(
                        "unversioned Planner journal contains existing schema objects"
                    )
                connection.execute(_META_SQL)
                connection.execute(_EVENTS_SQL)
                connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")
            elif version_row[0] != _SCHEMA_VERSION:
                raise PlannerJournalSchemaError("unsupported Planner journal schema version")
            self._validate_schema(connection)
            try:
                connection.execute("COMMIT")
            except sqlite3.Error as exc:
                raise PlannerJournalCommitUnknown(
                    "Planner journal bootstrap COMMIT outcome is unknown"
                ) from exc
        except PlannerJournalCommitUnknown:
            raise
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _read_meta(
        self,
        connection: sqlite3.Connection,
        plan_id: str,
    ) -> tuple[int, str, str, int, str]:
        row = connection.execute(
            "SELECT schema_version, topology_digest, genesis_status_digest, "
            "last_sequence, last_event_hash FROM planner_journal_meta WHERE plan_id = ?",
            (plan_id,),
        ).fetchone()
        if row is None:
            raise PlannerJournalNotFoundError("Planner journal plan does not exist")
        if (
            type(row) is not tuple
            or len(row) != 5
            or type(row[0]) is not int
            or type(row[1]) is not str
            or type(row[2]) is not str
            or type(row[3]) is not int
            or type(row[4]) is not str
            or row[0] != _SCHEMA_VERSION
            or _TOPOLOGY.fullmatch(row[1]) is None
            or _STATUS.fullmatch(row[2]) is None
            or not 0 <= row[3] <= _MAX_EVENTS
            or _HASH.fullmatch(row[4]) is None
        ):
            raise PlannerJournalCorruptError("Planner journal metadata is malformed")
        return row

    def _read_events(
        self,
        connection: sqlite3.Connection,
        plan_id: str,
    ) -> list[tuple[object, ...]]:
        rows = connection.execute(
            "SELECT sequence, step_id, from_state, to_state, expected_revision, "
            "result_status_digest, previous_event_hash, event_hash "
            "FROM planner_journal_events WHERE plan_id = ? "
            "ORDER BY sequence LIMIT ?",
            (plan_id, _MAX_EVENTS + 1),
        ).fetchall()
        if len(rows) > _MAX_EVENTS:
            raise PlannerJournalCorruptError("Planner journal event budget exceeded")
        return rows

    def _replay(
        self,
        plan_id: str,
        steps: tuple[PlanStep, ...],
        meta: tuple[int, str, str, int, str],
        rows: list[tuple[object, ...]],
    ) -> tuple[PlanGraph, str]:
        _, topology, genesis_status, last_sequence, last_hash = meta
        try:
            graph = PlanGraph(steps)
            if graph.topology_digest() != topology:
                raise PlannerJournalCorruptError("Planner journal topology does not match")
            if graph.status_digest() != genesis_status:
                raise PlannerJournalCorruptError("Planner journal genesis status does not match")
            previous_hash = _genesis_hash(plan_id, topology, genesis_status)
            for expected_sequence, row in enumerate(rows, start=1):
                if type(row) is not tuple or len(row) != 8:
                    raise PlannerJournalCorruptError("Planner journal event row is malformed")
                (
                    sequence, step_id, from_state, to_state, expected_revision,
                    result_status, stored_previous, stored_hash,
                ) = row
                if (
                    type(sequence) is not int
                    or sequence != expected_sequence
                    or type(step_id) is not str
                    or not 1 <= len(step_id.encode("utf-8", errors="strict")) <= _MAX_STEP_ID_BYTES
                    or type(from_state) is not str
                    or from_state not in _STATES
                    or type(to_state) is not str
                    or to_state not in _STATES
                    or type(expected_revision) is not int
                    or not 0 <= expected_revision < _MAX_SQLITE_INT
                    or type(result_status) is not str
                    or _STATUS.fullmatch(result_status) is None
                    or type(stored_previous) is not str
                    or _HASH.fullmatch(stored_previous) is None
                    or type(stored_hash) is not str
                    or _HASH.fullmatch(stored_hash) is None
                ):
                    raise PlannerJournalCorruptError("Planner journal event fields are malformed")
                if stored_previous != previous_hash:
                    raise PlannerJournalCorruptError("Planner journal hash-chain predecessor changed")
                wanted_hash = _event_hash(
                    plan_id=plan_id,
                    sequence=sequence,
                    topology_digest=topology,
                    step_id=step_id,
                    from_state=from_state,
                    to_state=to_state,
                    expected_revision=expected_revision,
                    result_status_digest=result_status,
                    previous_event_hash=stored_previous,
                )
                if wanted_hash != stored_hash:
                    raise PlannerJournalCorruptError("Planner journal event digest mismatch")
                current = graph.statuses().get(step_id)
                if (
                    current is None
                    or current.state.value != from_state
                    or current.revision != expected_revision
                ):
                    raise PlannerJournalCorruptError("Planner journal transition prefix changed")
                try:
                    graph.transition(
                        step_id,
                        StepState(to_state),
                        expected_revision=expected_revision,
                    )
                except (PlanConflictError, KeyError, TypeError, ValueError) as exc:
                    raise PlannerJournalCorruptError(
                        "Planner journal transition cannot be replayed"
                    ) from exc
                if graph.status_digest() != result_status:
                    raise PlannerJournalCorruptError("Planner journal result status digest changed")
                previous_hash = stored_hash
        except PlannerJournalCorruptError:
            raise
        except Exception as exc:
            raise PlannerJournalCorruptError("Planner journal replay failed") from exc

        if last_sequence != len(rows) or last_hash != previous_hash:
            raise PlannerJournalCorruptError("Planner journal metadata frontier changed")
        return graph, previous_hash

    def create_plan(self, plan_id: str, graph: PlanGraph) -> PlannerJournalReceipt:
        plan_id = _validate_plan_id(plan_id)
        steps, topology, status = _validate_graph(graph)
        statuses = graph.statuses()
        if any(
            item.state is not StepState.PENDING or item.revision != 0
            for item in statuses.values()
        ):
            raise PlannerJournalConflictError("a new journal requires an all-PENDING genesis graph")
        genesis = _genesis_hash(plan_id, topology, status)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_schema(connection)
            exists = connection.execute(
                "SELECT 1 FROM planner_journal_meta WHERE plan_id = ?",
                (plan_id,),
            ).fetchone()
            if exists is not None:
                raise PlannerJournalConflictError("Planner journal plan already exists")
            connection.execute(
                "INSERT INTO planner_journal_meta "
                "(plan_id, schema_version, topology_digest, genesis_status_digest, "
                "last_sequence, last_event_hash) VALUES (?, ?, ?, ?, 0, ?)",
                (plan_id, _SCHEMA_VERSION, topology, status, genesis),
            )
            try:
                connection.execute("COMMIT")
            except sqlite3.Error as exc:
                raise PlannerJournalCommitUnknown(
                    "Planner journal genesis COMMIT outcome is unknown"
                ) from exc
        except PlannerJournalCommitUnknown:
            raise
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
        return PlannerJournalReceipt(
            plan_id=plan_id,
            sequence=0,
            topology_digest=topology,
            status_digest=status,
            previous_event_hash=genesis,
            event_hash=genesis,
        )

    def transition(
        self,
        plan_id: str,
        graph: PlanGraph,
        step_id: str,
        to_state: StepState,
        *,
        expected_revision: int,
        expected_sequence: int,
    ) -> PlannerJournalTransition:
        plan_id = _validate_plan_id(plan_id)
        _identity_text(step_id, "step_id", _MAX_STEP_ID_BYTES)
        if type(to_state) is not StepState:
            raise TypeError("to_state must be an exact StepState")
        if (
            type(expected_revision) is not int
            or not 0 <= expected_revision < _MAX_SQLITE_INT
        ):
            raise ValueError("expected_revision must be a non-negative SQLite integer")
        if (
            type(expected_sequence) is not int
            or not 0 <= expected_sequence < _MAX_EVENTS
        ):
            raise ValueError("expected_sequence is outside the journal event budget")
        steps, topology, supplied_status = _validate_graph(graph)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            self._validate_schema(connection)
            meta = self._read_meta(connection, plan_id)
            rows = self._read_events(connection, plan_id)
            replayed, previous_hash = self._replay(plan_id, steps, meta, rows)
            _, stored_topology, _, last_sequence, stored_hash = meta
            if topology != stored_topology:
                raise PlannerJournalConflictError("PlanGraph topology does not match journal")
            if supplied_status != replayed.status_digest():
                raise PlannerJournalConflictError("supplied PlanGraph is stale")
            if expected_sequence != last_sequence:
                raise PlannerJournalConflictError("Planner journal sequence compare-and-swap failed")
            if previous_hash != stored_hash:
                raise PlannerJournalCorruptError("Planner journal hash frontier changed")
            current = replayed.statuses().get(step_id)
            if current is None:
                raise PlannerJournalConflictError("step_id is not in the journaled plan")
            if current.revision != expected_revision:
                raise PlannerJournalConflictError("Planner step revision compare-and-swap failed")
            from_state = current.state.value
            try:
                replayed.transition(
                    step_id,
                    to_state,
                    expected_revision=expected_revision,
                )
            except (PlanConflictError, KeyError, TypeError, ValueError) as exc:
                raise PlannerJournalConflictError("Planner transition was rejected") from exc
            result_status = replayed.status_digest()
            sequence = last_sequence + 1
            event_hash = _event_hash(
                plan_id=plan_id,
                sequence=sequence,
                topology_digest=topology,
                step_id=step_id,
                from_state=from_state,
                to_state=to_state.value,
                expected_revision=expected_revision,
                result_status_digest=result_status,
                previous_event_hash=previous_hash,
            )
            connection.execute(
                "INSERT INTO planner_journal_events "
                "(plan_id, sequence, step_id, from_state, to_state, expected_revision, "
                "result_status_digest, previous_event_hash, event_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    plan_id, sequence, step_id, from_state, to_state.value,
                    expected_revision, result_status, previous_hash, event_hash,
                ),
            )
            updated = connection.execute(
                "UPDATE planner_journal_meta SET last_sequence = ?, last_event_hash = ? "
                "WHERE plan_id = ? AND last_sequence = ? AND last_event_hash = ? "
                "AND topology_digest = ?",
                (
                    sequence, event_hash, plan_id, last_sequence,
                    previous_hash, topology,
                ),
            )
            if updated.rowcount != 1:
                raise PlannerJournalConflictError("Planner journal frontier changed during append")
            try:
                connection.execute("COMMIT")
            except sqlite3.Error as exc:
                raise PlannerJournalCommitUnknown(
                    "Planner transition COMMIT outcome is unknown; recover before any retry"
                ) from exc
        except PlannerJournalCommitUnknown:
            raise
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

        receipt = PlannerJournalReceipt(
            plan_id=plan_id,
            sequence=sequence,
            topology_digest=topology,
            status_digest=result_status,
            previous_event_hash=previous_hash,
            event_hash=event_hash,
            step_id=step_id,
            from_state=from_state,
            to_state=to_state.value,
            expected_revision=expected_revision,
        )
        return PlannerJournalTransition(graph=replayed, receipt=receipt)

    def recover(
        self,
        plan_id: str,
        steps: tuple[PlanStep, ...],
    ) -> PlannerJournalRecovery:
        plan_id = _validate_plan_id(plan_id)
        steps = _validate_steps(steps)
        connection = self._connect()
        try:
            connection.execute("PRAGMA query_only = ON")
            connection.execute("BEGIN")
            self._validate_schema(connection)
            meta = self._read_meta(connection, plan_id)
            rows = self._read_events(connection, plan_id)
            graph, last_hash = self._replay(plan_id, steps, meta, rows)
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

        ambiguous = tuple(
            step_id
            for step_id, status in sorted(graph.statuses().items())
            if status.state is StepState.RUNNING
        )
        return PlannerJournalRecovery(
            plan_id=plan_id,
            graph=graph,
            sequence=meta[3],
            last_event_hash=last_hash,
            ambiguous_running_step_ids=ambiguous,
        )


__all__ = [
    "PlannerJournal",
    "PlannerJournalCommitUnknown",
    "PlannerJournalConflictError",
    "PlannerJournalCorruptError",
    "PlannerJournalError",
    "PlannerJournalNotFoundError",
    "PlannerJournalReceipt",
    "PlannerJournalRecovery",
    "PlannerJournalSchemaError",
    "PlannerJournalTransition",
]
