"""SQLite action audit storing argument digests, never raw arguments."""

from __future__ import annotations

import hashlib
import sqlite3
import stat
import time
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from threading import RLock

from . import contracts as _contracts
from .contracts import ActionAuditEvent, ActionAuditSchemaError, ToolCall, _canonical_json

SCHEMA_VERSION = 1
_EVENT_TYPE = ActionAuditEvent
_ORIGINAL_EVENT_INIT = vars(_EVENT_TYPE)["__init__"]
_EVENT_FIELDS = (
    "event_id", "request_id", "tool", "capability", "scope",
    "arguments_sha256", "outcome", "occurred_at_ms",
)
_ORIGINAL_EVENT_FIELDS = tuple(vars(_EVENT_TYPE)[name] for name in _EVENT_FIELDS)
_EVENT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_EVENT_HOOKS = tuple(vars(_EVENT_TYPE).get(name) for name in _EVENT_HOOKS)
# Local callbacks may be rebound after a ToolCall is constructed. Before
# touching its private argument mapping or stored audit identities, validate
# both the audit-side and ToolCall-side canonical digest pipeline.
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_CANONICAL_JSON = _canonical_json
_ORIGINAL_TOOLCALL_JSON = _contracts._canonical_json
_ORIGINAL_TOOLCALL_FREEZE = _contracts._freeze_json
_ORIGINAL_JSON_DUMPS = _contracts.json.dumps
_SQLITE_INT_MAX = 2**63 - 1
_AUDIT_BOOTSTRAP_LOCK = RLock()  # same-process path preflight and WAL bootstrap

_AUDIT_SCHEMA_V1_SQL = """CREATE TABLE action_events(
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id TEXT NOT NULL,
                        tool TEXT NOT NULL,
                        capability TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        arguments_sha256 TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        occurred_at_ms INTEGER NOT NULL
                    );
                    CREATE INDEX idx_action_request ON action_events(request_id,event_id);
                    PRAGMA user_version=1;"""


def _normalized_ddl(sql: str | None) -> str | None:
    """Ignore unquoted formatting only; quoted SQL and CHECK values stay exact."""
    if sql is None:
        return None
    output: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(sql):
        char = sql[index]
        if quote is not None:
            output.append(char)
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    index += 1
                    output.append(sql[index])
                else:
                    quote = None
        elif char in ("'", '"', "`"):
            quote = char
            output.append(char)
        elif not char.isspace():
            output.append(char.lower())
        index += 1
    if quote is not None:
        raise ActionAuditSchemaError("unterminated SQLite audit schema quotation")
    return "".join(output)


def _schema_objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    rows = conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).fetchall()
    return tuple((row[0], row[1], row[2], _normalized_ddl(row[3])) for row in rows)


def _validate_v1_schema(conn: sqlite3.Connection) -> None:
    """Startup-only v1 audit DDL and quick_check gate; never auto-repair."""
    try:
        quick = conn.execute("PRAGMA quick_check").fetchall()
        if len(quick) != 1 or tuple(quick[0]) != ("ok",):
            raise ActionAuditSchemaError("action audit SQLite quick_check failed")
        with sqlite3.connect(":memory:") as expected:
            expected.executescript(_AUDIT_SCHEMA_V1_SQL)
            if _schema_objects(conn) != _schema_objects(expected):
                raise ActionAuditSchemaError(
                    "action audit v1 schema differs from original DDL"
                )
    except sqlite3.DatabaseError as exc:
        raise ActionAuditSchemaError("action audit schema cannot be verified") from exc



def _validate_tail_identity(row: sqlite3.Row) -> int:
    """Fail closed on a malformed persisted tail before appending evidence.

    The original v1 schema is unchanged. This is a local consistency check,
    not an authenticated event hash chain or a full historical audit.
    """
    _require_original_event_constructor()
    event_id = row["event_id"]
    occurred = row["occurred_at_ms"]
    if type(event_id) is not int or event_id < 1:
        raise ActionAuditSchemaError("audit persisted tail has invalid event")
    if type(occurred) is not int or occurred < 0:
        raise ActionAuditSchemaError(
            "audit clock regressed or persisted tail clock is malformed"
        )
    fields = (
        "request_id", "tool", "capability", "scope",
        "arguments_sha256", "outcome",
    )
    values = tuple(row[column] for column in fields)
    if any(type(value) is not str or not value.strip() for value in values):
        raise ActionAuditSchemaError("audit persisted tail identity is malformed")
    request_id, tool, capability, scope, args_hash, _outcome = values
    if (
        len(request_id) != 68 or not request_id.startswith("act_")
        or any(char not in "0123456789abcdef" for char in request_id[4:])
        or len(args_hash) != 64
        or any(char not in "0123456789abcdef" for char in args_hash)
    ):
        raise ActionAuditSchemaError("audit persisted tail digest is malformed")
    expected = "act_" + hashlib.sha256(_canonical_json({
        "arguments_sha256": args_hash,
        "capability": capability,
        "scope": scope,
        "tool": tool,
    })).hexdigest()
    if expected != request_id:
        raise ActionAuditSchemaError("audit persisted tail request identity is inconsistent")
    return occurred



def _require_dense_committed_audit_sequence(conn: sqlite3.Connection) -> None:
    """Refuse append after local audit event loss, including deleted tails.

    The AUTOINCREMENT high-water mark is only a local consistency signal:
    it is not authenticated history and can itself be rewritten by an actor
    with SQLite write access. No audit deletion/compaction is part of v1.
    Keep this check in the SAME BEGIN IMMEDIATE transaction as the append.
    """
    count, first, last = conn.execute(
        "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM action_events"
    ).fetchone()
    sequences = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
    ).fetchall()
    if type(count) is not int or count < 0:
        raise ActionAuditSchemaError("audit persisted event sequence is malformed")
    if count == 0:
        if sequences:
            raise ActionAuditSchemaError("audit append-only history was truncated")
    elif (
        type(first) is not int or first != 1
        or type(last) is not int or last != count
        # sqlite_sequence.name is not UNIQUE. The first row can appear
        # correct even when a second forged high-water marker is present.
        or len(sequences) != 1 or type(sequences[0][0]) is not int
        or sequences[0][0] != last
    ):
        raise ActionAuditSchemaError("audit append-only event ID gap or tail loss")




def _require_valid_committed_audit_history(conn: sqlite3.Connection) -> None:
    """Refuse to extend a locally inconsistent audit prefix.

    Dense IDs alone do not detect historical identity rewrites or chronology
    regressions outside the latest row. Inspect the complete pre-append prefix
    in the same SQLite writer transaction. This is local consistency only:
    SQLite rows/high-water are not independently authenticated evidence.
    """
    previous_clock: int | None = None
    for row in conn.execute("SELECT * FROM action_events ORDER BY event_id"):
        clock = _validate_tail_identity(row)
        if previous_clock is not None and clock < previous_clock:
            raise ActionAuditSchemaError(
                "audit clock regressed relative to persisted events"
            )
        previous_clock = clock


def _require_original_event_constructor(phase: str = "") -> None:
    if (
        hashlib.sha256 is not _ORIGINAL_SHA256
        or _canonical_json is not _ORIGINAL_CANONICAL_JSON
        or _contracts._canonical_json is not _ORIGINAL_TOOLCALL_JSON
        or _contracts._freeze_json is not _ORIGINAL_TOOLCALL_FREEZE
        or _contracts.json.dumps is not _ORIGINAL_JSON_DUMPS
    ):
        raise ActionAuditSchemaError("action audit digest callback changed")
    # An audit receipt is data, not a place to execute new Python code.
    # Reflectively replacing a slotted field can install an executable
    # descriptor. Inspect the ORIGINAL class dictionary without getattr(),
    # before opening SQLite, hydrating rows or constructing a receipt.
    if (
        ActionAuditEvent is not _EVENT_TYPE
        or vars(_EVENT_TYPE).get("__init__") is not _ORIGINAL_EVENT_INIT
        or any(
            vars(_EVENT_TYPE).get(name) is not original
            for name, original in zip(
                _EVENT_FIELDS, _ORIGINAL_EVENT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_EVENT_TYPE).get(name) is not original
            for name, original in zip(
                _EVENT_HOOKS, _ORIGINAL_EVENT_HOOKS, strict=True,
            )
        )
    ):
        suffix = f" {phase}" if phase else ""
        raise ActionAuditSchemaError(f"audit event constructor changed{suffix}")


def _require_safe_audit_path(path: Path, *, allow_new_parents: bool) -> None:
    """Refuse local audit path aliases before any SQLite open or mkdir.

    Existing ancestors must be real directories, not symbolic links. Bootstrap
    may create missing directories as before, but cannot create them *through*
    a preexisting symbolic ancestor. This preflight is NOT atomic dirfd custody,
    authenticated history or protection from later owner-controlled renames.
    """
    if type(path) is not type(Path()) or ".." in path.parts:
        raise ActionAuditSchemaError("audit path type or parent traversal refused")
    # Bound private paths BEFORE mkdir/lstat/SQLite; leave room for SQLite's
    # longest journal suffix even when the main database path fits.
    raw = str(path)
    if not path.name or "\x00" in raw or len(raw) > 4096:
        raise ActionAuditSchemaError("audit database path exceeds local fixture limits")
    target = path if path.is_absolute() else path.absolute()
    if len(str(target)) + len("-journal") > 4096:
        raise ActionAuditSchemaError("audit database/sidecar path exceeds local fixture limits")
    try:
        for ancestor in target.parents:
            try:
                meta = ancestor.lstat()
            except FileNotFoundError:
                if allow_new_parents:
                    continue
                raise ActionAuditSchemaError("audit ancestor unavailable") from None
            if not stat.S_ISDIR(meta.st_mode) or stat.S_ISLNK(meta.st_mode):
                raise ActionAuditSchemaError("audit symbolic or nondirectory ancestor refused")
        if target.is_symlink():
            raise ActionAuditSchemaError("audit symbolic path refused")
        main_exists = target.exists()
        if main_exists:
            meta = target.lstat()
            if not stat.S_ISREG(meta.st_mode) or meta.st_nlink != 1:
                raise ActionAuditSchemaError("audit path must have one regular-file link")
        # SQLite can open a journal, WAL or shared-memory sidecar even when
        # its main file has a safe pathname. Refuse aliased special sidecars
        # and do not adopt orphaned journal bytes when bootstrapping.
        # These are repeated local lstat checks, not atomic dirfd custody.
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = target.with_name(target.name + suffix)
            try:
                sidecar_info = sidecar.lstat()
            except FileNotFoundError:
                continue
            if not main_exists:
                raise ActionAuditSchemaError("orphaned audit SQLite sidecar refused")
            if not stat.S_ISREG(sidecar_info.st_mode) or sidecar_info.st_nlink != 1:
                # Report bounded metadata only. Never include the audit DB
                # pathname, request identifiers, arguments or row contents.
                # This identifies the rejected file class in a real process
                # race without relaxing the no-alias policy or retrying I/O.
                raise ActionAuditSchemaError(
                    "audit SQLite sidecar alias refused "
                    f"(suffix={suffix}, file_type={stat.S_IFMT(sidecar_info.st_mode):#o}, "
                    f"link_count={sidecar_info.st_nlink})"
                )
    except OSError as exc:
        raise ActionAuditSchemaError("audit path custody cannot be verified") from exc


class SQLiteActionAudit:
    def __init__(self, path: str | Path, *, clock_ms: Callable[[], int] | None = None) -> None:
        if type(path) not in (str, type(Path("."))):
            raise ActionAuditSchemaError("audit requires exact local path")
        self.path = Path(path)
        # The first-open parent/main/sidecar checks and WAL negotiation must
        # form one same-process bootstrap epoch. Otherwise a second constructor
        # can mistake transient journal creation for an orphaned audit sidecar.
        # This reentrant lock preserves _initialize()'s standalone guard,
        # without asserting cross-process or atomic filesystem path custody.
        with _AUDIT_BOOTSTRAP_LOCK:
            _require_safe_audit_path(self.path, allow_new_parents=True)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            _require_safe_audit_path(self.path, allow_new_parents=False)
            self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
            self._initialize()

    def append(self, call: ToolCall, *, outcome: str) -> ActionAuditEvent:
        _require_original_event_constructor()
        if type(call) is not ToolCall:
            raise TypeError("audit call must be an exact ToolCall")
        if type(outcome) is not str or not outcome.strip():
            raise ValueError("outcome must be a non-empty exact string")
        # Freeze the action identity before a reentrant clock callback. Frozen
        # dataclasses can still be modified by reflection; never mix fields
        # from before/after callback in a persisted audit event.
        try:
            checked = ToolCall(call.tool, call.capability, call.scope, call.arguments)
            identity = (
                checked.request_id, checked.tool, checked.capability,
                checked.scope, checked.arguments_sha256,
            )
            if identity != (
                call.request_id, call.tool, call.capability, call.scope,
                call.arguments_sha256,
            ):
                raise ActionAuditSchemaError("audit call identity is inconsistent")
        except (TypeError, ValueError) as exc:
            raise ActionAuditSchemaError("audit call identity is invalid") from exc
        original_arguments = call.arguments
        original_subject = (call.tool, call.capability, call.scope)
        path_epoch = self.path

        def assert_action_epoch(phase: str) -> None:
            _require_original_event_constructor(phase)
            try:
                stable = (
                    call.arguments is original_arguments
                    and call.tool is original_subject[0]
                    and call.capability is original_subject[1]
                    and call.scope is original_subject[2]
                    and (
                        call.request_id, call.tool, call.capability,
                        call.scope, call.arguments_sha256,
                    ) == identity
                )
            except (TypeError, ValueError, AttributeError) as exc:
                raise ActionAuditSchemaError(
                    f"audit call identity became invalid {phase}"
                ) from exc
            if not stable:
                raise ActionAuditSchemaError(f"audit call changed {phase}")

        with closing(self._connect()) as conn, conn:
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit path changed before append")
            # Commit an event with a clock sampled only after acquiring the
            # writer slot; no external backend dispatch is performed here.
            conn.execute("BEGIN IMMEDIATE")
            # The file may be replaced or its schema altered after startup.
            # Revalidate under the same transaction that will append the event.
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if type(version) is not int or version != SCHEMA_VERSION:
                raise ActionAuditSchemaError("action audit schema version changed before append")
            _validate_v1_schema(conn)
            _require_dense_committed_audit_sequence(conn)
            # An intact tail does not certify earlier audit events. Validate
            # the entire persisted prefix before sampling the action clock.
            _require_valid_committed_audit_history(conn)
            now = self._now()
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit path changed during clock")
            assert_action_epoch("during clock")
            # Audit-before-action requires chronological continuity across
            # process restarts, not merely a well-shaped current wall-time.
            # Read the last committed clock inside the SAME SQLite writer
            # transaction; an earlier, newer timestamp must never be
            # silently followed by a rollback in the evidence chain.
            previous_tail = conn.execute(
                "SELECT * FROM action_events ORDER BY event_id DESC LIMIT 1"
            ).fetchone()
            if previous_tail is not None:
                previous_clock = _validate_tail_identity(previous_tail)
                if now < previous_clock:
                    raise ActionAuditSchemaError(
                        "audit clock regressed relative to persisted events"
                    )
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit path changed during clock review")
            assert_action_epoch("after clock review")
            _require_original_event_constructor()
            cursor = conn.execute(
                """INSERT INTO action_events(
                    request_id,tool,capability,scope,arguments_sha256,outcome,occurred_at_ms
                ) VALUES(?,?,?,?,?,?,?)""",
                (
                    *identity,
                    outcome,
                    now,
                ),
            )
            event_id = int(cursor.lastrowid)
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit path changed before commit")
            # A reentrant INSERT callback must not change the original
            # action carrier after the SQL parameters were captured.
            assert_action_epoch("before commit")
            _require_original_event_constructor()
        # COMMIT has already happened. Deny a clean result on late source or
        # input drift, but never claim rollback or automatically retry.
        if self.path is not path_epoch:
            raise ActionAuditSchemaError("action audit path changed after commit")
        assert_action_epoch("after commit")
        _require_original_event_constructor("after commit")
        event = _EVENT_TYPE(event_id, *identity, outcome, now)
        _require_original_event_constructor("after commit")
        if self.path is not path_epoch:
            raise ActionAuditSchemaError("action audit path changed after commit")
        assert_action_epoch("after commit")
        if (
            type(event) is not ActionAuditEvent
            or event.event_id is not event_id
            or event.request_id is not identity[0]
            or event.tool is not identity[1]
            or event.capability is not identity[2]
            or event.scope is not identity[3]
            or event.arguments_sha256 is not identity[4]
            or event.outcome is not outcome
            or event.occurred_at_ms is not now
        ):
            raise ActionAuditSchemaError(
                "constructed action audit event changed after commit"
            )
        return event

    def events(self, *, after_event_id: int = 0, limit: int = 100) -> list[ActionAuditEvent]:
        _require_original_event_constructor()
        if (
            type(after_event_id) is not int
            or not 0 <= after_event_id <= _SQLITE_INT_MAX
        ):
            raise ValueError("after_event_id must fit a non-negative SQLite INTEGER")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer from 1 to 1000")
        # The audit object may outlive the SQLite file. Never create an empty
        # replacement database while reading evidence from a stale path.
        # A reflected equal-value Path replacement is still a new evidence
        # epoch, even when it names the same SQLite bytes.
        path_epoch = self.path
        with closing(self._connect_readonly()) as conn:
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit source changed before read")
            # Pin a single read snapshot and refuse post-startup DDL drift.
            conn.execute("BEGIN")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if type(version) is not int or version != SCHEMA_VERSION:
                raise ActionAuditSchemaError("action audit schema version changed before read")
            _validate_v1_schema(conn)
            # A valid-looking page cannot certify a locally truncated audit.
            # Check the entire append-only ID extent and AUTOINCREMENT tip
            # inside this SAME read snapshot before returning any evidence.
            # This is only local consistency, not authenticated custody.
            _require_dense_committed_audit_sequence(conn)
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit source changed during read")
            rows = conn.execute(
                """SELECT * FROM action_events WHERE event_id>?
                ORDER BY event_id LIMIT ?""",
                (after_event_id, limit),
            ).fetchall()
            # A paged read must compare the first returned timestamp against
            # its persisted predecessor, not only against later page entries.
            # Keep both queries in the same SQLite read transaction.
            predecessor = (
                conn.execute(
                    "SELECT occurred_at_ms FROM action_events "
                    "WHERE event_id<=? ORDER BY event_id DESC LIMIT 1",
                    (after_event_id,),
                ).fetchone()
                if after_event_id else None
            )
            # A valid selected page is not evidence that unseen earlier or
            # later rows are locally consistent. Scan the retained prefix in
            # this SAME read snapshot. Preserve page-specific diagnostics by
            # reporting the prefix error only after validating selected rows.
            history_error: ActionAuditSchemaError | None = None
            try:
                _require_valid_committed_audit_history(conn)
            except ActionAuditSchemaError as exc:
                history_error = exc
            if self.path is not path_epoch:
                raise ActionAuditSchemaError("action audit source changed during read")
        # Read persisted rows without SQLite's permissive Python coercions.
        # A digest is only a shape check here; it does not attest the issuer
        # or bind back to plaintext arguments that are deliberately not stored.
        result: list[ActionAuditEvent] = []
        previous_id = after_event_id
        previous_clock = predecessor[0] if predecessor is not None else None
        if previous_clock is not None and (
            type(previous_clock) is not int or previous_clock < 0
        ):
            raise ActionAuditSchemaError("audit preceding clock is malformed")
        for row in rows:
            event_id = row["event_id"]
            occurred = row["occurred_at_ms"]
            if type(event_id) is not int or event_id <= previous_id:
                raise ActionAuditSchemaError("audit event_id must increase as INTEGER")
            previous_id = event_id
            if type(occurred) is not int or occurred < 0:
                raise ActionAuditSchemaError("audit clock must be a non-negative INTEGER")
            if previous_clock is not None and occurred < previous_clock:
                raise ActionAuditSchemaError("audit stored clocks regressed")
            previous_clock = occurred
            fields = ("request_id", "tool", "capability", "scope", "arguments_sha256", "outcome")
            values = [row[column] for column in fields]
            if any(type(value) is not str or not value.strip() for value in values):
                raise ActionAuditSchemaError("audit identity fields must be non-empty TEXT")
            request_id, tool, capability, scope, arguments_sha256, outcome = values
            if (
                len(request_id) != 68 or not request_id.startswith("act_")
                or any(char not in "0123456789abcdef" for char in request_id[4:])
                or len(arguments_sha256) != 64
                or any(char not in "0123456789abcdef" for char in arguments_sha256)
            ):
                raise ActionAuditSchemaError("audit stored digest identity is invalid")
            # The audit intentionally stores no raw ToolCall.arguments, but
            # the deterministic request ID can still be recomputed from its
            # separately persisted argument digest and identity fields.
            # Reject self-contradictory, individually well-formed row values.
            _require_original_event_constructor("before read digest")
            expected_request_id = "act_" + hashlib.sha256(_canonical_json({
                "arguments_sha256": arguments_sha256,
                "capability": capability,
                "scope": scope,
                "tool": tool,
            })).hexdigest()
            if request_id != expected_request_id:
                raise ActionAuditSchemaError("audit stored request identity is inconsistent")
            _require_original_event_constructor()
            event = _EVENT_TYPE(
                event_id, request_id, tool, capability, scope, arguments_sha256,
                outcome, occurred,
            )
            _require_original_event_constructor()
            if (
                type(event) is not _EVENT_TYPE
                or event.event_id is not event_id
                or event.request_id is not request_id
                or event.tool is not tool
                or event.capability is not capability
                or event.scope is not scope
                or event.arguments_sha256 is not arguments_sha256
                or event.outcome is not outcome
                or event.occurred_at_ms is not occurred
            ):
                raise ActionAuditSchemaError("audit read event changed during hydration")
            result.append(event)
        if self.path is not path_epoch:
            raise ActionAuditSchemaError("action audit source changed during hydration")
        if history_error is not None:
            raise history_error
        _require_original_event_constructor()
        return result

    def _initialize(self) -> None:
        with _AUDIT_BOOTSTRAP_LOCK, closing(self._connect(create=True)) as conn, conn:
            # WAL negotiation is bootstrap-only. Under concurrent first opens,
            # retry transient SQLite lock/busy before taking the writer slot.
            for attempt in range(5):
                try:
                    journal_mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
                except sqlite3.OperationalError as exc:
                    error_code = getattr(exc, "sqlite_errorcode", 0) & 0xFF
                    if error_code not in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
                        raise
                    if attempt == 4:
                        raise
                    time.sleep(0.05 * (2 ** attempt))
                else:
                    if journal_mode.lower() != "wal":
                        raise ActionAuditSchemaError("action audit SQLite WAL negotiation failed")
                    break
            # Bootstrap must be atomic: executescript() implicitly commits and
            # could leave a partially initialized audit if verification fails.
            conn.execute("BEGIN IMMEDIATE")
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version < 0:
                raise ActionAuditSchemaError(
                    f"unsupported negative action audit schema version {version}"
                )
            if version > SCHEMA_VERSION:
                raise ActionAuditSchemaError(
                    f"action audit schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == 0:
                # Never treat another or a partially initialized database as
                # an empty audit. There is no implicit repair or migration.
                existing = conn.execute(
                    "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    raise ActionAuditSchemaError("unversioned action audit database is not empty")
                for statement in _AUDIT_SCHEMA_V1_SQL.split(";"):
                    if statement.strip():
                        conn.execute(statement)
            _validate_v1_schema(conn)

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        _require_safe_audit_path(self.path, allow_new_parents=False)
        # Explicit bootstrap may create a new SQLite file. Ordinary audit
        # appends MUST NOT recreate an empty replacement after a file moves.
        if create:
            conn = sqlite3.connect(self.path)
        else:
            conn = sqlite3.connect(
                self.path.resolve().as_uri() + "?mode=rw", uri=True
            )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _connect_readonly(self) -> sqlite3.Connection:
        _require_safe_audit_path(self.path, allow_new_parents=False)
        try:
            conn = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
        except sqlite3.DatabaseError as exc:
            raise ActionAuditSchemaError("action audit read-only file is unavailable") from exc
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _now(self) -> int:
        value = self._clock_ms()
        if type(value) is not int or not 0 <= value <= _SQLITE_INT_MAX:
            raise ValueError(
                "clock_ms must return a non-negative integer within SQLite INTEGER range"
            )
        return value
