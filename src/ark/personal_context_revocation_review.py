"""Durable synthetic revocation fence for ephemeral Personal Context reviews.

This is a local, append-only veto fixture, NOT authenticated consent or an
entitlement to disclose personal data. Memory and revocation live in separate
SQLite files, so two checks do not establish an atomic cross-store snapshot.
No raw owner/namespace, Memory content, credentials or notifications are stored.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

from .memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from .memory.contracts import MemoryScope
from .memory.sqlite_store import SQLiteMemoryStore
from .personal_context_review import (
    ContextSelectionPolicy,
    SyntheticContextBundle,
    review_personal_context,
)

_MAX = 2**63 - 1
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_TABLE = """CREATE TABLE synthetic_context_revocations(
    scope_digest TEXT PRIMARY KEY NOT NULL,
    revoked_at_ms INTEGER NOT NULL
)"""


class SyntheticContextRevocationRejected(RuntimeError):
    """A local revocation fence cannot safely provide a context projection."""


def _scope_digest(scope: MemoryScope) -> str:
    if type(scope) is not MemoryScope:
        raise SyntheticContextRevocationRejected("exact MemoryScope required")
    scope.__post_init__()
    payload = json.dumps(
        (scope.owner_id, scope.namespace), ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(b"ARK-context-revocation-scope-v1\0" + payload).hexdigest()


def _validate(conn: sqlite3.Connection) -> None:
    if conn.execute("PRAGMA user_version").fetchone()[0] != 1:
        raise SyntheticContextRevocationRejected("revocation schema version changed")
    expected = sqlite3.connect(":memory:")
    try:
        expected.execute(_TABLE)
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        if tuple(conn.execute(query)) != tuple(expected.execute(query)):
            raise SyntheticContextRevocationRejected("revocation schema changed")
    finally:
        expected.close()
    if conn.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
        raise SyntheticContextRevocationRejected("revocation SQLite quick_check failed")
    rows = conn.execute(
        "SELECT scope_digest,revoked_at_ms FROM synthetic_context_revocations"
    )
    for index, (digest, when) in enumerate(rows):
        if index >= 10_000:
            raise SyntheticContextRevocationRejected("revocation review budget exceeded")
        if (
            type(digest) is not str or not _SHA.fullmatch(digest)
            or type(when) is not int or not 0 <= when <= _MAX
        ):
            raise SyntheticContextRevocationRejected("revocation row integrity failed")


class SyntheticContextRevocationLedger:
    """Irreversible-within-fixture scope veto; no grant/reenrollment API."""

    def __init__(self, path: Path) -> None:
        if not isinstance(path, Path):
            raise TypeError("revocation path must be a pathlib.Path")
        self.path = path
        with closing(sqlite3.connect(path, timeout=10, isolation_level=None)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                version = conn.execute("PRAGMA user_version").fetchone()[0]
                if version == 0:
                    if tuple(conn.execute("SELECT name FROM sqlite_master")):
                        raise SyntheticContextRevocationRejected(
                            "unversioned revocation database is not empty"
                        )
                    conn.execute(_TABLE)
                    conn.execute("PRAGMA user_version=1")
                _validate(conn)
                conn.commit()
            except BaseException:
                conn.rollback()
                raise

    def _connect(self, *, readonly: bool) -> sqlite3.Connection:
        mode = "ro" if readonly else "rw"
        return sqlite3.connect(
            self.path.resolve().as_uri() + "?mode=" + mode,
            uri=True, timeout=10, isolation_level=None,
        )

    def revoke(self, scope: MemoryScope, *, at_ms: int) -> str:
        """Persist a veto marker; no implicit regrant or personal data deletion."""
        digest = _scope_digest(scope)
        if type(at_ms) is not int or not 0 <= at_ms <= _MAX:
            raise SyntheticContextRevocationRejected("invalid revocation timestamp")
        with closing(self._connect(readonly=False)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                _validate(conn)
                if conn.execute(
                    "SELECT 1 FROM synthetic_context_revocations WHERE scope_digest=?",
                    (digest,),
                ).fetchone() is not None:
                    raise SyntheticContextRevocationRejected("scope already revoked")
                latest = conn.execute(
                    "SELECT MAX(revoked_at_ms) FROM synthetic_context_revocations"
                ).fetchone()[0]
                if latest is not None and at_ms < latest:
                    raise SyntheticContextRevocationRejected("revocation clock regressed")
                if _scope_digest(scope) != digest:
                    raise SyntheticContextRevocationRejected("scope changed during revocation")
                conn.execute(
                    "INSERT INTO synthetic_context_revocations VALUES(?,?)",
                    (digest, at_ms),
                )
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        return digest

    def assert_not_revoked(self, scopes: tuple[MemoryScope, ...]) -> None:
        """Inspect one read-only snapshot; absence is not proof of consent."""
        if type(scopes) is not tuple or not 1 <= len(scopes) <= 16:
            raise SyntheticContextRevocationRejected("exact bounded scopes required")
        digests = tuple(_scope_digest(scope) for scope in scopes)
        if len(set(digests)) != len(digests):
            raise SyntheticContextRevocationRejected("duplicate context scopes")
        with closing(self._connect(readonly=True)) as conn:
            conn.execute("BEGIN")
            try:
                _validate(conn)
                for digest in digests:
                    if conn.execute(
                        "SELECT 1 FROM synthetic_context_revocations WHERE scope_digest=?",
                        (digest,),
                    ).fetchone() is not None:
                        raise SyntheticContextRevocationRejected("context scope revoked")
                if tuple(_scope_digest(scope) for scope in scopes) != digests:
                    raise SyntheticContextRevocationRejected("context scope changed")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise


def review_fresh_nonrevoked_context(
    store: SQLiteMemoryStore,
    request: CoherentSnapshotRequest,
    policy: ContextSelectionPolicy,
    ledger: SyntheticContextRevocationLedger,
    *, retained_revocations: object | None = None,
) -> SyntheticContextBundle:
    """Always reacquire Memory, bracket with veto checks, never grant usage.

    Revocation after the second check can still race with consumption, and
    absence of a marker cannot authenticate permission. Higher layers must
    forbid model/tool/export/notification use until consent gates are real.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(request) is not CoherentSnapshotRequest
        or type(policy) is not ContextSelectionPolicy
        or type(ledger) is not SyntheticContextRevocationLedger
    ):
        raise SyntheticContextRevocationRejected("exact context fixture inputs required")
    original = (
        request.owner_id, request.namespaces, request.text,
        request.per_namespace_limit, request.include_expired,
    )
    CoherentSnapshotRequest(*original)
    if request.include_expired:
        raise SyntheticContextRevocationRejected("expired records may not enter context")
    # Local import keeps the optional independent history reviewer separate
    # from this fixture's core SQLite schema and avoids an import cycle.
    from .personal_context_revocation_continuity_review import (
        review_revocation_continuity,
    )

    scopes = tuple(MemoryScope(request.owner_id, name) for name in request.namespaces)
    before = review_revocation_continuity(ledger, retained=retained_revocations)
    ledger.assert_not_revoked(scopes)
    snapshot = review_coherent_snapshot(store, request)
    bundle = review_personal_context(snapshot, policy)
    ledger.assert_not_revoked(scopes)
    # Detect disappearance or alteration of any veto that was present before
    # this read, even when a different namespace's row was changed mid-read.
    # A genuinely earlier independent witness also fences pre-existing edits.
    review_revocation_continuity(ledger, retained=before)
    if (
        request.owner_id, request.namespaces, request.text,
        request.per_namespace_limit, request.include_expired,
    ) != original:
        raise SyntheticContextRevocationRejected("context request changed during review")
    return bundle
