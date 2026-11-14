"""Local-only CAS event store for *synthetic* improvement proposal reviews.

This store contains proposal IDs, state names, revisions and hashes only. It
cannot establish human approval, authenticate owners, execute changes, train,
promote models or open protected evaluation. An independently retained witness
is necessary to notice a rolled-back prefix; a local digest is not a signature.
After COMMIT-UNKNOWN, do not retry a proposed action automatically.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from ark.agency import disconnected_proposal_lifecycle as lifecycle

_DOMAIN = b"ARK-disconnected-proposal-store-v1\0"
_MAX_ROWS = 512
_DDL = (
    "CREATE TABLE synthetic_proposal_events ("
    "seq INTEGER PRIMARY KEY, proposal_id TEXT NOT NULL, "
    "revision INTEGER NOT NULL, prior_state TEXT NOT NULL, "
    "new_state TEXT NOT NULL, previous_digest TEXT NOT NULL, "
    "event_digest TEXT NOT NULL, global_digest TEXT NOT NULL, "
    "UNIQUE(proposal_id,revision))"
)


class DisconnectedProposalStoreRejected(ValueError):
    """A local proposal history, path or optimistic revision is not safe."""


@dataclass(frozen=True, slots=True)
class DetachedProposalStoreWitness:
    event_count: int
    chain_digest: str

    @property
    def externally_authenticated(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class DetachedProposalStoreSnapshot:
    witness: DetachedProposalStoreWitness
    proposal_tip: lifecycle.DetachedProposalLifecycleTip | None

    @property
    def human_review_authenticated(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def candidate_promotion_authorized(self) -> bool:
        return False


_WITNESS = DetachedProposalStoreWitness
_SNAPSHOT = DetachedProposalStoreSnapshot
_FIELDS = ("event_count", "chain_digest")
_SNAPSHOT_FIELDS = ("witness", "proposal_tip")
_WITNESS_DENIAL = vars(_WITNESS)["externally_authenticated"]
_SNAPSHOT_DENIALS = tuple(
    vars(_SNAPSHOT)[name] for name in (
        "human_review_authenticated", "execution_authorized",
        "candidate_promotion_authorized",
    )
)
_WITNESS_DESCRIPTORS = tuple(vars(_WITNESS)[name] for name in _FIELDS)
_SNAPSHOT_DESCRIPTORS = tuple(vars(_SNAPSHOT)[name] for name in _SNAPSHOT_FIELDS)
# Both dataclasses are frozen only per instance. A hostile class-level
# __getattribute__ or __getattr__ substitution can execute before the first
# private witness or snapshot field read. Refuse even a false-returning hook.
_CARRIER_LOOKUP_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_WITNESS_LOOKUP_DESCRIPTORS = tuple(
    vars(_WITNESS).get(name) for name in _CARRIER_LOOKUP_HOOKS
)
_SNAPSHOT_LOOKUP_DESCRIPTORS = tuple(
    vars(_SNAPSHOT).get(name) for name in _CARRIER_LOOKUP_HOOKS
)
_ORIGINAL_WITNESS_INIT = vars(_WITNESS)["__init__"]
_ORIGINAL_SNAPSHOT_INIT = vars(_SNAPSHOT)["__init__"]
_ORIGINAL_CONNECT = sqlite3.connect
_ORIGINAL_OS_OPEN = os.open
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_DDL = _DDL
_ORIGINAL_LIFECYCLE = (
    lifecycle._id, lifecycle.DetachedProposalTransition,
    lifecycle.DetachedProposalLifecycleTip,
    lifecycle.replay_disconnected_proposal_lifecycle,
    lifecycle.prepare_disconnected_proposal_transition,
)


def _protocol() -> None:
    if (
        DetachedProposalStoreWitness is not _WITNESS
        or DetachedProposalStoreSnapshot is not _SNAPSHOT
        or vars(_WITNESS).get("__init__") is not _ORIGINAL_WITNESS_INIT
        or vars(_SNAPSHOT).get("__init__") is not _ORIGINAL_SNAPSHOT_INIT
        or vars(_WITNESS).get("externally_authenticated") is not _WITNESS_DENIAL
        or tuple(vars(_SNAPSHOT).get(name) for name in (
            "human_review_authenticated", "execution_authorized",
            "candidate_promotion_authorized",
        )) != _SNAPSHOT_DENIALS
        or any(vars(_WITNESS).get(name) is not original for name, original in zip(
            _FIELDS, _WITNESS_DESCRIPTORS, strict=True,
        ))
        or any(vars(_SNAPSHOT).get(name) is not original for name, original in zip(
            _SNAPSHOT_FIELDS, _SNAPSHOT_DESCRIPTORS, strict=True,
        ))
        or any(vars(_WITNESS).get(name) is not original for name, original in zip(
            _CARRIER_LOOKUP_HOOKS, _WITNESS_LOOKUP_DESCRIPTORS, strict=True,
        ))
        or any(vars(_SNAPSHOT).get(name) is not original for name, original in zip(
            _CARRIER_LOOKUP_HOOKS, _SNAPSHOT_LOOKUP_DESCRIPTORS, strict=True,
        ))
        or sqlite3.connect is not _ORIGINAL_CONNECT
        or os.open is not _ORIGINAL_OS_OPEN
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN or _DDL is not _ORIGINAL_DDL
        or type(_MAX_ROWS) is not int or _MAX_ROWS != 512
        or (
            lifecycle._id, lifecycle.DetachedProposalTransition,
            lifecycle.DetachedProposalLifecycleTip,
            lifecycle.replay_disconnected_proposal_lifecycle,
            lifecycle.prepare_disconnected_proposal_transition,
        ) != _ORIGINAL_LIFECYCLE
    ):
        raise DisconnectedProposalStoreRejected("proposal store protocol changed")


def _hash(payload: tuple[object, ...]) -> str:
    _protocol()
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(_DOMAIN + encoded.encode("ascii")).hexdigest()


def genesis_disconnected_proposal_witness() -> DetachedProposalStoreWitness:
    """Genesis token for a newly initialized *empty* fixture, not approval."""
    return DetachedProposalStoreWitness(0, _hash(("genesis",)))


def _witness(value: object) -> tuple[int, str]:
    _protocol()
    if type(value) is not DetachedProposalStoreWitness:
        raise DisconnectedProposalStoreRejected("exact retained store witness required")
    count, digest = value.event_count, value.chain_digest
    if (
        type(count) is not int or not 0 <= count <= _MAX_ROWS
        or type(digest) is not str or len(digest) != 64
        or any(c not in "0123456789abcdef" for c in digest)
        or value.externally_authenticated is not False
    ):
        raise DisconnectedProposalStoreRejected("invalid retained store witness")
    return count, digest


def _tip(value: object, proposal_id: str) -> tuple[int, str, str] | None:
    _protocol()
    if value is None:
        return None
    if type(value) is not lifecycle.DetachedProposalLifecycleTip:
        raise DisconnectedProposalStoreRejected("invalid expected proposal tip")
    if (
        type(value.proposal_id) is not str or value.proposal_id != proposal_id
        or type(value.revision) is not int
        or type(value.state) is not str
        or type(value.event_digest) is not str
        or any(getattr(value, field) is not False for field in (
            "human_review_authenticated", "code_change_authorized",
            "candidate_promotion_authorized", "training_authorized",
            "protected_evaluation_opened",
        ))
    ):
        raise DisconnectedProposalStoreRejected("invalid expected proposal tip")
    return value.revision, value.state, value.event_digest


_SQLITE_SIDECARS = ("-wal", "-shm", "-journal")


def _sidecar_integrity(path: Path, *, create: bool) -> None:
    """Refuse aliased SQLite sidecars before any SQLite call.

    Normal single-link regular WAL/SHM/journal files may be present while
    another local connection is alive. Creation refuses every stale sidecar.
    This check does not claim atomic race resistance or trusted storage.
    """
    for suffix in _SQLITE_SIDECARS:
        sidecar = path.with_name(path.name + suffix)
        try:
            info = sidecar.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise DisconnectedProposalStoreRejected(
                "proposal SQLite sidecar unavailable"
            ) from exc
        if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise DisconnectedProposalStoreRejected("unsafe proposal SQLite sidecar")


def _path(path: object, *, create: bool) -> Path:
    if (
        type(path) is not type(Path.cwd())
        or not path.is_absolute() or ".." in path.parts
        or not path.name or len(str(path)) > 4096 or "\x00" in str(path)
    ):
        raise DisconnectedProposalStoreRejected("exact absolute local file path required")
    # SQLite can access a -journal sibling after opening the main database.
    # Limit native filesystem bytes, not just Unicode codepoints, before lstat.
    try:
        encoded_size = len(os.fsencode(path))
    except (UnicodeError, ValueError, OSError) as exc:
        raise DisconnectedProposalStoreRejected(
            "proposal SQLite path encoding invalid"
        ) from exc
    if encoded_size + len(b"-journal") > 4096:
        raise DisconnectedProposalStoreRejected("proposal SQLite path byte budget exceeded")
    try:
        for ancestor in path.parents:
            mode = ancestor.lstat().st_mode
            if not stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
                raise DisconnectedProposalStoreRejected("unsafe parent path")
        try:
            info = path.lstat()
        except FileNotFoundError:
            if not create:
                raise DisconnectedProposalStoreRejected("missing proposal fixture") from None
        else:
            if create or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise DisconnectedProposalStoreRejected("unsafe or aliased proposal file")
        _sidecar_integrity(path, create=create)
    except OSError as exc:
        raise DisconnectedProposalStoreRejected("proposal fixture path unavailable") from exc
    return path


def _schema(conn: sqlite3.Connection) -> None:
    _protocol()
    if conn.execute("PRAGMA user_version").fetchone() != (1,):
        raise DisconnectedProposalStoreRejected("proposal schema version mismatch")
    # A foreign SQLite catalog may carry unbounded DDL. Enforce the exact
    # table + generated UNIQUE index and a byte budget in this transaction
    # before any catalog SQL is materialized in Python.
    budget = conn.execute(
        "SELECT COUNT(*),COALESCE(SUM(length(CAST(sql AS BLOB))),0) "
        "FROM sqlite_master"
    ).fetchone()
    if (
        type(budget) is not tuple or len(budget) != 2
        or type(budget[0]) is not int or budget[0] != 2
        or type(budget[1]) is not int or not 0 <= budget[1] <= 4_096
    ):
        raise DisconnectedProposalStoreRejected(
            "proposal schema catalog preflight failed (schema changed)"
        )
    with closing(sqlite3.connect(":memory:")) as reference:
        reference.execute(_DDL)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(query)) != tuple(reference.execute(query)):
            raise DisconnectedProposalStoreRejected("proposal schema changed")
    # Reject even a valid first diagnostic followed by corruption; do not
    # hydrate an unbounded SQLite error inventory from a malformed store.
    quick = conn.execute("PRAGMA quick_check").fetchmany(2)
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise DisconnectedProposalStoreRejected("proposal SQLite integrity failure")


def _scan(conn: sqlite3.Connection) -> tuple[
    DetachedProposalStoreWitness,
    dict[str, tuple[lifecycle.DetachedProposalTransition, ...]],
    tuple[DetachedProposalStoreWitness, ...],
]:
    _protocol()
    _schema(conn)
    # Bound both row count and each stored identity BEFORE Python sees a row.
    # This is one SQLite transaction snapshot; it does not authenticate writers.
    persisted_count = conn.execute(
        "SELECT COUNT(*) FROM synthetic_proposal_events"
    ).fetchone()[0]
    if type(persisted_count) is not int or not 0 <= persisted_count <= _MAX_ROWS:
        raise DisconnectedProposalStoreRejected("proposal persisted row budget exceeded")
    malformed = conn.execute(
        "SELECT 1 FROM synthetic_proposal_events WHERE "
        "typeof(seq)!='integer' OR typeof(revision)!='integer' OR "
        "typeof(proposal_id)!='text' OR "
        "length(CAST(proposal_id AS BLOB))!=73 OR "
        "typeof(prior_state)!='text' OR "
        "length(CAST(prior_state AS BLOB)) NOT BETWEEN 1 AND 32 OR "
        "typeof(new_state)!='text' OR "
        "length(CAST(new_state AS BLOB)) NOT BETWEEN 1 AND 32 OR "
        "typeof(previous_digest)!='text' OR "
        "length(CAST(previous_digest AS BLOB))!=64 OR "
        "typeof(event_digest)!='text' OR "
        "length(CAST(event_digest AS BLOB))!=64 OR "
        "typeof(global_digest)!='text' OR "
        "length(CAST(global_digest AS BLOB))!=64 LIMIT 1"
    ).fetchone()
    if malformed is not None:
        raise DisconnectedProposalStoreRejected(
            "proposal persisted event hydration admission failed"
        )
    witness = genesis_disconnected_proposal_witness()
    prefixes = [witness]
    histories: dict[str, tuple[lifecycle.DetachedProposalTransition, ...]] = {}
    for row in conn.execute(
        "SELECT seq,proposal_id,revision,prior_state,new_state,"
        "previous_digest,event_digest,global_digest "
        "FROM synthetic_proposal_events ORDER BY seq"
    ):
        if len(row) != 8:
            raise DisconnectedProposalStoreRejected("malformed proposal event")
        seq, proposal_id, revision, old, new, previous, digest, global_digest = row
        if type(seq) is not int or seq != witness.event_count + 1 or seq > _MAX_ROWS:
            raise DisconnectedProposalStoreRejected("proposal global sequence drift")
        # The replay function validates exact proposal identity, fields,
        # event digest, state transitions and contiguous per-proposal revision.
        event = lifecycle.DetachedProposalTransition(
            proposal_id, revision, old, new, previous, digest,
        )
        history = (*histories.get(proposal_id, ()), event)
        try:
            lifecycle.replay_disconnected_proposal_lifecycle(proposal_id, history)
        except (lifecycle.DisconnectedProposalLifecycleRejected, TypeError) as exc:
            raise DisconnectedProposalStoreRejected("proposal transition history drift") from exc
        wanted = _hash(("event", witness.chain_digest, *row[:7]))
        if type(global_digest) is not str or global_digest != wanted:
            raise DisconnectedProposalStoreRejected("proposal global chain drift")
        _protocol()
        histories[proposal_id] = history
        witness = DetachedProposalStoreWitness(seq, wanted)
        prefixes.append(witness)
    return witness, histories, tuple(prefixes)


def _assert_retained(
    retained: tuple[int, str], prefixes: tuple[DetachedProposalStoreWitness, ...],
    *, latest_required: bool,
) -> None:
    count, digest = retained
    if count >= len(prefixes) or prefixes[count].chain_digest != digest:
        raise DisconnectedProposalStoreRejected("retained proposal prefix mismatch")
    if latest_required and count != len(prefixes) - 1:
        raise DisconnectedProposalStoreRejected("stale proposal global CAS witness")


def create_disconnected_proposal_store(path: Path) -> DetachedProposalStoreWitness:
    """Create an empty local-only schema; never overwrite an existing file."""
    _protocol()
    path = _path(path, create=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        os.close(fd)
        with closing(sqlite3.connect(path, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(_DDL)
                conn.execute("PRAGMA user_version=1")
                _scan(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        _path(path, create=False)
    except (OSError, sqlite3.Error) as exc:
        raise DisconnectedProposalStoreRejected("proposal store creation failed") from exc
    return genesis_disconnected_proposal_witness()


def inspect_disconnected_proposal_store(
    path: Path, *, proposal_id: str,
    retained: DetachedProposalStoreWitness | None = None,
) -> DetachedProposalStoreSnapshot:
    """Read a coherent SQLite snapshot without authorizing any effect."""
    # Reuse exact domain identity checks before opening SQLite.
    _protocol()
    lifecycle._id(proposal_id)
    anchored = None if retained is None else _witness(retained)
    path = _path(path, create=False)
    try:
        with closing(sqlite3.connect(
            path.as_uri() + "?mode=ro", uri=True, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN")
            try:
                witness, histories, prefixes = _scan(conn)
                if anchored is not None:
                    _assert_retained(anchored, prefixes, latest_required=False)
                history = histories.get(proposal_id)
                tip = (
                    lifecycle.replay_disconnected_proposal_lifecycle(proposal_id, history)
                    if history else None
                )
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        _path(path, create=False)
    except (OSError, sqlite3.Error) as exc:
        raise DisconnectedProposalStoreRejected("proposal store inspection failed") from exc
    return DetachedProposalStoreSnapshot(witness, tip)


def append_disconnected_proposal_transition(
    path: Path, *, proposal_id: str, new_state: str,
    expected_revision: int, expected_tip: lifecycle.DetachedProposalLifecycleTip | None,
    retained: DetachedProposalStoreWitness,
) -> DetachedProposalStoreSnapshot:
    """One local event CAS. Never retries an uncertain commit or dispatches tools."""
    _protocol()
    lifecycle._id(proposal_id)
    if type(expected_revision) is not int or not 0 <= expected_revision <= 256:
        raise DisconnectedProposalStoreRejected("invalid proposal expected revision")
    pinned_tip = _tip(expected_tip, proposal_id)
    pinned_witness = _witness(retained)
    if expected_revision == 0 and pinned_tip is not None:
        raise DisconnectedProposalStoreRejected("unexpected initial proposal tip")
    if expected_revision > 0 and (
        pinned_tip is None or pinned_tip[0] != expected_revision
    ):
        raise DisconnectedProposalStoreRejected("missing or stale proposal tip")
    path = _path(path, create=False)
    try:
        with closing(sqlite3.connect(
            path.as_uri() + "?mode=rw", uri=True, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                witness, histories, prefixes = _scan(conn)
                _assert_retained(pinned_witness, prefixes, latest_required=True)
                history = histories.get(proposal_id, ())
                current = (
                    lifecycle.replay_disconnected_proposal_lifecycle(proposal_id, history)
                    if history else None
                )
                actual_tip = _tip(current, proposal_id)
                if (
                    (0 if current is None else current.revision) != expected_revision
                    or actual_tip != pinned_tip
                ):
                    raise DisconnectedProposalStoreRejected("proposal CAS revision conflict")
                if witness.event_count >= _MAX_ROWS:
                    raise DisconnectedProposalStoreRejected("proposal event capacity exceeded")
                event = lifecycle.prepare_disconnected_proposal_transition(
                    proposal_id, current, new_state,
                )
                next_history = (*history, event)
                proposed_tip = lifecycle.replay_disconnected_proposal_lifecycle(
                    proposal_id, next_history,
                )
                seq = witness.event_count + 1
                values = (
                    seq, event.proposal_id, event.revision, event.prior_state,
                    event.new_state, event.previous_digest, event.event_digest,
                )
                new_digest = _hash(("event", witness.chain_digest, *values))
                conn.execute(
                    "INSERT INTO synthetic_proposal_events "
                    "(seq,proposal_id,revision,prior_state,new_state,"
                    "previous_digest,event_digest,global_digest) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (*values, new_digest),
                )
                reread, _, _ = _scan(conn)
                if (reread.event_count, reread.chain_digest) != (seq, new_digest):
                    raise DisconnectedProposalStoreRejected("proposal postappend readback mismatch")
                if (
                    _witness(retained) != pinned_witness
                    or _tip(expected_tip, proposal_id) != pinned_tip
                ):
                    raise DisconnectedProposalStoreRejected("proposal caller evidence changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        _path(path, create=False)
    except (OSError, sqlite3.Error) as exc:
        raise DisconnectedProposalStoreRejected("proposal store append failed") from exc
    # A post-COMMIT exception must be treated as COMMIT-UNKNOWN by the caller.
    return DetachedProposalStoreSnapshot(reread, proposed_tip)
