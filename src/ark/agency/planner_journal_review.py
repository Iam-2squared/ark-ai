"""Disconnected, replay-only SQLite journal for synthetic PlanGraph transitions.

This is a fixture, NOT execution authority. Callers provide the clock and
topology. A recovered RUNNING step is UNKNOWN, never an instruction to retry.
A matching internal tail is not independent evidence against coordinated
rewrites; callers must retain an earlier tail outside this SQLite database.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import PlanConflictError, PlanStep, StepState
from .planner import PlanGraph

_MAX_INT = 2**63 - 1
_MAX_EVENTS = 10_000
_HEX = re.compile(r"pevt_[0-9a-f]{64}\Z")
_PLAN = re.compile(r"plan_[0-9a-f]{64}\Z")
_STATE = re.compile(r"pstate_[0-9a-f]{64}\Z")
_SCHEMA = (
    """CREATE TABLE synthetic_plan_header(
        id INTEGER PRIMARY KEY CHECK(id = 1),
        topology_digest TEXT NOT NULL,
        initial_status_digest TEXT NOT NULL,
        event_count INTEGER NOT NULL,
        tail_hash TEXT NOT NULL,
        status_digest TEXT NOT NULL,
        last_at_ms INTEGER NOT NULL
    )""",
    """CREATE TABLE synthetic_plan_events(
        seq INTEGER PRIMARY KEY CHECK(seq >= 1),
        step_id TEXT NOT NULL,
        from_state TEXT NOT NULL,
        to_state TEXT NOT NULL,
        expected_revision INTEGER NOT NULL,
        resulting_revision INTEGER NOT NULL,
        occurred_at_ms INTEGER NOT NULL,
        post_status_digest TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        event_hash TEXT NOT NULL
    )""",
)
_HEADER = """SELECT topology_digest,initial_status_digest,event_count,
                    tail_hash,status_digest,last_at_ms
             FROM synthetic_plan_header"""
_EVENTS = """SELECT seq,step_id,from_state,to_state,expected_revision,
                    resulting_revision,occurred_at_ms,post_status_digest,
                    previous_hash,event_hash
             FROM synthetic_plan_events ORDER BY seq"""


class SyntheticPlanJournalRejected(RuntimeError):
    """The fixture journal cannot establish coherent replay evidence."""


def _hash(label: str, payload: object) -> str:
    data = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "pevt_" + hashlib.sha256(label.encode("utf-8") + b"\0" + data).hexdigest()


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        )
    )


def _schema_check(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticPlanJournalRejected("synthetic plan schema version changed")
    # Bound SQLite metadata inside the caller's existing replay/append
    # transaction before hydrating any untrusted DDL into Python.
    budget = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int or budget[0] != 2
        or type(budget[1]) is not int or not 0 <= budget[1] <= 4_096
    ):
        raise SyntheticPlanJournalRejected(
            "synthetic plan schema changed: preflight budget exceeded"
        )
    with sqlite3.connect(":memory:") as expected:
        for ddl in _SCHEMA:
            expected.execute(ddl)
        if _objects(conn) != _objects(expected):
            raise SyntheticPlanJournalRejected("synthetic plan schema changed")
    # A malformed journal can yield many SQLite corruption diagnostics.
    # Only one exact "ok" is accepted; two rows detect extra output without
    # hydrating an unbounded diagnostic stream into Python.
    quick = conn.execute("PRAGMA quick_check").fetchmany(2)
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise SyntheticPlanJournalRejected("synthetic plan quick_check failed")


@dataclass(frozen=True, slots=True)
class SyntheticPlanTail:
    topology_digest: str
    event_count: int
    event_hash: str
    status_digest: str
    last_at_ms: int

    def assert_shape(self) -> None:
        if (
            type(self.topology_digest) is not str
            or not _PLAN.fullmatch(self.topology_digest)
            or type(self.event_count) is not int
            or not 0 <= self.event_count <= _MAX_EVENTS
            or type(self.event_hash) is not str
            or not _HEX.fullmatch(self.event_hash)
            or type(self.status_digest) is not str
            or not _STATE.fullmatch(self.status_digest)
            or type(self.last_at_ms) is not int
            or not -1 <= self.last_at_ms <= _MAX_INT
            or (self.event_count == 0) != (self.last_at_ms == -1)
        ):
            raise SyntheticPlanJournalRejected("retained synthetic plan tail is malformed")


@dataclass(frozen=True, slots=True)
class SyntheticPlanRecovery:
    tail: SyntheticPlanTail
    step_statuses: tuple[tuple[str, str, int], ...]
    ambiguous_running_steps: tuple[str, ...]

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


def _retained_tail_epoch_stable(
    tail: SyntheticPlanTail, original: tuple[object, ...],
) -> bool:
    """Reject equal-valued substitution of a retained evidence carrier.

    These synthetic witnesses are never permission to dispatch or retry.
    """
    current = (
        tail.topology_digest, tail.event_count, tail.event_hash,
        tail.status_digest, tail.last_at_ms,
    )
    return (
        current == original
        and all(
            value is prior for value, prior in zip(current, original, strict=True)
        )
    )


def _snapshot(graph: PlanGraph, tail: SyntheticPlanTail) -> SyntheticPlanRecovery:
    states = graph.statuses()
    statuses = tuple(
        (name, state.state.value, state.revision)
        for name, state in sorted(states.items())
    )
    running = tuple(
        name for name, state, _revision in statuses if state == StepState.RUNNING.value
    )
    return SyntheticPlanRecovery(tail, statuses, running)


# This recovery object is an inert witness, never an authorization. Pin its
# original class even if a synthetic test hook later replaces the constructor.
_RECOVERY_RESULT_TYPE = SyntheticPlanRecovery
# A frozen slotted *tail* is also executable when its class-level field or
# lookup descriptors are replaced. Pin it before any retained-tail field read,
# SQLite replay or synthetic result-constructor callback.
_TAIL_RESULT_TYPE = SyntheticPlanTail
_TAIL_FIELDS = (
    "topology_digest", "event_count", "event_hash", "status_digest", "last_at_ms",
)
# assert_shape is invoked on a caller-retained witness; a class method
# substituted between topology/replay callbacks and validation must never run.
_TAIL_HOOKS = (
    "__init__", "__new__", "__getattribute__", "__getattr__", "assert_shape",
)
_ORIGINAL_TAIL_FIELDS = tuple(vars(_TAIL_RESULT_TYPE)[name] for name in _TAIL_FIELDS)
_ORIGINAL_TAIL_HOOKS = tuple(
    vars(_TAIL_RESULT_TYPE).get(name) for name in _TAIL_HOOKS
)
_ORIGINAL_RECOVERY_INIT = vars(_RECOVERY_RESULT_TYPE)["__init__"]
_RECOVERY_DENIAL_NAMES = ("dispatch_authorized", "automatic_replay_authorized")
_ORIGINAL_RECOVERY_DENIALS = tuple(
    vars(_RECOVERY_RESULT_TYPE)[name] for name in _RECOVERY_DENIAL_NAMES
)
# A frozen dataclass still permits class-level replacement of a member slot,
# __getattribute__, __getattr__, or constructor. Those are executable before
# a post-hoc False-only getter or digest would reject the resulting witness.
_RECOVERY_FIELDS = ("tail", "step_statuses", "ambiguous_running_steps")
_RECOVERY_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RECOVERY_FIELDS = tuple(
    vars(_RECOVERY_RESULT_TYPE)[name] for name in _RECOVERY_FIELDS
)
_ORIGINAL_RECOVERY_HOOKS = tuple(
    vars(_RECOVERY_RESULT_TYPE).get(name) for name in _RECOVERY_HOOKS
)


def _require_original_recovery_denials() -> None:
    if (
        SyntheticPlanTail is not _TAIL_RESULT_TYPE
        or any(
            vars(_TAIL_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _TAIL_FIELDS, _ORIGINAL_TAIL_FIELDS, strict=True,
            )
        )
        or any(
            vars(_TAIL_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _TAIL_HOOKS, _ORIGINAL_TAIL_HOOKS, strict=True,
            )
        )
        or SyntheticPlanRecovery is not _RECOVERY_RESULT_TYPE
        or vars(_RECOVERY_RESULT_TYPE).get("__init__") is not _ORIGINAL_RECOVERY_INIT
        or any(
            vars(_RECOVERY_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RECOVERY_FIELDS, _ORIGINAL_RECOVERY_FIELDS, strict=True,
            )
        )
        or any(
            vars(_RECOVERY_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RECOVERY_HOOKS, _ORIGINAL_RECOVERY_HOOKS, strict=True,
            )
        )
        or any(
            vars(_RECOVERY_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _RECOVERY_DENIAL_NAMES, _ORIGINAL_RECOVERY_DENIALS, strict=True,
            )
        )
    ):
        raise SyntheticPlanJournalRejected(
            "synthetic recovery authority epoch changed"
        )



def _checked_snapshot(
    graph: PlanGraph, tail: SyntheticPlanTail,
) -> tuple[SyntheticPlanRecovery, Callable[[], None]]:
    """Bind the return witness to the replayed graph across COMMIT callbacks.

    A reentrant snapshot/result constructor may return a syntactically valid
    but forged status, omit a RUNNING step, or replace an equal-valued tail.
    Capture pre-constructor values and post-constructor carrier references.
    The returned check also runs *after* COMMIT: rejection must not imply that
    a successfully committed local journal event was rolled back.
    """
    original_tail = (
        tail.topology_digest, tail.event_count, tail.event_hash,
        tail.status_digest, tail.last_at_ms,
    )
    tail_types = tuple(type(value) for value in original_tail)
    states = graph.statuses()
    expected_statuses = tuple(
        (name, state.state.value, state.revision)
        for name, state in sorted(states.items())
    )
    expected_running = tuple(
        name for name, state, _revision in expected_statuses
        if state == StepState.RUNNING.value
    )
    _require_original_recovery_denials()
    result = _snapshot(graph, tail)
    # _snapshot may be a substituted/reentrant test callback. It can rewrite
    # a recovery field slot or lookup hook AFTER our pre-call check; reading
    # result.tail below would execute that forged descriptor before denial.
    # Fail closed at the callback boundary, before ANY result field access.
    _require_original_recovery_denials()
    carriers = (
        (result.tail, result.step_statuses, result.ambiguous_running_steps)
        if type(result) is _RECOVERY_RESULT_TYPE else None
    )

    def assert_result() -> None:
        _require_original_recovery_denials()
        current_tail = (
            tail.topology_digest, tail.event_count, tail.event_hash,
            tail.status_digest, tail.last_at_ms,
        )
        if (
            type(result) is not _RECOVERY_RESULT_TYPE
            or type(tail) is not SyntheticPlanTail
            or tuple(type(value) for value in current_tail) != tail_types
            or current_tail != original_tail
            or any(
                value is not original
                for value, original in zip(
                    current_tail, original_tail, strict=True,
                )
            )
            or result.tail is not tail
            or result.tail is not carriers[0]
            or result.step_statuses is not carriers[1]
            or result.ambiguous_running_steps is not carriers[2]
            or type(result.step_statuses) is not tuple
            or result.step_statuses != expected_statuses
            or type(result.ambiguous_running_steps) is not tuple
            or result.ambiguous_running_steps != expected_running
        ):
            raise SyntheticPlanJournalRejected(
                "synthetic plan recovery result changed during review"
            )
        # Status hashing is itself a synthetic callback boundary. Recheck
        # the exact carriers and values again after that callback.
        # A denial property may itself be reentrant. Check each False-only
        # getter before hashing, then verify all result carriers after hashing.
        for name in _RECOVERY_DENIAL_NAMES:
            if getattr(result, name) is not False:
                raise SyntheticPlanJournalRejected(
                    "synthetic recovery result gained authority"
                )
            _require_original_recovery_denials()
        try:
            digest = graph.status_digest()
        except PlanConflictError as exc:
            # Preserve the journal's established topology-drift diagnostic.
            # A reentrant snapshot callback can mutate the original DAG,
            # which PlanGraph correctly rejects before we compare witnesses.
            raise SyntheticPlanJournalRejected(
                "synthetic plan topology changed during review"
            ) from exc
        # A status_digest() callback runs AFTER the last deny-only getter.
        # Detect a descriptor rebound at that boundary before exposing a
        # recovered state or treating an appended local event as authority.
        _require_original_recovery_denials()
        after_tail = (
            tail.topology_digest, tail.event_count, tail.event_hash,
            tail.status_digest, tail.last_at_ms,
        )
        if (
            digest != original_tail[3]
            or after_tail != original_tail
            or any(
                value is not original
                for value, original in zip(after_tail, original_tail, strict=True)
            )
            or result.tail is not carriers[0]
            or result.step_statuses is not carriers[1]
            or result.ambiguous_running_steps is not carriers[2]
            or result.step_statuses != expected_statuses
            or result.ambiguous_running_steps != expected_running
        ):
            raise SyntheticPlanJournalRejected(
                "synthetic plan recovery result changed during review"
            )

    assert_result()
    return result, assert_result


def _require_safe_journal_path(path: Path) -> None:
    """Refuse lexical/symlinked SQLite path escapes before any DB access.

    SQLite connection strings and Path.resolve() can follow symlinked parent
    directories even when the final file is not itself a symlink. This local
    preflight is not atomic directory-handle custody or independent provenance.
    """
    # Sidecar names must fit in the filesystem's encoded byte budget.
    # Refuse NUL, empty basename and oversized -journal paths BEFORE lstat:
    # OS-dependent path errors must not leak into the SQLite open boundary.
    if type(path) is not type(Path()):
        raise SyntheticPlanJournalRejected(
            "synthetic plan journal requires absolute non-traversing Path"
        )
    raw = str(path)
    if (
        not path.is_absolute()
        or not path.name
        or ".." in path.parts
        or "\x00" in raw
        or len(raw) > 4096
    ):
        raise SyntheticPlanJournalRejected(
            "synthetic plan journal requires absolute non-traversing Path"
        )
    try:
        if len(os.fsencode(path)) + len(b"-journal") > 4096:
            raise SyntheticPlanJournalRejected(
                "synthetic plan journal requires absolute non-traversing Path"
            )
    except (UnicodeError, ValueError) as exc:
        raise SyntheticPlanJournalRejected(
            "synthetic plan journal requires absolute non-traversing Path"
        ) from exc
    try:
        for ancestor in path.parents:
            meta = ancestor.lstat()
            if not stat.S_ISDIR(meta.st_mode) or stat.S_ISLNK(meta.st_mode):
                raise SyntheticPlanJournalRejected(
                    "synthetic plan journal ancestor is not a real directory"
                )
        if path.is_symlink():
            raise SyntheticPlanJournalRejected(
                "synthetic plan journal symlink refused"
            )
        if path.exists():
            meta = path.lstat()
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise SyntheticPlanJournalRejected(
                    "synthetic plan journal must be one regular file"
                )
        # An otherwise safe main DB does not make its SQLite -wal/-shm
        # or rollback journal safe. Refuse aliases, special files, and
        # orphan sidecars before either read-only replay or an append.
        # This lexical check is not a descriptor-held race proof.
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = path.with_name(path.name + suffix)
            try:
                sidecar_meta = sidecar.lstat()
            except FileNotFoundError:
                continue
            if (
                not path.exists()
                or not stat.S_ISREG(sidecar_meta.st_mode)
                or sidecar_meta.st_nlink != 1
            ):
                raise SyntheticPlanJournalRejected(
                    "synthetic plan journal sidecar unsafe or orphaned"
                )
    except OSError as exc:
        raise SyntheticPlanJournalRejected(
            "synthetic plan journal path cannot be verified"
        ) from exc


class SyntheticPlanJournal:
    """Bounded fixture journal: atomic event+tail, replay-only recovery."""

    def __init__(self, path: Path, steps: tuple[PlanStep, ...]) -> None:
        if type(path) is not type(Path()):
            raise TypeError("synthetic plan path must be an exact pathlib.Path")
        self._path = path
        # An instance-held path may be replaced *before* recover/append starts.
        # Keep the original carrier, not just a value-equal string, so a
        # retargeted journal never opens or writes another SQLite database.
        self._source_path_epoch = path
        self._steps = steps
        initial = PlanGraph(steps)
        with closing(self._connect(create=True)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if _objects(conn):
                        raise SyntheticPlanJournalRejected(
                            "unversioned synthetic plan database is not empty"
                        )
                    for ddl in _SCHEMA:
                        conn.execute(ddl)
                    conn.execute(
                        """INSERT INTO synthetic_plan_header
                           VALUES(1,?,?,?,?,?,?)""",
                        (
                            initial.topology_digest(), initial.status_digest(), 0,
                            _hash(
                                "ARK-synthetic-plan-genesis-v1",
                                (initial.topology_digest(), initial.status_digest()),
                            ),
                            initial.status_digest(), -1,
                        ),
                    )
                    conn.execute("PRAGMA user_version=1")
                self._replay(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _assert_source_path(self) -> None:
        # Preserve the established wrong-type diagnostic for callers holding
        # a corrupted instance, while still rejecting value-equal replacement
        # of an otherwise correctly typed source path before any DB access.
        if not isinstance(self._path, Path):
            raise SyntheticPlanJournalRejected(
                "synthetic plan source must be a Path"
            )
        if (
            type(self._path) is not type(Path())
            or self._path is not self._source_path_epoch
        ):
            raise SyntheticPlanJournalRejected(
                "synthetic plan source identity changed"
            )

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        self._assert_source_path()
        _require_safe_journal_path(self._path)
        # Only explicit journal initialization is allowed to create a file.
        # Appending to a missing/moved initialized journal must not silently
        # materialize a fresh empty SQLite database.
        if create:
            return sqlite3.connect(self._path, timeout=10, isolation_level=None)
        uri = self._path.resolve().as_uri() + "?mode=rw"
        return sqlite3.connect(uri, uri=True, timeout=10, isolation_level=None)

    def _replay(
        self, conn: sqlite3.Connection,
    ) -> tuple[PlanGraph, tuple[SyntheticPlanTail, ...]]:
        _schema_check(conn)
        graph = PlanGraph(self._steps)
        # The frozen header schema permits exactly one row. A malformed or
        # substituted cursor must never hydrate an unbounded result during
        # cold recovery; two rows suffice to reject ambiguity.
        headers = conn.execute(_HEADER).fetchmany(2)
        if len(headers) != 1:
            raise SyntheticPlanJournalRejected("synthetic plan header missing or duplicated")
        topology, initial, count, tail_hash, status_digest, last_at = headers[0]
        if (
            type(topology) is not str or topology != graph.topology_digest()
            or type(initial) is not str or initial != graph.status_digest()
            or type(count) is not int or not 0 <= count <= _MAX_EVENTS
            or type(tail_hash) is not str or not _HEX.fullmatch(tail_hash)
            or type(status_digest) is not str or not _STATE.fullmatch(status_digest)
            or type(last_at) is not int or not -1 <= last_at <= _MAX_INT
        ):
            raise SyntheticPlanJournalRejected("synthetic plan header integrity failed")
        genesis = _hash("ARK-synthetic-plan-genesis-v1", (topology, initial))
        prefixes = [SyntheticPlanTail(topology, 0, genesis, initial, -1)]
        cursor = conn.execute(_EVENTS)
        for ordinal, row in enumerate(cursor, 1):
            if ordinal > _MAX_EVENTS:
                raise SyntheticPlanJournalRejected("synthetic plan replay budget exceeded")
            (
                seq, step_id, before, after, expected_revision,
                resulting_revision, at_ms, after_digest, previous_hash, event_hash,
            ) = row
            if (
                type(seq) is not int or seq != ordinal
                or type(step_id) is not str or step_id not in graph.steps
                or type(before) is not str or before not in StepState._value2member_map_
                or type(after) is not str or after not in StepState._value2member_map_
                or type(expected_revision) is not int
                or not 0 <= expected_revision < _MAX_INT
                or type(resulting_revision) is not int
                or resulting_revision != expected_revision + 1
                or type(at_ms) is not int
                or not 0 <= at_ms <= _MAX_INT
                or at_ms < prefixes[-1].last_at_ms
                or type(after_digest) is not str or not _STATE.fullmatch(after_digest)
                or type(previous_hash) is not str
                or previous_hash != prefixes[-1].event_hash
                or type(event_hash) is not str or not _HEX.fullmatch(event_hash)
            ):
                raise SyntheticPlanJournalRejected("synthetic plan event integrity failed")
            old = graph.statuses()[step_id]
            if old.state.value != before or old.revision != expected_revision:
                raise SyntheticPlanJournalRejected("synthetic plan transition prestate mismatch")
            try:
                updated = graph.transition(
                    step_id, StepState(after), expected_revision=expected_revision,
                )
            except (PlanConflictError, TypeError, ValueError) as exc:
                raise SyntheticPlanJournalRejected(
                    "synthetic plan transition not replayable"
                ) from exc
            if updated.revision != resulting_revision or graph.status_digest() != after_digest:
                raise SyntheticPlanJournalRejected("synthetic plan poststate digest mismatch")
            payload = (
                seq, step_id, before, after, expected_revision,
                resulting_revision, at_ms, after_digest, previous_hash,
            )
            if event_hash != _hash("ARK-synthetic-plan-event-v1", payload):
                raise SyntheticPlanJournalRejected("synthetic plan event chain changed")
            prefixes.append(
                SyntheticPlanTail(topology, ordinal, event_hash, after_digest, at_ms)
            )
        if (
            count != len(prefixes) - 1
            or (topology, count, tail_hash, status_digest, last_at)
            != (
                prefixes[-1].topology_digest, prefixes[-1].event_count,
                prefixes[-1].event_hash, prefixes[-1].status_digest,
                prefixes[-1].last_at_ms,
            )
        ):
            raise SyntheticPlanJournalRejected("synthetic plan tail/header mismatch")
        return graph, tuple(prefixes)

    def _pin_topology(
        self,
    ) -> tuple[tuple[PlanStep, ...], str, tuple[tuple[object, ...], ...]]:
        steps_epoch = self._steps
        try:
            # A topology digest binds request *values*, not the exact original
            # PlanStep/ToolCall/dependency carriers used for this operation.
            # Pin nested identity BEFORE the first graph/hash callback.
            carriers = tuple(
                (
                    step, step.step_id, step.call, step.depends_on,
                    step.call.tool, step.call.capability, step.call.scope,
                    step.call.arguments, step.call.request_id,
                )
                for step in steps_epoch
            )
            digest = PlanGraph(steps_epoch).topology_digest()
            self._assert_topology_epoch(steps_epoch, digest, carriers)
        except (PlanConflictError, TypeError, ValueError, AttributeError) as exc:
            raise SyntheticPlanJournalRejected(
                "synthetic plan topology is invalid"
            ) from exc
        return steps_epoch, digest, carriers

    def _assert_topology_epoch(
        self, steps_epoch: tuple[PlanStep, ...], digest: str,
        carriers: tuple[tuple[object, ...], ...],
    ) -> None:
        def carrier_unchanged() -> bool:
            return (
                self._steps is steps_epoch
                and len(steps_epoch) == len(carriers)
                and all(
                    step is original
                    and step.step_id is old_step_id
                    and step.call is old_call
                    and step.depends_on is old_dependencies
                    # A frozen ToolCall can be reflectively mutated in-place
                    # without changing its canonical request digest (e.g.,
                    # replacement by a distinct but equal string object).
                    # Pin original nested identities, not only digest values.
                    and step.call.tool is old_tool
                    and step.call.capability is old_capability
                    and step.call.scope is old_scope
                    and step.call.arguments is old_arguments
                    and step.call.request_id == old_request
                    for step, (
                        original, old_step_id, old_call, old_dependencies,
                        old_tool, old_capability, old_scope,
                        old_arguments, old_request,
                    ) in zip(steps_epoch, carriers, strict=True)
                )
            )

        try:
            before = carrier_unchanged()
            if not before:
                raise SyntheticPlanJournalRejected(
                    "synthetic plan topology changed during review"
                )
            same_digest = PlanGraph(steps_epoch).topology_digest() == digest
            # PlanGraph construction/hashing may be reentrant too. A callback
            # that replaces a value-equal PlanStep call must not rebase the
            # caller's original action within an append/recovery.
            after = carrier_unchanged()
            if not same_digest or not after:
                raise SyntheticPlanJournalRejected(
                    "synthetic plan topology changed during review"
                )
        except (PlanConflictError, TypeError, ValueError, AttributeError) as exc:
            raise SyntheticPlanJournalRejected(
                "synthetic plan topology changed during review"
            ) from exc

    def recover(
        self, *, retained: SyntheticPlanTail | None = None,
    ) -> SyntheticPlanRecovery:
        """Read-only replay; an independently retained earlier tail is optional.

        A locally regenerated earlier witness provides no tamper resistance.
        No step is dispatched, and RUNNING is ambiguous rather than retried.
        """
        _require_original_recovery_denials()
        path_epoch = self._path
        self._assert_source_path()
        # Pin an independent witness before the first reentrant topology
        # hash or witness-shape callback; never silently accept a new prefix.
        pinned = None
        if retained is not None:
            if type(retained) is not SyntheticPlanTail:
                raise SyntheticPlanJournalRejected("retained tail has wrong type")
            pinned = (
                retained.topology_digest, retained.event_count,
                retained.event_hash, retained.status_digest, retained.last_at_ms,
            )
        steps_epoch, topology_epoch, carriers = self._pin_topology()
        if retained is not None:
            _require_original_recovery_denials()
            retained.assert_shape()
            if (
                retained.topology_digest, retained.event_count,
                retained.event_hash, retained.status_digest, retained.last_at_ms,
            ) != pinned or not _retained_tail_epoch_stable(retained, pinned):
                raise SyntheticPlanJournalRejected(
                    "retained synthetic plan witness changed before recovery"
                )
        # Recovery previously bypassed the verified _connect() path and
        # resolved an unchecked pathname, permitting a post-init symlink
        # retarget to be read. Recheck main, ancestors and sidecars before
        # constructing the read-only URI. No source is auto-recreated.
        _require_safe_journal_path(path_epoch)
        uri = path_epoch.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
            conn.execute("BEGIN")
            try:
                graph, prefixes = self._replay(conn)
                # Check topology before using the replayed graph: a callback
                # may mutate its original frozen step during _replay itself.
                self._assert_topology_epoch(steps_epoch, topology_epoch, carriers)
                # Compare stored prefix scalars, never replaceable dataclass
                # __eq__; a forged retained hash cannot become a valid tail.
                if retained is not None and (
                    retained.event_count >= len(prefixes)
                    or (
                        prefixes[retained.event_count].topology_digest,
                        prefixes[retained.event_count].event_count,
                        prefixes[retained.event_count].event_hash,
                        prefixes[retained.event_count].status_digest,
                        prefixes[retained.event_count].last_at_ms,
                    ) != pinned
                ):
                    raise SyntheticPlanJournalRejected("retained synthetic plan history changed")
                result, check_result = _checked_snapshot(graph, prefixes[-1])
                if retained is not None:
                    _require_original_recovery_denials()
                    retained.assert_shape()
                    current = (
                        retained.topology_digest, retained.event_count,
                        retained.event_hash, retained.status_digest, retained.last_at_ms,
                    )
                    if current != pinned or not _retained_tail_epoch_stable(
                        retained, pinned,
                    ):
                        raise SyntheticPlanJournalRejected(
                            "retained synthetic plan witness changed during recovery"
                        )
                if self._path is not path_epoch:
                    raise SyntheticPlanJournalRejected(
                        "synthetic plan source changed during recovery"
                    )
                self._assert_topology_epoch(steps_epoch, topology_epoch, carriers)
                conn.commit()
                check_result()
                if retained is not None and not _retained_tail_epoch_stable(
                    retained, pinned,
                ):
                    raise SyntheticPlanJournalRejected(
                        "retained synthetic plan witness changed after recovery"
                    )
                return result
            except BaseException:
                conn.rollback()
                raise

    def append(
        self, step_id: str, to_state: StepState, *,
        expected_revision: int, at_ms: int,
        retained: SyntheticPlanTail | None = None,
    ) -> SyntheticPlanRecovery:
        """CAS and journal append in one local transaction, without effects."""
        _require_original_recovery_denials()
        if type(at_ms) is not int or not 0 <= at_ms <= _MAX_INT:
            raise SyntheticPlanJournalRejected("invalid synthetic plan timestamp")
        if type(to_state) is not StepState:
            raise SyntheticPlanJournalRejected("invalid synthetic plan target state")
        # Fail closed before opening SQLite. PlanGraph.transition also checks
        # these, but only AFTER replay, which is unnecessary for malformed or
        # nonexistent caller-supplied step/revision identities.
        if (
            type(step_id) is not str or not step_id.strip()
            or step_id not in (step.step_id for step in self._steps)
        ):
            raise SyntheticPlanJournalRejected("unknown or invalid synthetic plan step")
        if (
            type(expected_revision) is not int
            or not 0 <= expected_revision <= _MAX_INT
        ):
            raise SyntheticPlanJournalRejected("invalid synthetic plan expected revision")
        # An earlier, independently retained tail must match inside the same
        # write transaction as the new transition. Never use a separate
        # preflight read as an authority for this append.
        _require_original_recovery_denials()
        path_epoch = self._path
        self._assert_source_path()
        # Capture original retained evidence before any topology/shape
        # callback or tentative SQLite event append.
        pinned = None
        if retained is not None:
            if type(retained) is not SyntheticPlanTail:
                raise SyntheticPlanJournalRejected("retained tail has wrong type")
            pinned = (
                retained.topology_digest, retained.event_count, retained.event_hash,
                retained.status_digest, retained.last_at_ms,
            )
        steps_epoch, topology_epoch, carriers = self._pin_topology()
        if retained is not None:
            _require_original_recovery_denials()
            retained.assert_shape()
            if (
                retained.topology_digest, retained.event_count,
                retained.event_hash, retained.status_digest, retained.last_at_ms,
            ) != pinned or not _retained_tail_epoch_stable(retained, pinned):
                raise SyntheticPlanJournalRejected(
                    "retained synthetic plan witness changed before append"
                )
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                graph, prefixes = self._replay(conn)
                # Check topology before using the replayed graph: a callback
                # may mutate its original frozen step during _replay itself.
                self._assert_topology_epoch(steps_epoch, topology_epoch, carriers)
                if pinned is not None:
                    _require_original_recovery_denials()
                    retained.assert_shape()
                    current_retained = (
                        retained.topology_digest, retained.event_count, retained.event_hash,
                        retained.status_digest, retained.last_at_ms,
                    )
                    if (
                        current_retained != pinned
                        or not _retained_tail_epoch_stable(retained, pinned)
                        or retained.event_count >= len(prefixes)
                        or (
                            prefixes[retained.event_count].topology_digest,
                            prefixes[retained.event_count].event_count,
                            prefixes[retained.event_count].event_hash,
                            prefixes[retained.event_count].status_digest,
                            prefixes[retained.event_count].last_at_ms,
                        ) != pinned
                    ):
                        raise SyntheticPlanJournalRejected(
                            "retained synthetic plan history changed before append"
                        )
                prev = prefixes[-1]
                if prev.event_count >= _MAX_EVENTS or at_ms < prev.last_at_ms:
                    raise SyntheticPlanJournalRejected(
                        "synthetic plan capacity or clock regression"
                    )
                current = graph.statuses()[step_id]
                updated = graph.transition(
                    step_id, to_state, expected_revision=expected_revision,
                )
                post = graph.status_digest()
                payload = (
                    prev.event_count + 1, step_id, current.state.value, to_state.value,
                    expected_revision, updated.revision, at_ms, post, prev.event_hash,
                )
                event_hash = _hash("ARK-synthetic-plan-event-v1", payload)
                conn.execute(
                    """INSERT INTO synthetic_plan_events VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (*payload, event_hash),
                )
                conn.execute(
                    """UPDATE synthetic_plan_header
                       SET event_count=?,tail_hash=?,status_digest=?,last_at_ms=?
                       WHERE id=1""",
                    (prev.event_count + 1, event_hash, post, at_ms),
                )
                result, check_result = _checked_snapshot(
                    graph,
                    SyntheticPlanTail(
                        prev.topology_digest, prev.event_count + 1,
                        event_hash, post, at_ms,
                    ),
                )
                # Snapshot construction is another overridable/reentrant
                # boundary. Revalidate an independently retained older tail
                # *after* it, before committing the row and header together.
                if retained is not None:
                    _require_original_recovery_denials()
                    retained.assert_shape()
                    if (
                        retained.topology_digest, retained.event_count,
                        retained.event_hash, retained.status_digest, retained.last_at_ms,
                    ) != pinned or not _retained_tail_epoch_stable(retained, pinned):
                        raise SyntheticPlanJournalRejected(
                            "retained synthetic plan witness changed during append"
                        )
                if self._path is not path_epoch:
                    raise SyntheticPlanJournalRejected(
                        "synthetic plan source changed during append"
                    )
                self._assert_topology_epoch(steps_epoch, topology_epoch, carriers)
                conn.commit()
                check_result()
                if retained is not None and not _retained_tail_epoch_stable(
                    retained, pinned,
                ):
                    # A local event may already be durable; never auto-retry it.
                    raise SyntheticPlanJournalRejected(
                        "retained synthetic plan witness changed after append commit"
                    )
                return result
            except BaseException:
                conn.rollback()
                raise
