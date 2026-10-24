"""Disconnected, replay-only SQLite journal for synthetic PlanGraph transitions.

This is a fixture, NOT execution authority. Callers provide the clock and
topology. A recovered RUNNING step is UNKNOWN, never an instruction to retry.
A matching internal tail is not independent evidence against coordinated
rewrites; callers must retain an earlier tail outside this SQLite database.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
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
    with sqlite3.connect(":memory:") as expected:
        for ddl in _SCHEMA:
            expected.execute(ddl)
        if _objects(conn) != _objects(expected):
            raise SyntheticPlanJournalRejected("synthetic plan schema changed")
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
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


class SyntheticPlanJournal:
    """Bounded fixture journal: atomic event+tail, replay-only recovery."""

    def __init__(self, path: Path, steps: tuple[PlanStep, ...]) -> None:
        if not isinstance(path, Path):
            raise TypeError("synthetic plan path must be an exact pathlib.Path")
        self._path = path
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

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
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
        headers = conn.execute(_HEADER).fetchall()
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

    def recover(
        self, *, retained: SyntheticPlanTail | None = None,
    ) -> SyntheticPlanRecovery:
        """Read-only replay; an independently retained earlier tail is optional.

        A locally regenerated earlier witness provides no tamper resistance.
        No step is dispatched, and RUNNING is ambiguous rather than retried.
        """
        path_epoch = self._path
        if not isinstance(path_epoch, Path):
            raise SyntheticPlanJournalRejected("synthetic plan source must be a Path")
        pinned = None
        if retained is not None:
            if type(retained) is not SyntheticPlanTail:
                raise SyntheticPlanJournalRejected("retained tail has wrong type")
            retained.assert_shape()
            pinned = (
                retained.topology_digest, retained.event_count,
                retained.event_hash, retained.status_digest, retained.last_at_ms,
            )
        uri = path_epoch.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
            conn.execute("BEGIN")
            try:
                graph, prefixes = self._replay(conn)
                if retained is not None and (
                    retained.event_count >= len(prefixes)
                    or prefixes[retained.event_count] != retained
                ):
                    raise SyntheticPlanJournalRejected("retained synthetic plan history changed")
                result = _snapshot(graph, prefixes[-1])
                if retained is not None:
                    retained.assert_shape()
                    current = (
                        retained.topology_digest, retained.event_count,
                        retained.event_hash, retained.status_digest, retained.last_at_ms,
                    )
                    if current != pinned:
                        raise SyntheticPlanJournalRejected(
                            "retained synthetic plan witness changed during recovery"
                        )
                if self._path is not path_epoch:
                    raise SyntheticPlanJournalRejected(
                        "synthetic plan source changed during recovery"
                    )
                conn.commit()
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
        if type(at_ms) is not int or not 0 <= at_ms <= _MAX_INT:
            raise SyntheticPlanJournalRejected("invalid synthetic plan timestamp")
        if type(to_state) is not StepState:
            raise SyntheticPlanJournalRejected("invalid synthetic plan target state")
        # An earlier, independently retained tail must match inside the same
        # write transaction as the new transition. Never use a separate
        # preflight read as an authority for this append.
        path_epoch = self._path
        if not isinstance(path_epoch, Path):
            raise SyntheticPlanJournalRejected("synthetic plan source must be a Path")
        pinned = None
        if retained is not None:
            if type(retained) is not SyntheticPlanTail:
                raise SyntheticPlanJournalRejected("retained tail has wrong type")
            retained.assert_shape()
            pinned = (
                retained.topology_digest, retained.event_count, retained.event_hash,
                retained.status_digest, retained.last_at_ms,
            )
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                graph, prefixes = self._replay(conn)
                if pinned is not None:
                    retained.assert_shape()
                    current_retained = (
                        retained.topology_digest, retained.event_count, retained.event_hash,
                        retained.status_digest, retained.last_at_ms,
                    )
                    if (
                        current_retained != pinned
                        or retained.event_count >= len(prefixes)
                        or prefixes[retained.event_count] != retained
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
                result = _snapshot(
                    graph,
                    SyntheticPlanTail(
                        prev.topology_digest, prev.event_count + 1,
                        event_hash, post, at_ms,
                    ),
                )
                if self._path is not path_epoch:
                    raise SyntheticPlanJournalRejected(
                        "synthetic plan source changed during append"
                    )
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise
