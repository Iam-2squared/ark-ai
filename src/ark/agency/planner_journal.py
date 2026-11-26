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
import stat
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
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
# Retain the module objects and executable digest functions as one import-time
# epoch. Mutable module aliases must not jointly redefine the "original" pair.
_ORIGINAL_PLANNER_DIGEST_EPOCH = (
    _ORIGINAL_HASHLIB,
    _ORIGINAL_SHA256,
    _ORIGINAL_JSON,
    _ORIGINAL_DUMPS,
)
_ORIGINAL_STAT = stat
_ORIGINAL_S_ISDIR = stat.S_ISDIR
_ORIGINAL_S_ISLNK = stat.S_ISLNK
_ORIGINAL_S_ISREG = stat.S_ISREG

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


class PlannerJournalPathError(PlannerJournalError):
    """The local database path is missing, aliased or not a regular file."""


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


def _require_digest_protocol(
    *,
    _original_planner_digest_epoch: tuple[object, ...] = _ORIGINAL_PLANNER_DIGEST_EPOCH,
) -> None:
    if (
        _ORIGINAL_PLANNER_DIGEST_EPOCH is not _original_planner_digest_epoch
        or hashlib is not _original_planner_digest_epoch[0]
        or _ORIGINAL_HASHLIB is not _original_planner_digest_epoch[0]
        or hashlib.sha256 is not _original_planner_digest_epoch[1]
        or _ORIGINAL_SHA256 is not _original_planner_digest_epoch[1]
        or json is not _original_planner_digest_epoch[2]
        or _ORIGINAL_JSON is not _original_planner_digest_epoch[2]
        or json.dumps is not _original_planner_digest_epoch[3]
        or _ORIGINAL_DUMPS is not _original_planner_digest_epoch[3]
    ):
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


def _require_original_stat_policy(
    _stat=stat,
    _stat_isdir=stat.S_ISDIR,
    _stat_islnk=stat.S_ISLNK,
    _stat_isreg=stat.S_ISREG,
) -> None:
    """Reject substituted filesystem classifiers before path inspection."""
    # Retain the module and predicate objects outside mutable module aliases.
    # Replacing both stat references and all three comparison predicates must
    # not make the identity checks self-consistent with an attacker object.
    if (
        stat is not _stat
        or _ORIGINAL_STAT is not _stat
        or _ORIGINAL_S_ISDIR is not _stat_isdir
        or _ORIGINAL_S_ISLNK is not _stat_islnk
        or _ORIGINAL_S_ISREG is not _stat_isreg
        or _stat.S_ISDIR is not _stat_isdir
        or _stat.S_ISLNK is not _stat_islnk
        or _stat.S_ISREG is not _stat_isreg
    ):
        raise PlannerJournalPathError("Planner journal filesystem policy changed")


def _require_safe_journal_path(path: Path, *, create: bool) -> None:
    """Reject path aliases before SQLite can create, read or mutate a database.

    This is a repeated local lstat preflight, not atomic dirfd custody or
    protection against a hostile concurrent rename between inspection/open.
    """
    _require_original_stat_policy()
    if type(path) is not type(Path(".")) or ".." in path.parts:
        raise PlannerJournalPathError("Planner journal path type or traversal refused")
    raw = os.fspath(path)
    if type(raw) is not str or not path.name or "\0" in raw or len(raw) > 4096:
        raise PlannerJournalPathError("Planner journal path exceeds local limits")
    try:
        target = path if path.is_absolute() else path.absolute()
        if len(os.fsencode(target)) + len(b"-journal") > 4096:
            raise PlannerJournalPathError("Planner journal path/sidecar byte budget exceeded")
        for ancestor in target.parents:
            try:
                metadata = ancestor.lstat()
            except FileNotFoundError:
                _require_original_stat_policy()
                raise PlannerJournalPathError(
                    "Planner journal parent directory is unavailable"
                ) from None
            _require_original_stat_policy()
            mode = metadata.st_mode
            _require_original_stat_policy()
            is_directory = _ORIGINAL_S_ISDIR(mode)
            _require_original_stat_policy()
            is_symlink = _ORIGINAL_S_ISLNK(mode)
            _require_original_stat_policy()
            if not is_directory or is_symlink:
                raise PlannerJournalPathError(
                    "Planner journal symbolic or non-directory ancestor refused"
                )

        main_absent = False
        try:
            metadata = target.lstat()
        except FileNotFoundError:
            _require_original_stat_policy()
            main_absent = True
            if not create:
                raise PlannerJournalPathError(
                    "Planner journal database is unavailable; recreation is refused"
                ) from None
        else:
            _require_original_stat_policy()
            mode = metadata.st_mode
            _require_original_stat_policy()
            is_regular = _ORIGINAL_S_ISREG(mode)
            _require_original_stat_policy()
            is_symlink = _ORIGINAL_S_ISLNK(mode)
            _require_original_stat_policy()
            if not is_regular or is_symlink or metadata.st_nlink != 1:
                raise PlannerJournalPathError(
                    "Planner journal database must be one regular unaliased file"
                )

        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = target.with_name(target.name + suffix)
            try:
                sidecar_metadata = sidecar.lstat()
            except FileNotFoundError:
                _require_original_stat_policy()
                continue
            _require_original_stat_policy()
            if main_absent:
                raise PlannerJournalPathError(
                    "orphaned Planner journal SQLite sidecar refused"
                )
            mode = sidecar_metadata.st_mode
            _require_original_stat_policy()
            is_regular = _ORIGINAL_S_ISREG(mode)
            _require_original_stat_policy()
            is_symlink = _ORIGINAL_S_ISLNK(mode)
            _require_original_stat_policy()
            if is_regular and sidecar_metadata.st_nlink == 0:
                try:
                    sidecar_metadata = sidecar.lstat()
                except FileNotFoundError:
                    _require_original_stat_policy()
                    continue
                _require_original_stat_policy()
                mode = sidecar_metadata.st_mode
                _require_original_stat_policy()
                is_regular = _ORIGINAL_S_ISREG(mode)
                _require_original_stat_policy()
                is_symlink = _ORIGINAL_S_ISLNK(mode)
                _require_original_stat_policy()
            if (
                not is_regular
                or is_symlink
                or sidecar_metadata.st_nlink != 1
            ):
                raise PlannerJournalPathError(
                    "Planner journal SQLite sidecar must be one regular unaliased file"
                )
        _require_original_stat_policy()
    except PlannerJournalPathError:
        raise
    except (OSError, UnicodeError, ValueError) as exc:
        raise PlannerJournalPathError(
            "Planner journal path custody cannot be verified"
        ) from exc


class PlannerJournal:
    """Append-only local journal; transition returns a new recovered PlanGraph.

    The caller must replace its prior graph with the returned graph after a
    successful transition. A failed or uncertain append never authorizes retry
    or external execution; recover the durable state and quarantine RUNNING
    steps whose external outcome cannot be established.
    """

    # Keep __dict__ for existing fault-injection fixtures while making the
    # database path a non-shadowable data-descriptor slot.
    __slots__ = ("_path", "_path_identity", "__dict__")

    def __setattr__(self, name: str, value: object) -> None:
        if name in ("_path", "_path_identity"):
            raise AttributeError("Planner journal path identity is immutable")
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if name in ("_path", "_path_identity"):
            raise AttributeError("Planner journal path identity is immutable")
        object.__delattr__(self, name)

    def __init__(self, path: Path) -> None:
        if type(self) is not PlannerJournal:
            raise PlannerJournalPathError("exact PlannerJournal type required")
        if not isinstance(path, Path) or type(path) is not type(Path(".")):
            raise TypeError("path must be a native pathlib Path")
        path_value = os.fspath(path)
        if type(path_value) is not str or not path_value or "\0" in path_value:
            raise ValueError("journal path is invalid")
        if ".." in path.parts:
            raise PlannerJournalPathError("Planner journal path traversal refused")
        # Pin a lexical absolute path without resolving or following symlinks.
        source = os.fspath(path.absolute())
        object.__setattr__(self, "_path", source)
        object.__setattr__(self, "_path_identity", source)
        _require_planner_journal_path_epoch(self, source)
        _require_safe_journal_path(Path(source), create=True)
        self._bootstrap()

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        _require_planner_journal_path_epoch(self)
        path = Path(self._path)
        _require_safe_journal_path(path, create=create)
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                self._path,
                timeout=10.0,
                isolation_level=None,
            )
            # Recheck after open. This narrows, but does not eliminate, the
            # pathname TOCTOU window because sqlite3 does not expose its file
            # descriptor for an atomic no-follow identity comparison.
            _require_safe_journal_path(path, create=False)
        except Exception:
            if connection is not None:
                connection.close()
            raise
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
        if any(
            row[0] != "table" or type(row[1]) is not str or type(row[2]) is not str
            for row in rows
        ):
            raise PlannerJournalSchemaError("unexpected Planner journal schema object")
        actual = {row[1]: row[2] for row in rows}
        if set(actual) != set(_EXPECTED_SCHEMA):
            raise PlannerJournalSchemaError("Planner journal managed tables changed")
        for name, expected_sql in _EXPECTED_SCHEMA.items():
            if _normalize_sql(actual[name]) != _normalize_sql(expected_sql):
                raise PlannerJournalSchemaError(f"Planner journal table changed: {name}")

    def _bootstrap(self) -> None:
        _require_planner_journal_path_epoch(self)
        connection = self._connect(create=True)
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
                    raise PlannerJournalCorruptError(
                        "Planner journal hash-chain predecessor changed"
                    )
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
        _require_planner_journal_path_epoch(self)
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
        _require_planner_journal_path_epoch(self)
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
                raise PlannerJournalConflictError(
                    "Planner journal sequence compare-and-swap failed"
                )
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
        _require_planner_journal_path_epoch(self)
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



_PLANNER_JOURNAL_TYPE = PlannerJournal
_PLANNER_JOURNAL_SLOTS = vars(_PLANNER_JOURNAL_TYPE)["__slots__"]
_ORIGINAL_PLANNER_JOURNAL_INIT = vars(_PLANNER_JOURNAL_TYPE)["__init__"]
_ORIGINAL_PLANNER_JOURNAL_SETATTR = vars(_PLANNER_JOURNAL_TYPE)["__setattr__"]
_ORIGINAL_PLANNER_JOURNAL_DELATTR = vars(_PLANNER_JOURNAL_TYPE)["__delattr__"]
_ORIGINAL_PLANNER_JOURNAL_CONNECT = vars(_PLANNER_JOURNAL_TYPE)["_connect"]
_ORIGINAL_PLANNER_JOURNAL_BOOTSTRAP = vars(_PLANNER_JOURNAL_TYPE)["_bootstrap"]
_ORIGINAL_PLANNER_JOURNAL_VALIDATE_SCHEMA = vars(_PLANNER_JOURNAL_TYPE)["_validate_schema"]
_ORIGINAL_PLANNER_JOURNAL_READ_META = vars(_PLANNER_JOURNAL_TYPE)["_read_meta"]
_ORIGINAL_PLANNER_JOURNAL_READ_EVENTS = vars(_PLANNER_JOURNAL_TYPE)["_read_events"]
_ORIGINAL_PLANNER_JOURNAL_REPLAY = vars(_PLANNER_JOURNAL_TYPE)["_replay"]
_ORIGINAL_PLANNER_JOURNAL_CREATE_PLAN = vars(_PLANNER_JOURNAL_TYPE)["create_plan"]
_ORIGINAL_PLANNER_JOURNAL_TRANSITION = vars(_PLANNER_JOURNAL_TYPE)["transition"]
_ORIGINAL_PLANNER_JOURNAL_RECOVER = vars(_PLANNER_JOURNAL_TYPE)["recover"]
_PLANNER_JOURNAL_HOOK_NAMES = ("__getattribute__", "__getattr__")
_PLANNER_JOURNAL_HOOK_ABSENT = object()
_ORIGINAL_PLANNER_JOURNAL_HOOK_NAMES = _PLANNER_JOURNAL_HOOK_NAMES
_ORIGINAL_PLANNER_JOURNAL_HOOKS = tuple(
    vars(_PLANNER_JOURNAL_TYPE).get(name, _PLANNER_JOURNAL_HOOK_ABSENT)
    for name in _PLANNER_JOURNAL_HOOK_NAMES
)


def _require_planner_journal_path_epoch(
    journal: object,
    expected: str | None = None,
    *,
    _journal_type: type = _PLANNER_JOURNAL_TYPE,
    _hook_names: tuple[str, ...] = _PLANNER_JOURNAL_HOOK_NAMES,
    _hook_absent: object = _PLANNER_JOURNAL_HOOK_ABSENT,
    _original_hooks: tuple[object, ...] = _ORIGINAL_PLANNER_JOURNAL_HOOKS,
) -> str:
    """Reject a retargeted path or replaced class guard before SQLite access."""
    journal_namespace = vars(_journal_type)
    if (
        PlannerJournal is not _journal_type
        or _PLANNER_JOURNAL_TYPE is not _journal_type
        or type(journal) is not _journal_type
        or _PLANNER_JOURNAL_HOOK_NAMES is not _hook_names
        or _ORIGINAL_PLANNER_JOURNAL_HOOK_NAMES is not _hook_names
        or _PLANNER_JOURNAL_HOOK_ABSENT is not _hook_absent
        or _ORIGINAL_PLANNER_JOURNAL_HOOKS is not _original_hooks
        or journal_namespace.get("__slots__") is not _PLANNER_JOURNAL_SLOTS
        or journal_namespace.get("__init__") is not _ORIGINAL_PLANNER_JOURNAL_INIT
        or journal_namespace.get("__setattr__") is not _ORIGINAL_PLANNER_JOURNAL_SETATTR
        or journal_namespace.get("__delattr__") is not _ORIGINAL_PLANNER_JOURNAL_DELATTR
        or journal_namespace.get("_connect") is not _ORIGINAL_PLANNER_JOURNAL_CONNECT
        or journal_namespace.get("_bootstrap") is not _ORIGINAL_PLANNER_JOURNAL_BOOTSTRAP
        or (
            journal_namespace.get("_validate_schema")
            is not _ORIGINAL_PLANNER_JOURNAL_VALIDATE_SCHEMA
        )
        or journal_namespace.get("_read_meta") is not _ORIGINAL_PLANNER_JOURNAL_READ_META
        or (
            journal_namespace.get("_read_events")
            is not _ORIGINAL_PLANNER_JOURNAL_READ_EVENTS
        )
        or journal_namespace.get("_replay") is not _ORIGINAL_PLANNER_JOURNAL_REPLAY
        or (
            journal_namespace.get("create_plan")
            is not _ORIGINAL_PLANNER_JOURNAL_CREATE_PLAN
        )
        or journal_namespace.get("transition") is not _ORIGINAL_PLANNER_JOURNAL_TRANSITION
        or journal_namespace.get("recover") is not _ORIGINAL_PLANNER_JOURNAL_RECOVER
        or any(
            (name in journal_namespace) != (original is not _hook_absent)
            or (
                name in journal_namespace
                and journal_namespace[name] is not original
            )
            for name, original in zip(
                _hook_names,
                _original_hooks,
                strict=True,
            )
        )
    ):
        raise PlannerJournalPathError("Planner journal implementation changed")
    try:
        path = object.__getattribute__(journal, "_path")
        identity = object.__getattribute__(journal, "_path_identity")
        namespace = object.__getattribute__(journal, "__dict__")
    except (AttributeError, TypeError) as exc:
        raise PlannerJournalPathError("Planner journal path identity unavailable") from exc
    if (
        type(path) is not str
        or path is not identity
        or "_path" in namespace
        or "_path_identity" in namespace
        or (expected is not None and path is not expected)
    ):
        raise PlannerJournalPathError("Planner journal source identity changed")
    return path


__all__ = [
    "PlannerJournal",
    "PlannerJournalCommitUnknown",
    "PlannerJournalConflictError",
    "PlannerJournalCorruptError",
    "PlannerJournalError",
    "PlannerJournalNotFoundError",
    "PlannerJournalPathError",
    "PlannerJournalReceipt",
    "PlannerJournalRecovery",
    "PlannerJournalSchemaError",
    "PlannerJournalTransition",
]
