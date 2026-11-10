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


def review_atomic_input_carriers(
    claim: AtomicIntentClaim,
    retained: AtomicPreactionWitness,
) -> tuple[str, str, str, int, str]:
    """Return exact immutable values, never a permission or retained proof.

    Intended as an opt-in preflight ahead of a future reviewed storage path.
    This function is not wired into the existing ledger's ingress.
    """
    _original_carriers()
    if type(claim) is not _CLAIM or type(retained) is not _WITNESS:
        raise AtomicPreactionRejected("exact atomic claim and witness required")
    initial = (
        claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        retained.count, retained.tip_sha256,
    )
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
    _original_carriers()
    if any(after is not before for after, before in zip(final, initial, strict=True)):
        raise AtomicPreactionRejected("atomic input carrier changed during review")
    return initial
