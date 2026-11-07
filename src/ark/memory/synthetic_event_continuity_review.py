"""Read-only, per-scope synthetic Memory v1 event continuity witness.

An event hash is local, not authenticated. A retained historical prefix must
be independently preserved to detect a coherent suffix rollback. No frozen
Memory schema, content, consent, deletion or external backend is modified.
"""

from __future__ import annotations

import hashlib
import json
import re
from contextlib import closing
from dataclasses import dataclass

from .contracts import MemoryScope
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema

_MAX = 10_000
_INT_MAX = 2**63 - 1
_ID = re.compile(r"mem_[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"memevt_[0-9a-f]{64}\Z")


class SyntheticMemoryEventRejected(RuntimeError):
    """The local Memory event and live-row histories cannot be reconciled."""


def _hash(label: str, values: object) -> str:
    encoded = json.dumps(
        values, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return "memevt_" + hashlib.sha256(
        label.encode("utf-8") + b"\0" + encoded
    ).hexdigest()


def _scope_digest(scope: MemoryScope) -> str:
    return _hash(
        "ARK-synthetic-memory-event-scope-v1",
        (scope.owner_id, scope.namespace),
    )


def _genesis(scope_digest: str) -> str:
    return _hash("ARK-synthetic-memory-event-genesis-v1", scope_digest)


@dataclass(frozen=True, slots=True)
class SyntheticMemoryEventWitness:
    scope_digest: str
    event_count: int
    last_event_id: int
    tail_hash: str

    def assert_shape(self, scope_digest: str) -> None:
        if (
            type(self.scope_digest) is not str
            or self.scope_digest != scope_digest
            or type(self.event_count) is not int
            or not 0 <= self.event_count <= _MAX
            or type(self.last_event_id) is not int
            or not 0 <= self.last_event_id <= _INT_MAX
            or type(self.tail_hash) is not str
            or not _DIGEST.fullmatch(self.tail_hash)
            or (self.event_count == 0) != (self.last_event_id == 0)
            or self.event_count == 0
            and self.tail_hash != _genesis(scope_digest)
        ):
            raise SyntheticMemoryEventRejected("invalid retained Memory witness")

    @property
    def deletion_authorized(self) -> bool:
        return False

    @property
    def context_use_authorized(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False


# Freeze the inert receipt contract across synthetic constructor substitution.
_WITNESS_TYPE = SyntheticMemoryEventWitness


def _new_witness(
    scope_digest: str, event_count: int, last_event_id: int, tail_hash: str,
) -> SyntheticMemoryEventWitness:
    witness = SyntheticMemoryEventWitness(
        scope_digest, event_count, last_event_id, tail_hash,
    )
    if (
        type(witness) is not _WITNESS_TYPE
        or witness.scope_digest is not scope_digest
        or witness.event_count is not event_count
        or witness.last_event_id is not last_event_id
        or witness.tail_hash is not tail_hash
        or witness.deletion_authorized is not False
        or witness.context_use_authorized is not False
        or witness.external_disclosure_authorized is not False
    ):
        raise SyntheticMemoryEventRejected("constructed Memory event witness changed")
    return witness


def review_synthetic_memory_event_continuity(
    memory: SQLiteMemoryStore,
    scope: MemoryScope,
    *,
    retained: SyntheticMemoryEventWitness | None = None,
) -> SyntheticMemoryEventWitness:
    """Replay bounded local events and match live rows in one read snapshot.

    Per-scope event IDs may contain gaps because SQLite IDs are global.
    Timestamps are NOT required to increase: Memory v1 permits caller-clock
    regression. Closed IDs may be explicitly re-created at revision 1.
    """
    if type(memory) is not SQLiteMemoryStore or type(scope) is not MemoryScope:
        raise SyntheticMemoryEventRejected("exact Memory store and scope required")
    # Capture the original caller-owned scope/source before the first hash,
    # including the immutable string carriers that can be swapped reflectively.
    original = (scope.owner_id, scope.namespace)
    path_epoch = memory.path
    pinned = MemoryScope(*original)
    if retained is not None and type(retained) is not _WITNESS_TYPE:
        raise SyntheticMemoryEventRejected("exact retained Memory witness required")
    retained_epoch = None if retained is None else (
        retained.scope_digest, retained.event_count,
        retained.last_event_id, retained.tail_hash,
    )

    def assert_epoch() -> None:
        if (
            memory.path is not path_epoch
            or scope.owner_id is not original[0]
            or scope.namespace is not original[1]
        ):
            raise SyntheticMemoryEventRejected(
                "Memory source or scope changed during review"
            )
        if retained is not None:
            try:
                stable_retained = (
                    type(retained) is _WITNESS_TYPE
                    and not any(
                        current is not before for current, before in zip(
                            (
                                retained.scope_digest, retained.event_count,
                                retained.last_event_id, retained.tail_hash,
                            ),
                            retained_epoch, strict=True,
                        )
                    )
                    and retained.deletion_authorized is False
                    and retained.context_use_authorized is False
                    and retained.external_disclosure_authorized is False
                )
            except (AttributeError, TypeError, ValueError) as exc:
                raise SyntheticMemoryEventRejected(
                    "retained Memory witness authority or epoch invalid"
                ) from exc
            if not stable_retained:
                raise SyntheticMemoryEventRejected(
                    "independently retained Memory witness changed during review"
                )

    assert_epoch()
    scope_hash = _scope_digest(pinned)
    assert_epoch()
    if retained is not None:
        retained.assert_shape(scope_hash)
        assert_epoch()
    genesis = _new_witness(scope_hash, 0, 0, _genesis(scope_hash))
    assert_epoch()
    prefixes = [genesis]
    # Retain exact original witness carriers. Reentrant hashing or decoding
    # may rewrite an earlier prefix after it is no longer the latest link.
    prefix_epochs = [(
        genesis, (
            genesis.scope_digest, genesis.event_count,
            genesis.last_event_id, genesis.tail_hash,
        ),
    )]

    def assert_prefixes_stable() -> None:
        if len(prefixes) != len(prefix_epochs):
            raise SyntheticMemoryEventRejected("Memory event prefix set changed")
        try:
            for current, (original_witness, original_fields) in zip(
                prefixes, prefix_epochs, strict=True,
            ):
                if (
                    current is not original_witness
                    or type(current) is not _WITNESS_TYPE
                    or any(now is not original for now, original in zip(
                        (
                            current.scope_digest, current.event_count,
                            current.last_event_id, current.tail_hash,
                        ), original_fields, strict=True,
                    ))
                    or current.deletion_authorized is not False
                    or current.context_use_authorized is not False
                    or current.external_disclosure_authorized is not False
                ):
                    raise SyntheticMemoryEventRejected(
                        "earlier Memory event witness changed during review"
                    )
        except (AttributeError, TypeError, ValueError) as exc:
            raise SyntheticMemoryEventRejected(
                "earlier Memory event witness is invalid"
            ) from exc

    with closing(memory._connect_readonly()) as conn:
        assert_epoch()
        conn.execute("BEGIN")
        try:
            assert_epoch()
            _validate_v1_schema(conn)
            assert_epoch()
            events = conn.execute(
                """SELECT event_id,memory_id,owner_id,namespace,operation,
                          revision,occurred_at_ms FROM memory_events
                   WHERE owner_id=? AND namespace=?
                   ORDER BY event_id LIMIT ?""",
                (*original, _MAX + 1),
            ).fetchall()
            assert_epoch()
            if len(events) > _MAX:
                raise SyntheticMemoryEventRejected("Memory event review budget exceeded")
            states: dict[str, tuple[bool, int]] = {}
            last_id = 0
            for raw in events:
                assert_epoch()
                event_id, memory_id, owner, namespace, op, revision, at_ms = raw
                if (
                    type(event_id) is not int
                    or not last_id < event_id <= _INT_MAX
                    or type(memory_id) is not str or not _ID.fullmatch(memory_id)
                    or (owner, namespace) != original
                    or type(owner) is not str or type(namespace) is not str
                    or type(op) is not str
                    or op not in ("create", "update", "delete", "expire")
                    or type(revision) is not int or not 1 <= revision <= _INT_MAX
                    or type(at_ms) is not int or not 0 <= at_ms <= _INT_MAX
                ):
                    raise SyntheticMemoryEventRejected("malformed stored Memory event")
                alive, old_rev = states.get(memory_id, (False, 0))
                if op == "create":
                    if alive or revision != 1:
                        raise SyntheticMemoryEventRejected("invalid Memory create history")
                    states[memory_id] = (True, revision)
                elif op == "update":
                    if not alive or revision != old_rev + 1:
                        raise SyntheticMemoryEventRejected("invalid Memory update history")
                    states[memory_id] = (True, revision)
                else:
                    if not alive or revision != old_rev:
                        raise SyntheticMemoryEventRejected("invalid Memory terminal history")
                    states[memory_id] = (False, revision)
                prior = prefixes[-1]
                prior_epoch = (
                    prior.scope_digest, prior.event_count,
                    prior.last_event_id, prior.tail_hash,
                )
                prior_hash = prior.tail_hash
                digest = _hash(
                    "ARK-synthetic-memory-event-v1",
                    (prior_hash, tuple(raw)),
                )
                assert_epoch()
                if (
                    (
                        prior.scope_digest, prior.event_count,
                        prior.last_event_id, prior.tail_hash,
                    ) != prior_epoch
                    or prior.tail_hash is not prior_hash
                ):
                    raise SyntheticMemoryEventRejected(
                        "prior Memory event chain link changed"
                    )
                next_count = prior.event_count + 1
                witness = _new_witness(scope_hash, next_count, event_id, digest)
                prefixes.append(witness)
                prefix_epochs.append((
                    witness, (
                        scope_hash, next_count, event_id, digest,
                    ),
                ))
                assert_epoch()
                last_id = event_id
            stored = conn.execute(
                """SELECT * FROM memories WHERE owner_id=? AND namespace=?
                   ORDER BY memory_id LIMIT ?""",
                (*original, _MAX + 1),
            ).fetchall()
            assert_epoch()
            if len(stored) > _MAX:
                raise SyntheticMemoryEventRejected("Memory row review budget exceeded")
            live: dict[str, int] = {}
            for row in stored:
                assert_epoch()
                record = _record(row)
                assert_epoch()
                if record.scope != pinned or record.memory_id in live:
                    raise SyntheticMemoryEventRejected("Memory live row scope changed")
                live[record.memory_id] = record.revision
            expected = {
                memory_id: rev for memory_id, (alive, rev) in states.items()
                if alive
            }
            if live != expected:
                raise SyntheticMemoryEventRejected(
                    "Memory event lifecycle differs from live rows"
                )
            assert_epoch()
            assert_prefixes_stable()
            if retained is not None and (
                retained.event_count >= len(prefixes)
                or prefixes[retained.event_count] != retained
            ):
                raise SyntheticMemoryEventRejected(
                    "independently retained Memory history changed"
                )
            assert_epoch()
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    assert_epoch()
    assert_prefixes_stable()
    return prefixes[-1]
