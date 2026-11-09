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


# A result property is executable code, not a harmless stored Boolean.
# Pin deny-only definitions before callers can install False-looking substitutes.
_VECTOR_TYPE = DisconnectedEpochVector
_DENIAL_NAMES = (
    "coherent_snapshot_proven", "trusted_time_proven",
    "independent_custody_proven", "memory_disclosure_authorized",
    "dispatch_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_VECTOR_TYPE)[name] for name in _DENIAL_NAMES)


# These bindings are locally retained dependencies, not a tamper-proof
# sandbox, trusted source identity or independent store provenance. Reject
# in-process substitutions before reading caller-supplied store metadata.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_STORE_PATTERN = _STORE
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_MAX_STORES = _MAX_STORES
_ORIGINAL_MAX_INTEGER = _MAX_INTEGER


def _assert_epoch_helpers() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _STORE is not _ORIGINAL_STORE_PATTERN
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _MAX_STORES is not _ORIGINAL_MAX_STORES
        or _MAX_INTEGER is not _ORIGINAL_MAX_INTEGER
    ):
        raise EpochVectorRejected("epoch validation or digest dependencies changed")


def _assert_non_authorizing(vector: object) -> None:
    """Reject substituted authority getters and reflective result mutation."""
    if (
        DisconnectedEpochVector is not _VECTOR_TYPE
        or type(vector) is not _VECTOR_TYPE
        or any(
            vars(_VECTOR_TYPE).get(name) is not original
            for name, original in zip(_DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise EpochVectorRejected("store vector acquired authority")
    retained_stores = vector.stores
    retained_digest = vector.digest
    for name in _DENIAL_NAMES:
        if getattr(vector, name) is not False:
            raise EpochVectorRejected("store vector acquired authority")
        # A getter can mutate frozen dataclass fields or change a later getter.
        # Equal-value replacement is also a new, unreviewed carrier epoch.
        if (
            vector.stores is not retained_stores
            or vector.digest is not retained_digest
            or any(
                vars(_VECTOR_TYPE).get(key) is not original
                for key, original in zip(
                    _DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True,
                )
            )
        ):
            raise EpochVectorRejected("store vector changed during denial check")


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
    _assert_epoch_helpers()
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
    _assert_epoch_helpers()
    data = json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    _assert_epoch_helpers()
    result = hashlib.sha256(_DOMAIN + data).hexdigest()
    _assert_epoch_helpers()
    return result


def capture_disconnected_epoch_vector(
    stores: tuple[DisconnectedStoreEpoch, ...],
) -> DisconnectedEpochVector:
    """Canonicalize synthetic store claims without vouching for their origins."""
    _assert_epoch_helpers()
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
    _assert_non_authorizing(result)
    return result


def _validated_vector(vector: object) -> tuple[tuple[object, ...], ...]:
    _assert_epoch_helpers()
    if type(vector) is not DisconnectedEpochVector:
        raise EpochVectorRejected("exact vector required")
    _assert_non_authorizing(vector)
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
    _assert_non_authorizing(vector)
    return rows


def review_disconnected_epoch_progress(
    retained: DisconnectedEpochVector, observed: DisconnectedEpochVector,
) -> DisconnectedEpochVector:
    """Reject schema swaps, counter rollbacks, and silent same-generation changes.

    Both vectors must be supplied by callers. An internal hash cannot prove
    independent retention or a coherent transaction spanning multiple stores.
    """
    _assert_epoch_helpers()
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
    _assert_non_authorizing(retained)
    _assert_non_authorizing(observed)
    return observed
