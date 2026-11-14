"""Disconnected, proposal-only lifecycle replay with a retained continuity tip.

This is a synthetic local review, not a persisted proposal store, signature,
human decision, code change, execution permission or Candidate promotion.
A digest cannot establish who approved or authored an event.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType

_PROPOSAL_ID = re.compile(r"proposal_[0-9a-f]{64}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_GENESIS = "0" * 64
_DOMAIN = b"ARK-disconnected-proposal-lifecycle-v1\0"
_MAX_EVENTS = 256
_ALLOWED = MappingProxyType({
    "NONE": frozenset(("PROPOSED",)),
    "PROPOSED": frozenset(("REVIEW_REQUIRED", "REJECTED")),
    "REVIEW_REQUIRED": frozenset((
        "ACCEPTED_FOR_IMPLEMENTATION", "REJECTED", "SUPERSEDED",
    )),
    "ACCEPTED_FOR_IMPLEMENTATION": frozenset(("SUPERSEDED",)),
    "REJECTED": frozenset(),
    "SUPERSEDED": frozenset(),
})


class DisconnectedProposalLifecycleRejected(ValueError):
    """The proposed synthetic event sequence is not a coherent lifecycle."""


@dataclass(frozen=True, slots=True)
class DetachedProposalTransition:
    proposal_id: str
    revision: int
    prior_state: str
    new_state: str
    previous_digest: str
    event_digest: str


@dataclass(frozen=True, slots=True)
class DetachedProposalLifecycleTip:
    proposal_id: str
    revision: int
    state: str
    event_digest: str

    @property
    def human_review_authenticated(self) -> bool:
        return False

    @property
    def code_change_authorized(self) -> bool:
        return False

    @property
    def candidate_promotion_authorized(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def protected_evaluation_opened(self) -> bool:
        return False


_TRANSITION = DetachedProposalTransition
_TIP = DetachedProposalLifecycleTip
_TRANSITION_FIELDS = (
    "proposal_id", "revision", "prior_state", "new_state",
    "previous_digest", "event_digest",
)
_TIP_FIELDS = ("proposal_id", "revision", "state", "event_digest")
_DENIAL_FIELDS = (
    "human_review_authenticated", "code_change_authorized",
    "candidate_promotion_authorized", "training_authorized",
    "protected_evaluation_opened",
)
_TRANSITION_ORIGINAL = tuple(vars(_TRANSITION).get(n) for n in _TRANSITION_FIELDS)
_TIP_ORIGINAL = tuple(vars(_TIP).get(n) for n in _TIP_FIELDS + _DENIAL_FIELDS)
_ORIGINAL_TRANSITION_INIT = vars(_TRANSITION)["__init__"]
_ORIGINAL_TIP_INIT = vars(_TIP)["__init__"]
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_ALLOWED = _ALLOWED
_ORIGINAL_MAX_EVENTS = _MAX_EVENTS
_ORIGINAL_GENESIS = _GENESIS
_ORIGINAL_PROPOSAL_ID = _PROPOSAL_ID
_ORIGINAL_DIGEST_RE = _DIGEST


def _protocol() -> None:
    if (
        DetachedProposalTransition is not _TRANSITION
        or DetachedProposalLifecycleTip is not _TIP
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _ALLOWED is not _ORIGINAL_ALLOWED
        or type(_MAX_EVENTS) is not int
        or _MAX_EVENTS is not _ORIGINAL_MAX_EVENTS
        or _GENESIS is not _ORIGINAL_GENESIS
        or _PROPOSAL_ID is not _ORIGINAL_PROPOSAL_ID
        or _DIGEST is not _ORIGINAL_DIGEST_RE
        or vars(_TRANSITION).get("__init__") is not _ORIGINAL_TRANSITION_INIT
        or vars(_TIP).get("__init__") is not _ORIGINAL_TIP_INIT
        or any(
            vars(_TRANSITION).get(name) is not original
            for name, original in zip(
                _TRANSITION_FIELDS, _TRANSITION_ORIGINAL, strict=True,
            )
        )
        or any(
            vars(_TIP).get(name) is not original
            for name, original in zip(
                _TIP_FIELDS + _DENIAL_FIELDS, _TIP_ORIGINAL, strict=True,
            )
        )
    ):
        raise DisconnectedProposalLifecycleRejected(
            "detached proposal protocol changed"
        )


def _id(value: object) -> str:
    if type(value) is not str or _PROPOSAL_ID.fullmatch(value) is None:
        raise DisconnectedProposalLifecycleRejected("invalid proposal identity")
    return value


def _digest(value: object) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise DisconnectedProposalLifecycleRejected("invalid synthetic event digest")
    return value


def _event_hash(
    proposal_id: str, revision: int, old: str, new: str, previous: str,
) -> str:
    payload = (1, proposal_id, revision, old, new, previous)
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(_DOMAIN + encoded.encode("ascii")).hexdigest()


def replay_disconnected_proposal_lifecycle(
    proposal_id: str,
    events: tuple[DetachedProposalTransition, ...],
    *,
    retained: DetachedProposalLifecycleTip | None = None,
) -> DetachedProposalLifecycleTip:
    """Replay exact synthetic revisions; require an external tip if supplied.

    An independently retained tip can detect a divergent prefix at its own
    revision, but cannot prove authentic provenance or detect rollback alone.
    """
    _protocol()
    _id(proposal_id)
    if (
        type(events) is not tuple or not 1 <= len(events) <= _MAX_EVENTS
        or any(type(item) is not _TRANSITION for item in events)
    ):
        raise DisconnectedProposalLifecycleRejected("invalid event sequence")
    if retained is not None and (
        type(retained) is not _TIP
        or retained.proposal_id != proposal_id
        or type(retained.revision) is not int
        or not 1 <= retained.revision <= len(events)
        or retained.state not in _ALLOWED
        or _digest(retained.event_digest) is None
    ):
        raise DisconnectedProposalLifecycleRejected("invalid retained tip")
    pinned = tuple(
        (event, tuple(getattr(event, field) for field in _TRANSITION_FIELDS))
        for event in events
    )
    retained_epoch = (
        None if retained is None
        else tuple(getattr(retained, field) for field in _TIP_FIELDS)
    )

    def stable() -> None:
        _protocol()
        if any(
            item is not event
            or any(
                getattr(item, name) is not value
                for name, value in zip(
                    _TRANSITION_FIELDS, fields, strict=True,
                )
            )
            for item, (event, fields) in zip(events, pinned, strict=True)
        ):
            raise DisconnectedProposalLifecycleRejected("event epoch changed")
        if retained is not None and any(
            getattr(retained, name) is not value
            for name, value in zip(_TIP_FIELDS, retained_epoch, strict=True)
        ):
            raise DisconnectedProposalLifecycleRejected("retained tip changed")

    revision, state, previous = 0, "NONE", _GENESIS
    retained_matched = retained is None
    for _, fields in pinned:
        stable()
        event_id, seq, old, new, prev_hash, event_hash = fields
        if (
            _id(event_id) != proposal_id
            or type(seq) is not int or seq != revision + 1
            or type(old) is not str or old != state
            or type(new) is not str or new not in _ALLOWED[state]
            or _digest(prev_hash) != previous
        ):
            raise DisconnectedProposalLifecycleRejected(
                "synthetic revision, transition or prefix mismatch"
            )
        calculated = _event_hash(event_id, seq, old, new, previous)
        stable()
        if _digest(event_hash) != calculated:
            raise DisconnectedProposalLifecycleRejected("synthetic event hash mismatch")
        revision, state, previous = seq, new, calculated
        if retained is not None and revision == retained.revision:
            if state != retained.state or previous != retained.event_digest:
                raise DisconnectedProposalLifecycleRejected("retained prefix diverged")
            retained_matched = True
    stable()
    if not retained_matched:
        raise DisconnectedProposalLifecycleRejected("retained tip not present")
    result = _TIP(proposal_id, revision, state, previous)
    stable()
    if (
        type(result) is not _TIP
        or result.proposal_id != proposal_id
        or result.revision != revision
        or result.state != state
        or result.event_digest != previous
    ):
        raise DisconnectedProposalLifecycleRejected("synthetic result mutated")
    for name in _DENIAL_FIELDS:
        stable()
        if getattr(result, name) is not False:
            raise DisconnectedProposalLifecycleRejected("synthetic tip gained authority")
    stable()
    return result


def prepare_disconnected_proposal_transition(
    proposal_id: str, prior: DetachedProposalLifecycleTip | None, new_state: str,
) -> DetachedProposalTransition:
    """Create one synthetic transition. Never records a human decision."""
    _protocol()
    _id(proposal_id)
    if prior is not None and (
        type(prior) is not _TIP
        or prior.proposal_id != proposal_id
        or type(prior.revision) is not int
        or not 1 <= prior.revision < _MAX_EVENTS
        or type(prior.state) is not str
        or prior.state not in _ALLOWED
    ):
        raise DisconnectedProposalLifecycleRejected("invalid prior tip")
    old = "NONE" if prior is None else prior.state
    previous = _GENESIS if prior is None else _digest(prior.event_digest)
    if type(new_state) is not str or new_state not in _ALLOWED[old]:
        raise DisconnectedProposalLifecycleRejected("synthetic transition denied")
    revision = 1 if prior is None else prior.revision + 1
    digest = _event_hash(proposal_id, revision, old, new_state, previous)
    _protocol()
    event = _TRANSITION(proposal_id, revision, old, new_state, previous, digest)
    _protocol()
    if type(event) is not _TRANSITION:
        raise DisconnectedProposalLifecycleRejected("synthetic constructor changed")
    return event
