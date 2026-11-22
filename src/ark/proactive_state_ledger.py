"""Durable, content-minimized proactive eligibility state; never notifies.

This SQLite fixture persists local rate-limit and unchanged-observation state
across restarts. Caller clocks, owner labels and observation digests are
unauthenticated. ELIGIBLE_PREVIEW is not consent, notification permission,
dispatch authority, a trusted-clock assertion or an external outcome.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from . import proactive_synthetic_review as _proactive

_MAX = 2**63 - 1
_MAX_ROWS = 10_000
_MAX_WINDOW_ITEMS = 1_000
_HEX = re.compile(r"[0-9a-f]{64}\\Z")
_DECISIONS = frozenset({
    "ELIGIBLE_PREVIEW", "UNCHANGED", "TOO_SOON", "COOLDOWN", "WINDOW_BUDGET",
})
_TABLE = """CREATE TABLE synthetic_proactive_states(
    scope_digest TEXT NOT NULL,
    policy_digest TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK(revision>=1),
    last_observation_digest TEXT NOT NULL,
    last_observed_at_ms INTEGER NOT NULL CHECK(last_observed_at_ms>=0),
    last_evaluated_at_ms INTEGER NOT NULL CHECK(last_evaluated_at_ms>=0),
    last_proposal_at_ms INTEGER NOT NULL CHECK(last_proposal_at_ms>=0),
    window_proposal_times_json TEXT NOT NULL,
    last_decision TEXT NOT NULL,
    updated_at_ms INTEGER NOT NULL CHECK(updated_at_ms>=0),
    state_sha256 TEXT NOT NULL,
    PRIMARY KEY(scope_digest,policy_digest),
    CHECK(last_observed_at_ms<=last_evaluated_at_ms),
    CHECK(last_proposal_at_ms<=last_evaluated_at_ms),
    CHECK(updated_at_ms>=last_evaluated_at_ms),
    CHECK(last_decision IN (
        'ELIGIBLE_PREVIEW','UNCHANGED','TOO_SOON','COOLDOWN','WINDOW_BUDGET'
    ))
)"""

_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_SQLITE = sqlite3
_ORIGINAL_CONNECT = sqlite3.connect
_ORIGINAL_PROACTIVE_MODULE = _proactive
_ORIGINAL_PATH_CHECK = _proactive._refuse_aliased_proactive_path
_ORIGINAL_PROACTIVE_STAT = _proactive.stat
_ORIGINAL_PROACTIVE_S_ISDIR = _proactive.stat.S_ISDIR
_ORIGINAL_PROACTIVE_S_ISREG = _proactive.stat.S_ISREG
_ORIGINAL_PROACTIVE_S_ISLNK = _proactive.stat.S_ISLNK
_ORIGINAL_TABLE = _TABLE
_ORIGINAL_BOUNDS = (_MAX, _MAX_ROWS, _MAX_WINDOW_ITEMS)


class SyntheticProactiveStateRejected(RuntimeError):
    """The local proactive state or its policy is malformed or stale."""


class SyntheticProactiveStateConflict(SyntheticProactiveStateRejected):
    """A compare-and-swap revision no longer matches the persisted state."""


def _require_original_protocol() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or sqlite3 is not _ORIGINAL_SQLITE
        or sqlite3.connect is not _ORIGINAL_CONNECT
        or _proactive is not _ORIGINAL_PROACTIVE_MODULE
        or _proactive._refuse_aliased_proactive_path is not _ORIGINAL_PATH_CHECK
        or _proactive.stat is not _ORIGINAL_PROACTIVE_STAT
        or _ORIGINAL_PROACTIVE_STAT.S_ISDIR is not _ORIGINAL_PROACTIVE_S_ISDIR
        or _ORIGINAL_PROACTIVE_STAT.S_ISREG is not _ORIGINAL_PROACTIVE_S_ISREG
        or _ORIGINAL_PROACTIVE_STAT.S_ISLNK is not _ORIGINAL_PROACTIVE_S_ISLNK
        or _TABLE is not _ORIGINAL_TABLE
        or any(type(value) is not int for value in (_MAX, _MAX_ROWS, _MAX_WINDOW_ITEMS))
        or (_MAX, _MAX_ROWS, _MAX_WINDOW_ITEMS) != _ORIGINAL_BOUNDS
    ):
        raise SyntheticProactiveStateRejected("proactive state protocol changed")


def _hash(label: str, values: object) -> str:
    _require_original_protocol()
    payload = json.dumps(
        values, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    _require_original_protocol()
    digest = _ORIGINAL_SHA256(label.encode("utf-8") + b"\\0" + payload).hexdigest()
    _require_original_protocol()
    return digest


def _exact_text(name: str, value: object) -> None:
    if type(value) is not str or not 1 <= len(value) <= 512 or value != value.strip():
        raise SyntheticProactiveStateRejected(f"{name} must be a bounded exact string")
    if "\\x00" in value or any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise SyntheticProactiveStateRejected(f"{name} contains a control delimiter")
    try:
        size = len(value.encode("utf-8", errors="strict"))
    except UnicodeError as exc:
        raise SyntheticProactiveStateRejected(f"{name} is not valid UTF-8") from exc
    if size > 512:
        raise SyntheticProactiveStateRejected(f"{name} exceeds its UTF-8 byte budget")


def _exact_int(name: str, value: object, *, minimum: int = 0) -> None:
    if type(value) is not int or not minimum <= value <= _MAX:
        raise SyntheticProactiveStateRejected(f"{name} must be an exact bounded integer")


@dataclass(frozen=True, slots=True)
class SyntheticProactivePolicy:
    owner: str
    namespace: str
    definition_id: str
    revision: int
    policy_revision: str
    minimum_interval_ms: int
    cooldown_ms: int
    rolling_window_ms: int
    max_previews_per_window: int

    def __post_init__(self) -> None:
        _require_original_policy_contract()
        fields = (
            "owner", "namespace", "definition_id", "revision", "policy_revision",
            "minimum_interval_ms", "cooldown_ms", "rolling_window_ms",
            "max_previews_per_window",
        )
        original = tuple(getattr(self, name) for name in fields)
        for name in ("owner", "namespace", "definition_id", "policy_revision"):
            _exact_text(name, getattr(self, name))
            _assert_policy_fields(self, fields, original)
        _exact_int("revision", self.revision, minimum=1)
        _exact_int("minimum_interval_ms", self.minimum_interval_ms)
        _exact_int("cooldown_ms", self.cooldown_ms)
        _exact_int("rolling_window_ms", self.rolling_window_ms, minimum=1)
        _exact_int("max_previews_per_window", self.max_previews_per_window, minimum=1)
        if self.max_previews_per_window > _MAX_WINDOW_ITEMS:
            raise SyntheticProactiveStateRejected("preview window capacity exceeds its bound")
        _assert_policy_fields(self, fields, original)

    def identity(self) -> tuple[str, str]:
        _require_original_policy_contract()
        values = (
            self.owner, self.namespace, self.definition_id, self.revision,
            self.policy_revision, self.minimum_interval_ms, self.cooldown_ms,
            self.rolling_window_ms, self.max_previews_per_window,
        )
        scope = _hash("ARK-proactive-state-scope-v1", values[:2])
        policy = _hash("ARK-proactive-state-policy-v1", values[2:])
        _assert_policy_fields(self, _POLICY_FIELDS, values)
        return scope, policy


_POLICY_TYPE = SyntheticProactivePolicy
_POLICY_FIELDS = (
    "owner", "namespace", "definition_id", "revision", "policy_revision",
    "minimum_interval_ms", "cooldown_ms", "rolling_window_ms",
    "max_previews_per_window",
)
_POLICY_METHODS = ("__init__", "__new__", "__getattribute__", "__getattr__", "__post_init__", "identity")
_ORIGINAL_POLICY_FIELDS = tuple(vars(_POLICY_TYPE)[name] for name in _POLICY_FIELDS)
_ORIGINAL_POLICY_METHODS = tuple(vars(_POLICY_TYPE).get(name) for name in _POLICY_METHODS)


def _require_original_policy_contract() -> None:
    _require_original_protocol()
    if (
        SyntheticProactivePolicy is not _POLICY_TYPE
        or any(
            vars(_POLICY_TYPE).get(name) is not original
            for names, originals in (
                (_POLICY_FIELDS, _ORIGINAL_POLICY_FIELDS),
                (_POLICY_METHODS, _ORIGINAL_POLICY_METHODS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticProactiveStateRejected("proactive policy definition changed")


def _assert_policy_fields(
    policy: SyntheticProactivePolicy,
    names: tuple[str, ...],
    original: tuple[object, ...],
) -> None:
    _require_original_policy_contract()
    if any(
        getattr(policy, name) is not saved
        for name, saved in zip(names, original, strict=True)
    ):
        raise SyntheticProactiveStateRejected("proactive policy changed during review")


@dataclass(frozen=True, slots=True)
class SyntheticProactiveState:
    scope_digest: str
    policy_digest: str
    revision: int
    last_observation_digest: str
    last_observed_at_ms: int
    last_evaluated_at_ms: int
    last_proposal_at_ms: int
    window_proposal_times: tuple[int, ...]
    last_decision: str
    updated_at_ms: int
    state_sha256: str

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False


_STATE_TYPE = SyntheticProactiveState
_STATE_FIELDS = (
    "scope_digest", "policy_digest", "revision", "last_observation_digest",
    "last_observed_at_ms", "last_evaluated_at_ms", "last_proposal_at_ms",
    "window_proposal_times", "last_decision", "updated_at_ms", "state_sha256",
)
_STATE_DENIALS = (
    "notification_authorized", "dispatch_authorized", "trusted_clock_verified",
    "automatic_replay_authorized", "consent_verified",
)
_STATE_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_STATE_FIELDS = tuple(vars(_STATE_TYPE)[name] for name in _STATE_FIELDS)
_ORIGINAL_STATE_DENIALS = tuple(vars(_STATE_TYPE)[name] for name in _STATE_DENIALS)
_ORIGINAL_STATE_HOOKS = tuple(vars(_STATE_TYPE).get(name) for name in _STATE_HOOKS)


def _require_original_state_type() -> None:
    _require_original_protocol()
    if (
        SyntheticProactiveState is not _STATE_TYPE
        or any(
            vars(_STATE_TYPE).get(name) is not original
            for names, originals in (
                (_STATE_FIELDS, _ORIGINAL_STATE_FIELDS),
                (_STATE_DENIALS, _ORIGINAL_STATE_DENIALS),
                (_STATE_HOOKS, _ORIGINAL_STATE_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticProactiveStateRejected("proactive state result definition changed")


def _state_values(
    scope: str,
    policy: str,
    revision: int,
    observation: str,
    observed_at: int,
    evaluated_at: int,
    proposal_at: int,
    window_times: tuple[int, ...],
    decision: str,
    updated_at: int,
) -> tuple[object, ...]:
    return (
        scope, policy, revision, observation, observed_at, evaluated_at,
        proposal_at, window_times, decision, updated_at,
    )


def _state_digest(values: tuple[object, ...]) -> str:
    return _hash("ARK-proactive-state-row-v1", values)


def _build_state(values: tuple[object, ...]) -> SyntheticProactiveState:
    _require_original_state_type()
    state = SyntheticProactiveState(*values, _state_digest(values))
    _require_original_state_type()
    if (
        type(state) is not _STATE_TYPE
        or any(
            getattr(state, name) is not expected
            for name, expected in zip(
                _STATE_FIELDS,
                (*values, _state_digest(values)),
                strict=True,
            )
        )
    ):
        raise SyntheticProactiveStateRejected("proactive state result changed")
    for name in _STATE_DENIALS:
        if getattr(state, name) is not False:
            raise SyntheticProactiveStateRejected("proactive state gained authority")
        _require_original_state_type()
    return state


def _canonical_window(values: tuple[int, ...]) -> str:
    return json.dumps(list(values), separators=(",", ":"), ensure_ascii=True)


def _objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        tuple(row) for row in conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        )
    )


def _row_state(row: tuple[object, ...]) -> SyntheticProactiveState:
    if type(row) is not tuple or len(row) != 11:
        raise SyntheticProactiveStateRejected("proactive state row shape changed")
    (
        scope, policy, revision, observation, observed_at, evaluated_at,
        proposal_at, window_json, decision, updated_at, digest,
    ) = row
    if (
        type(scope) is not str or not _HEX.fullmatch(scope)
        or type(policy) is not str or not _HEX.fullmatch(policy)
        or type(revision) is not int or not 1 <= revision <= _MAX
        or type(observation) is not str or not _HEX.fullmatch(observation)
        or any(type(value) is not int or not 0 <= value <= _MAX for value in (
            observed_at, evaluated_at, proposal_at, updated_at,
        ))
        or type(window_json) is not str
        or type(decision) is not str or decision not in _DECISIONS
        or type(digest) is not str or not _HEX.fullmatch(digest)
        or not observed_at <= evaluated_at <= updated_at
        or proposal_at <= evaluated_at
    ):
        raise SyntheticProactiveStateRejected("proactive state row integrity failed")
    try:
        window_list = json.loads(window_json)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SyntheticProactiveStateRejected("proactive window JSON is invalid") from exc
    _require_original_protocol()
    if (
        type(window_list) is not list
        or any(type(value) is not int or not 0 <= value <= _MAX for value in window_list)
        or len(window_list) > _MAX_WINDOW_ITEMS
        or any(left >= right for left, right in zip(window_list, window_list[1:]))
        or _canonical_window(tuple(window_list)) != window_json
    ):
        raise SyntheticProactiveStateRejected("proactive window history is noncanonical")
    window = tuple(window_list)
    values = _state_values(
        scope, policy, revision, observation, observed_at, evaluated_at,
        proposal_at, window, decision, updated_at,
    )
    if _state_digest(values) != digest:
        raise SyntheticProactiveStateRejected("proactive state digest mismatch")
    return _build_state(values)


def _validate(conn: sqlite3.Connection) -> None:
    _require_original_protocol()
    version = conn.execute("PRAGMA user_version").fetchone()
    if version != (1,):
        raise SyntheticProactiveStateRejected("proactive state schema version changed")
    with closing(_ORIGINAL_CONNECT(":memory:")) as expected:
        expected.execute(_TABLE)
        if _objects(conn) != _objects(expected):
            raise SyntheticProactiveStateRejected("proactive state schema changed")
    if conn.execute("PRAGMA quick_check").fetchmany(2) != [("ok",)]:
        raise SyntheticProactiveStateRejected("proactive state SQLite integrity failed")
    budget = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(CASE WHEN "
        "typeof(scope_digest)='text' AND length(CAST(scope_digest AS BLOB))=64 "
        "AND typeof(policy_digest)='text' AND length(CAST(policy_digest AS BLOB))=64 "
        "AND typeof(revision)='integer' "
        "AND typeof(last_observation_digest)='text' "
        "AND length(CAST(last_observation_digest AS BLOB))=64 "
        "AND typeof(last_observed_at_ms)='integer' "
        "AND typeof(last_evaluated_at_ms)='integer' "
        "AND typeof(last_proposal_at_ms)='integer' "
        "AND typeof(window_proposal_times_json)='text' "
        "AND length(CAST(window_proposal_times_json AS BLOB))<=16384 "
        "AND typeof(last_decision)='text' "
        "AND length(CAST(last_decision AS BLOB))<=32 "
        "AND typeof(updated_at_ms)='integer' "
        "AND typeof(state_sha256)='text' "
        "AND length(CAST(state_sha256 AS BLOB))=64 "
        "THEN 0 ELSE 1 END),0) "
        "FROM synthetic_proactive_states"
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int or not 0 <= budget[0] <= _MAX_ROWS
        or type(budget[1]) is not int or budget[1] != 0
    ):
        raise SyntheticProactiveStateRejected("proactive state SQL preflight failed")
    rows = conn.execute(
        "SELECT scope_digest,policy_digest,revision,last_observation_digest,"
        "last_observed_at_ms,last_evaluated_at_ms,last_proposal_at_ms,"
        "window_proposal_times_json,last_decision,updated_at_ms,state_sha256 "
        "FROM synthetic_proactive_states"
    )
    for index, row in enumerate(rows):
        if index >= _MAX_ROWS:
            raise SyntheticProactiveStateRejected("proactive state row budget exceeded")
        _row_state(tuple(row))


def _validate_policy_state(
    state: SyntheticProactiveState,
    policy: SyntheticProactivePolicy,
    scope_digest: str,
    policy_digest: str,
) -> None:
    if (
        type(state) is not _STATE_TYPE
        or state.scope_digest != scope_digest
        or state.policy_digest != policy_digest
        or len(state.window_proposal_times) > policy.max_previews_per_window
        or any(
            at <= state.updated_at_ms - policy.rolling_window_ms
            or at > state.updated_at_ms
            for at in state.window_proposal_times
        )
        or (
            state.window_proposal_times
            and state.window_proposal_times[-1] != state.last_proposal_at_ms
        )
        or (
            not state.window_proposal_times
            and state.last_proposal_at_ms
            > state.updated_at_ms - policy.rolling_window_ms
        )
    ):
        raise SyntheticProactiveStateRejected("proactive state does not match policy window")


def _safe_path(path: Path) -> None:
    _require_original_protocol()
    if type(path) is not type(Path(".")) or ".." in path.parts:
        raise SyntheticProactiveStateRejected("proactive state path must be an exact Path")
    try:
        raw = str(path)
        if "\\x00" in raw or len(raw) > 4096:
            raise SyntheticProactiveStateRejected("proactive state path exceeds its budget")
        _proactive._refuse_aliased_proactive_path(path)
        _require_original_protocol()
    except SyntheticProactiveStateRejected:
        raise
    except (OSError, ValueError, TypeError) as exc:
        raise SyntheticProactiveStateRejected("proactive state path is unavailable") from exc


class SyntheticProactiveStateLedger:
    """SQLite CAS state for proposal eligibility; no timer or notification."""

    def __init__(self, path: Path) -> None:
        _require_original_protocol()
        if type(path) is not type(Path(".")):
            raise TypeError("proactive state path must be an exact Path")
        _safe_path(path)
        self.path = path
        with closing(_ORIGINAL_CONNECT(path, timeout=10, isolation_level=None)) as conn:
            _require_original_protocol()
            _safe_path(path)
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()
                if version == (0,):
                    if conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone() is not None:
                        raise SyntheticProactiveStateRejected(
                            "unversioned proactive state database is not empty"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _validate(conn)
                _safe_path(path)
                if self.path is not path:
                    raise SyntheticProactiveStateRejected("proactive state path changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        _require_original_protocol()

    def _connect(self, *, read_only: bool) -> sqlite3.Connection:
        _require_original_protocol()
        path = self.path
        _safe_path(path)
        resolved = path.resolve()
        _require_original_protocol()
        if self.path is not path:
            raise SyntheticProactiveStateRejected("proactive state path changed before open")
        mode = "ro" if read_only else "rw"
        uri = resolved.as_uri() + "?mode=" + mode
        if self.path is not path:
            raise SyntheticProactiveStateRejected("proactive state path changed before open")
        conn = _ORIGINAL_CONNECT(
            uri, uri=True, timeout=10, isolation_level=None,
        )
        _require_original_protocol()
        if self.path is not path:
            conn.close()
            raise SyntheticProactiveStateRejected("proactive state path changed during open")
        _safe_path(path)
        return conn

    @staticmethod
    def _policy_identity(policy: SyntheticProactivePolicy) -> tuple[str, str, tuple[object, ...]]:
        if type(policy) is not _POLICY_TYPE:
            raise SyntheticProactiveStateRejected("exact proactive policy required")
        _require_original_policy_contract()
        values = tuple(getattr(policy, name) for name in _POLICY_FIELDS)
        identity = policy.identity()
        _assert_policy_fields(policy, _POLICY_FIELDS, values)
        return identity[0], identity[1], values

    def read_state(
        self, policy: SyntheticProactivePolicy,
    ) -> SyntheticProactiveState | None:
        scope, policy_digest, policy_values = self._policy_identity(policy)
        path_epoch = self.path
        with closing(self._connect(read_only=True)) as conn:
            if self.path is not path_epoch:
                raise SyntheticProactiveStateRejected("proactive state path changed before read")
            conn.execute("BEGIN")
            try:
                _validate(conn)
                row = conn.execute(
                    "SELECT scope_digest,policy_digest,revision,last_observation_digest,"
                    "last_observed_at_ms,last_evaluated_at_ms,last_proposal_at_ms,"
                    "window_proposal_times_json,last_decision,updated_at_ms,state_sha256 "
                    "FROM synthetic_proactive_states WHERE scope_digest=? AND policy_digest=?",
                    (scope, policy_digest),
                ).fetchone()
                state = None if row is None else _row_state(tuple(row))
                if state is not None:
                    _validate_policy_state(state, policy, scope, policy_digest)
                _assert_policy_fields(policy, _POLICY_FIELDS, policy_values)
                if self.path is not path_epoch:
                    raise SyntheticProactiveStateRejected("proactive state path changed during read")
                conn.commit()
                return state
            except BaseException:
                conn.rollback()
                raise

    def evaluate(
        self,
        policy: SyntheticProactivePolicy,
        *,
        observation_digest: str,
        observed_at_ms: int,
        now_ms: int,
        expected_revision: int,
    ) -> SyntheticProactiveState:
        scope, policy_digest, policy_values = self._policy_identity(policy)
        if type(observation_digest) is not str or not _HEX.fullmatch(observation_digest):
            raise SyntheticProactiveStateRejected("canonical observation digest required")
        _exact_int("observed_at_ms", observed_at_ms)
        _exact_int("now_ms", now_ms)
        _exact_int("expected_revision", expected_revision)
        if observed_at_ms > now_ms:
            raise SyntheticProactiveStateRejected("future observation cannot be evaluated")
        path_epoch = self.path
        with closing(self._connect(read_only=False)) as conn:
            if self.path is not path_epoch:
                raise SyntheticProactiveStateRejected("proactive state path changed before write")
            conn.execute("BEGIN IMMEDIATE")
            try:
                _validate(conn)
                row = conn.execute(
                    "SELECT scope_digest,policy_digest,revision,last_observation_digest,"
                    "last_observed_at_ms,last_evaluated_at_ms,last_proposal_at_ms,"
                    "window_proposal_times_json,last_decision,updated_at_ms,state_sha256 "
                    "FROM synthetic_proactive_states WHERE scope_digest=? AND policy_digest=?",
                    (scope, policy_digest),
                ).fetchone()
                current = None if row is None else _row_state(tuple(row))
                if current is not None:
                    _validate_policy_state(current, policy, scope, policy_digest)
                    if current.revision != expected_revision:
                        raise SyntheticProactiveStateConflict("proactive state CAS revision changed")
                    if now_ms < current.updated_at_ms or now_ms < current.last_evaluated_at_ms:
                        raise SyntheticProactiveStateRejected("proactive state clock regressed")
                    if observed_at_ms < current.last_observed_at_ms:
                        raise SyntheticProactiveStateRejected("proactive observation clock regressed")
                    window = tuple(
                        value for value in current.window_proposal_times
                        if value > now_ms - policy.rolling_window_ms
                    )
                    if observation_digest == current.last_observation_digest:
                        decision = "UNCHANGED"
                        last_observation = current.last_observation_digest
                        last_observed = observed_at_ms
                        last_evaluated = now_ms
                        last_proposal = current.last_proposal_at_ms
                    elif now_ms - current.last_evaluated_at_ms < policy.minimum_interval_ms:
                        decision = "TOO_SOON"
                        last_observation = current.last_observation_digest
                        last_observed = current.last_observed_at_ms
                        last_evaluated = current.last_evaluated_at_ms
                        last_proposal = current.last_proposal_at_ms
                    elif now_ms - current.last_proposal_at_ms < policy.cooldown_ms:
                        decision = "COOLDOWN"
                        last_observation = observation_digest
                        last_observed = observed_at_ms
                        last_evaluated = now_ms
                        last_proposal = current.last_proposal_at_ms
                    elif len(window) >= policy.max_previews_per_window:
                        decision = "WINDOW_BUDGET"
                        last_observation = observation_digest
                        last_observed = observed_at_ms
                        last_evaluated = now_ms
                        last_proposal = current.last_proposal_at_ms
                    else:
                        decision = "ELIGIBLE_PREVIEW"
                        last_observation = observation_digest
                        last_observed = observed_at_ms
                        last_evaluated = now_ms
                        last_proposal = now_ms
                        window = (*window, now_ms)
                    revision = current.revision + 1
                    if revision > _MAX:
                        raise SyntheticProactiveStateRejected("proactive state revision exhausted")
                else:
                    if expected_revision != 0:
                        raise SyntheticProactiveStateConflict("proactive state does not exist at expected revision")
                    decision = "ELIGIBLE_PREVIEW"
                    last_observation = observation_digest
                    last_observed = observed_at_ms
                    last_evaluated = now_ms
                    last_proposal = now_ms
                    window = (now_ms,)
                    revision = 1
                values = _state_values(
                    scope, policy_digest, revision, last_observation,
                    last_observed, last_evaluated, last_proposal, window,
                    decision, now_ms,
                )
                state = _build_state(values)
                _validate_policy_state(state, policy, scope, policy_digest)
                _assert_policy_fields(policy, _POLICY_FIELDS, policy_values)
                if current is None:
                    conn.execute(
                        "INSERT INTO synthetic_proactive_states VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            *values[:7], _canonical_window(window), values[8],
                            values[9], state.state_sha256,
                        ),
                    )
                else:
                    changed = conn.execute(
                        "UPDATE synthetic_proactive_states SET "
                        "revision=?,last_observation_digest=?,last_observed_at_ms=?,"
                        "last_evaluated_at_ms=?,last_proposal_at_ms=?,"
                        "window_proposal_times_json=?,last_decision=?,updated_at_ms=?,"
                        "state_sha256=? WHERE scope_digest=? AND policy_digest=? AND revision=?",
                        (
                            revision, last_observation, last_observed, last_evaluated,
                            last_proposal, _canonical_window(window), decision, now_ms,
                            state.state_sha256, scope, policy_digest, expected_revision,
                        ),
                    )
                    if changed.rowcount != 1:
                        raise SyntheticProactiveStateConflict("proactive state CAS lost")
                _require_original_state_type()
                _assert_policy_fields(policy, _POLICY_FIELDS, policy_values)
                if self.path is not path_epoch:
                    raise SyntheticProactiveStateRejected("proactive state path changed before commit")
                _safe_path(path_epoch)
                conn.commit()
                # COMMIT may be durable even if a later result/path check fails.
                # Inspect read_state before retrying; this method never replays.
                _require_original_state_type()
                _assert_policy_fields(policy, _POLICY_FIELDS, policy_values)
                if self.path is not path_epoch:
                    raise SyntheticProactiveStateRejected("proactive state path changed after commit")
                return state
            except BaseException:
                conn.rollback()
                raise

    def count(self) -> int:
        path_epoch = self.path
        with closing(self._connect(read_only=True)) as conn:
            if self.path is not path_epoch:
                raise SyntheticProactiveStateRejected("proactive state path changed before count")
            conn.execute("BEGIN")
            try:
                _validate(conn)
                result = conn.execute(
                    "SELECT COUNT(*) FROM synthetic_proactive_states"
                ).fetchone()[0]
                if type(result) is not int or not 0 <= result <= _MAX_ROWS:
                    raise SyntheticProactiveStateRejected("proactive state count is invalid")
                if self.path is not path_epoch:
                    raise SyntheticProactiveStateRejected("proactive state path changed during count")
                conn.commit()
                return result
            except BaseException:
                conn.rollback()
                raise
