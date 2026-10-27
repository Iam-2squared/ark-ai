"""Pure, bounded, synthetic comparison of externally retained store epochs.

This is NOT a coherent cross-SQLite snapshot: claims are caller-supplied and
no read transaction, trusted witness, authentication or write is performed.
A changed epoch is only a *consistency hint* after independent custody.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, fields

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_STORE = re.compile(r"[a-z][a-z0-9_]{0,31}\Z")
_DOMAIN = b"ARK-disconnected-epoch-vector-v1\0"
_MAX_STORES = 16
_MAX_INTEGER = 2**63 - 1


class EpochVectorRejected(ValueError):
    """Untrusted store epochs are malformed, inconsistent or regressive."""


@dataclass(frozen=True, slots=True)
class DisconnectedStoreEpoch:
    store_id: str
    incarnation_sha256: str
    schema_sha256: str
    generation: int
    event_count: int
    event_tail_sha256: str
    state_sha256: str
    logical_time_ns: int


@dataclass(frozen=True, slots=True)
class DisconnectedEpochVector:
    stores: tuple[DisconnectedStoreEpoch, ...]
    digest: str

    @property
    def coherent_snapshot_proven(self) -> bool:
        return False

    @property
    def trusted_time_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


def _carrier_values(stores: tuple[DisconnectedStoreEpoch, ...]) -> tuple[tuple[object, ...], ...]:
    return tuple(tuple(getattr(store, item.name) for item in fields(store)) for store in stores)


def _assert_carriers(
    stores: tuple[DisconnectedStoreEpoch, ...],
    original_stores: tuple[DisconnectedStoreEpoch, ...],
    originals: tuple[DisconnectedStoreEpoch, ...],
    values: tuple[tuple[object, ...], ...],
) -> None:
    if stores is not original_stores or len(stores) != len(originals):
        raise EpochVectorRejected("store tuple changed during review")
    for current, original, previous in zip(stores, originals, values, strict=True):
        if current is not original:
            raise EpochVectorRejected("store epoch carrier changed during review")
        now = tuple(getattr(current, item.name) for item in fields(current))
        if any(left is not right for left, right in zip(now, previous, strict=True)):
            raise EpochVectorRejected("store field carrier changed during review")


def _rows(stores: object) -> tuple[tuple[object, ...], ...]:
    if (
        type(stores) is not tuple
        or not 1 <= len(stores) <= _MAX_STORES
        or any(type(s) is not DisconnectedStoreEpoch for s in stores)
    ):
        raise EpochVectorRejected("exact bounded store tuple required")
    rows = _carrier_values(stores)
    previous = ""
    for row in rows:
        sid, incarnation, schema, generation, events, tail, state, time_ns = row
        if (
            type(sid) is not str or _STORE.fullmatch(sid) is None or sid <= previous
            or any(type(s) is not str or _SHA.fullmatch(s) is None
                   for s in (incarnation, schema, tail, state))
            or any(type(n) is not int or not 0 <= n <= _MAX_INTEGER
                   for n in (generation, events, time_ns))
            or events < generation
        ):
            raise EpochVectorRejected("malformed, unordered or contradictory store epoch")
        previous = sid
    return rows


def _canonical_digest(rows: tuple[tuple[object, ...], ...]) -> str:
    data = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(_DOMAIN + data).hexdigest()


def capture_disconnected_epoch_vector(
    stores: tuple[DisconnectedStoreEpoch, ...],
) -> DisconnectedEpochVector:
    """Canonicalize synthetic store claims without vouching for their origins."""
    original = stores
    rows = _rows(stores)
    carriers = tuple(stores)
    values = rows
    _assert_carriers(stores, original, carriers, values)
    digest = _canonical_digest(rows)
    _assert_carriers(stores, original, carriers, values)
    if _rows(stores) != rows:
        raise EpochVectorRejected("store epoch changed while capturing")
    _assert_carriers(stores, original, carriers, values)
    result = DisconnectedEpochVector(stores=stores, digest=digest)
    _assert_carriers(stores, original, carriers, values)
    if (type(result) is not DisconnectedEpochVector or result.stores is not stores
            or result.digest is not digest):
        raise EpochVectorRejected("constructed store vector changed")
    return result


def _validated_vector(vector: object) -> tuple[tuple[object, ...], ...]:
    if type(vector) is not DisconnectedEpochVector:
        raise EpochVectorRejected("exact vector required")
    original_stores = vector.stores
    original_digest = vector.digest
    rows = _rows(original_stores)
    carriers = tuple(original_stores)
    values = rows
    _assert_carriers(vector.stores, original_stores, carriers, values)
    if type(original_digest) is not str or _SHA.fullmatch(original_digest) is None:
        raise EpochVectorRejected("malformed vector digest")
    if _canonical_digest(rows) != original_digest:
        raise EpochVectorRejected("store vector digest mismatch")
    if vector.stores is not original_stores or vector.digest is not original_digest:
        raise EpochVectorRejected("vector carrier changed during review")
    _assert_carriers(vector.stores, original_stores, carriers, values)
    if _rows(original_stores) != rows:
        raise EpochVectorRejected("store epoch changed during review")
    _assert_carriers(vector.stores, original_stores, carriers, values)
    return rows


def review_disconnected_epoch_progress(
    retained: DisconnectedEpochVector, observed: DisconnectedEpochVector,
) -> DisconnectedEpochVector:
    """Reject schema swaps, counter rollbacks, and silent same-generation changes.

    Both vectors must be supplied by callers. An internal hash cannot prove
    independent retention or a coherent transaction spanning multiple stores.
    """
    earlier = _validated_vector(retained)
    later = _validated_vector(observed)
    if len(earlier) != len(later):
        raise EpochVectorRejected("store membership changed across epochs")
    for prev, now in zip(earlier, later, strict=True):
        p_id, p_inc, p_schema, p_gen, p_events, p_tail, p_state, p_clock = prev
        n_id, n_inc, n_schema, n_gen, n_events, n_tail, n_state, n_clock = now
        if (p_id, p_inc, p_schema) != (n_id, n_inc, n_schema):
            raise EpochVectorRejected("store identity or schema changed")
        if n_gen < p_gen or n_events < p_events or n_clock < p_clock:
            raise EpochVectorRejected("observed store epoch regressed")
        if n_gen == p_gen:
            if now != prev:
                raise EpochVectorRejected("unchanged revision has changed retained state")
        elif n_events == p_events or n_tail == p_tail or n_state == p_state:
            raise EpochVectorRejected("new generation lacks advancing event/state witness")
    if _validated_vector(retained) != earlier or _validated_vector(observed) != later:
        raise EpochVectorRejected("review inputs changed during comparison")
    return observed
