"""Import-pinned preflight for inert atomic claim and witness carriers.

This isolated reviewer deliberately does not access SQLite, reserve an
occurrence, authenticate evidence, or grant any kind of tool permission.
The retained witness remains caller-controlled and cannot prove a real effect.
"""

from __future__ import annotations

import re

from .disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    AtomicPreactionWitness,
)

_CLAIM = AtomicIntentClaim
_WITNESS = AtomicPreactionWitness
_FIELDS = {
    _CLAIM: ("occurrence_id", "bound_action_id", "request_sha256"),
    _WITNESS: ("count", "tip_sha256"),
}
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINALS = {
    kind: tuple(vars(kind).get(name) for name in (*fields, *_HOOKS))
    for kind, fields in _FIELDS.items()
}
_OCCURRENCE = re.compile(r"occ_[0-9a-f]{64}\Z")
_BOUND = re.compile(r"bound_[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX = 128

# Pin the control-plane shape separately from the mutable module dictionaries.
# These checks are local tamper alarms, not authentication or a sandbox.
_ORIGINAL_FIELD_MAP = _FIELDS
_ORIGINAL_FIELD_ITEMS = tuple(_FIELDS.items())
_ORIGINAL_CAPTURE_MAP = _ORIGINALS
_ORIGINAL_CAPTURE_ITEMS = tuple(_ORIGINALS.items())
_ORIGINAL_HOOKS = _HOOKS
_ORIGINAL_PATTERNS = (_OCCURRENCE, _BOUND, _SHA)
_ORIGINAL_BUDGET = _MAX


def _original_carriers() -> None:
    if (
        AtomicIntentClaim is not _CLAIM
        or AtomicPreactionWitness is not _WITNESS
        or any(
            vars(kind).get(name) is not original
            for kind, fields in _FIELDS.items()
            for name, original in zip(
                (*fields, *_HOOKS), _ORIGINALS[kind], strict=True,
            )
        )
    ):
        raise AtomicPreactionRejected("atomic input carrier definition changed")


def _matches(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


_ORIGINAL_CARRIER_GATE = _original_carriers
_ORIGINAL_MATCHER = _matches


def _assert_input_protocol() -> None:
    """Reject changed parsers, admission limits and recorded class shapes."""
    if (
        _FIELDS is not _ORIGINAL_FIELD_MAP
        or tuple(_FIELDS) != tuple(kind for kind, _ in _ORIGINAL_FIELD_ITEMS)
        or any(
            _FIELDS.get(kind) is not fields
            for kind, fields in _ORIGINAL_FIELD_ITEMS
        )
        or _ORIGINALS is not _ORIGINAL_CAPTURE_MAP
        or tuple(_ORIGINALS) != tuple(kind for kind, _ in _ORIGINAL_CAPTURE_ITEMS)
        or any(
            _ORIGINALS.get(kind) is not originals
            for kind, originals in _ORIGINAL_CAPTURE_ITEMS
        )
        or _HOOKS is not _ORIGINAL_HOOKS
        or _OCCURRENCE is not _ORIGINAL_PATTERNS[0]
        or _BOUND is not _ORIGINAL_PATTERNS[1]
        or _SHA is not _ORIGINAL_PATTERNS[2]
        or type(_MAX) is not int
        or _MAX != _ORIGINAL_BUDGET
        or _original_carriers is not _ORIGINAL_CARRIER_GATE
        or _matches is not _ORIGINAL_MATCHER
    ):
        raise AtomicPreactionRejected("atomic input protocol changed")


def review_atomic_input_carriers(
    claim: AtomicIntentClaim,
    retained: AtomicPreactionWitness,
) -> tuple[str, str, str, int, str]:
    """Return exact immutable values, never a permission or retained proof.

    Intended as an opt-in preflight ahead of a future reviewed storage path.
    This function is not wired into the existing ledger's ingress.
    """
    _assert_input_protocol()
    _original_carriers()
    if type(claim) is not _CLAIM or type(retained) is not _WITNESS:
        raise AtomicPreactionRejected("exact atomic claim and witness required")
    initial = (
        claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        retained.count, retained.tip_sha256,
    )
    _assert_input_protocol()
    _original_carriers()
    occurrence, bound, request, count, tip = initial
    if (
        not _matches(occurrence, _OCCURRENCE)
        or not _matches(bound, _BOUND)
        or not _matches(request, _SHA)
        or type(count) is not int
        or not 0 <= count <= _MAX
        or not _matches(tip, _SHA)
    ):
        raise AtomicPreactionRejected("invalid bounded atomic input carriers")
    final = (
        claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        retained.count, retained.tip_sha256,
    )
    _assert_input_protocol()
    _original_carriers()
    if any(after is not before for after, before in zip(final, initial, strict=True)):
        raise AtomicPreactionRejected("atomic input carrier changed during review")
    return initial
