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
    SyntheticContextItem,
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
        self._source_path = path
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

    def _assert_source_path(self, expected: Path) -> None:
        # A local object-path fence; not protection against filesystem swaps.
        if (
            self.path is not expected
            or self._source_path is not expected
            or not isinstance(expected, Path)
        ):
            raise SyntheticContextRevocationRejected(
                "revocation source path changed"
            )

    def _connect(self, *, readonly: bool) -> sqlite3.Connection:
        self._assert_source_path(self._source_path)
        mode = "ro" if readonly else "rw"
        # Even a Path.resolve()/as_uri() implementation substituted by a
        # synthetic callback must not change the original source before
        # the SQLite handle is opened. The connection may also be a
        # reentrant boundary; close a handle returned under source drift.
        original_path = self._source_path
        resolved = self.path.resolve()
        self._assert_source_path(original_path)
        uri = resolved.as_uri() + "?mode=" + mode
        self._assert_source_path(original_path)
        connection = sqlite3.connect(
            uri, uri=True, timeout=10, isolation_level=None,
        )
        try:
            self._assert_source_path(original_path)
        except BaseException:
            connection.close()
            raise
        return connection

    def revoke(self, scope: MemoryScope, *, at_ms: int) -> str:
        """Persist a veto marker; no implicit regrant or personal data deletion."""
        source_path = self.path
        self._assert_source_path(source_path)
        # The initial digest computation is an overridable Python boundary.
        # Capture original scope BEFORE hashing, not the possibly retargeted
        # scope left by the first callback. This remains a local veto only.
        if type(scope) is not MemoryScope:
            raise SyntheticContextRevocationRejected("exact MemoryScope required")
        scope_epoch = (scope.owner_id, scope.namespace)

        def assert_scope_epoch() -> None:
            if (
                type(scope) is not MemoryScope
                or scope.owner_id is not scope_epoch[0]
                or scope.namespace is not scope_epoch[1]
            ):
                raise SyntheticContextRevocationRejected(
                    "scope changed during revocation"
                )

        assert_scope_epoch()
        digest = _scope_digest(scope)
        assert_scope_epoch()
        if type(at_ms) is not int or not 0 <= at_ms <= _MAX:
            raise SyntheticContextRevocationRejected("invalid revocation timestamp")
        with closing(self._connect(readonly=False)) as conn:
            self._assert_source_path(source_path)
            assert_scope_epoch()
            conn.execute("BEGIN IMMEDIATE")
            try:
                self._assert_source_path(source_path)
                assert_scope_epoch()
                _validate(conn)
                self._assert_source_path(source_path)
                assert_scope_epoch()
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
                assert_scope_epoch()
                if _scope_digest(scope) != digest:
                    raise SyntheticContextRevocationRejected("scope changed during revocation")
                assert_scope_epoch()
                conn.execute(
                    "INSERT INTO synthetic_context_revocations VALUES(?,?)",
                    (digest, at_ms),
                )
                assert_scope_epoch()
                self._assert_source_path(source_path)
                conn.commit()
                # A committed veto is never rolled back or re-granted if a
                # callback retargets its local source after the durable write.
                self._assert_source_path(source_path)
                assert_scope_epoch()
            except BaseException:
                conn.rollback()
                raise
        self._assert_source_path(source_path)
        assert_scope_epoch()
        return digest

    def assert_not_revoked(self, scopes: tuple[MemoryScope, ...]) -> None:
        """Inspect one read-only snapshot; absence is not proof of consent."""
        if type(scopes) is not tuple or not 1 <= len(scopes) <= 16:
            raise SyntheticContextRevocationRejected("exact bounded scopes required")
        source_path = self.path
        self._assert_source_path(source_path)
        # Pin each exact scope before the first potentially reentrant digest
        # callback. End-only checks can miss drift restored by a later SELECT.
        scope_epoch = tuple(
            (scope, scope.owner_id, scope.namespace) for scope in scopes
        )

        def assert_epoch() -> None:
            self._assert_source_path(source_path)
            if any(
                type(scope) is not MemoryScope
                or scope.owner_id is not owner
                or scope.namespace is not namespace
                for scope, owner, namespace in scope_epoch
            ):
                raise SyntheticContextRevocationRejected(
                    "context scope changed during revocation check"
                )

        digests = []
        for scope in scopes:
            digests.append(_scope_digest(scope))
            assert_epoch()
        digests = tuple(digests)
        if len(set(digests)) != len(digests):
            raise SyntheticContextRevocationRejected("duplicate context scopes")
        with closing(self._connect(readonly=True)) as conn:
            assert_epoch()
            conn.execute("BEGIN")
            try:
                # BEGIN itself and schema validation are separate reentrant
                # boundaries: never let a later callback restore early drift.
                assert_epoch()
                _validate(conn)
                assert_epoch()
                for digest in digests:
                    assert_epoch()
                    revoked = conn.execute(
                        "SELECT 1 FROM synthetic_context_revocations WHERE scope_digest=?",
                        (digest,),
                    ).fetchone()
                    assert_epoch()
                    if revoked is not None:
                        raise SyntheticContextRevocationRejected("context scope revoked")
                if tuple(_scope_digest(scope) for scope in scopes) != digests:
                    raise SyntheticContextRevocationRejected("context scope changed")
                assert_epoch()
                conn.commit()
                assert_epoch()
            except BaseException:
                conn.rollback()
                raise
        assert_epoch()


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
    # The veto receives these exact reflected-mutable scope objects. A hook
    # must not redirect the veto to another owner/namespace while projection
    # still reads the original request's private Memory.
    scope_epoch = tuple(
        (scope, scope.owner_id, scope.namespace) for scope in scopes
    )
    memory_source = store.path
    veto_source = ledger.path
    if not isinstance(memory_source, Path) or not isinstance(veto_source, Path):
        raise SyntheticContextRevocationRejected("exact context sources required")
    policy_epoch = (
        policy.total_limit, policy.per_namespace_limit, policy.policy_revision,
    )

    def assert_epoch() -> None:
        # An equal-valued replacement is still a new input epoch: a later
        # privacy callback could restore the original and conceal a transient
        # retarget. Pin each immutable field carrier, not only its value.
        request_current = (
            request.owner_id, request.namespaces, request.text,
            request.per_namespace_limit, request.include_expired,
        )
        policy_current = (
            policy.total_limit, policy.per_namespace_limit,
            policy.policy_revision,
        )
        if (
            store.path is not memory_source
            or ledger.path is not veto_source
            or any(
                current is not pinned
                for current, pinned in zip(request_current, original, strict=True)
            )
            or any(
                type(scope) is not MemoryScope
                or scope.owner_id is not owner
                or scope.namespace is not namespace
                for scope, owner, namespace in scope_epoch
            )
            or any(
                current is not pinned
                for current, pinned in zip(policy_current, policy_epoch, strict=True)
            )
        ):
            raise SyntheticContextRevocationRejected(
                "context source, request or policy changed during review"
            )

    before = review_revocation_continuity(ledger, retained=retained_revocations)
    assert_epoch()
    ledger.assert_not_revoked(scopes)
    assert_epoch()
    snapshot = review_coherent_snapshot(store, request)
    assert_epoch()
    bundle = review_personal_context(snapshot, policy)
    assert_epoch()
    # The second veto read and retained-history replay are independently
    # reentrant. Hold the actual private projection across both operations:
    # otherwise a callback can rewrite the returned content or carrier after
    # the projection's own final integrity check.
    if type(bundle) is not SyntheticContextBundle or type(bundle.items) is not tuple:
        raise SyntheticContextRevocationRejected("context bundle shape changed")
    bundle_items = bundle.items
    bundle_id = bundle.bundle_id
    bundle_digest = bundle.snapshot_digest
    bundle_items_epoch = tuple((
        item, item.memory_id, item.namespace, item.content,
        item.revision, item.provenance_id,
    ) for item in bundle_items)

    def assert_bundle_epoch() -> None:
        if (
            bundle.items is not bundle_items
            or bundle.bundle_id is not bundle_id
            or bundle.snapshot_digest is not bundle_digest
            or bundle.snapshot_digest != snapshot.provenance_sha256
            or len(bundle.items) != len(bundle_items_epoch)
            or any(
                type(item) is not SyntheticContextItem
                or item is not original
                or item.memory_id is not memory_id
                or item.namespace is not namespace
                or item.content is not content
                or item.revision != revision
                or item.provenance_id is not provenance
                for item, (
                    original, memory_id, namespace, content, revision, provenance,
                ) in zip(bundle.items, bundle_items_epoch, strict=True)
            )
        ):
            raise SyntheticContextRevocationRejected(
                "context bundle changed during final privacy checks"
            )

    assert_bundle_epoch()
    ledger.assert_not_revoked(scopes)
    assert_epoch()
    assert_bundle_epoch()
    # Detect disappearance or alteration of any veto that was present before
    # this read, even when a different namespace's row was changed mid-read.
    # A genuinely earlier independent witness also fences pre-existing edits.
    review_revocation_continuity(ledger, retained=before)
    assert_epoch()
    assert_bundle_epoch()
    return bundle
