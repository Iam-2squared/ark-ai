"""Coherent read-only snapshot of multiple synthetic improvement proposals.

Independent single-proposal reads can straddle another local commit. This
module views all requested IDs under one SQLite read transaction. The returned
snapshot is not human review, authenticated history, an approval, or permission
to execute, train, edit code, or retry an uncertain write.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from . import disconnected_proposal_lifecycle as lifecycle
from . import disconnected_proposal_store as store


class DisconnectedProposalBatchRejected(ValueError):
    """The detached proposal snapshot could not be verified coherently."""


@dataclass(frozen=True, slots=True)
class DetachedProposalBatchSnapshot:
    proposal_ids: tuple[str, ...]
    tips: tuple[lifecycle.DetachedProposalLifecycleTip | None, ...]
    witness: store.DetachedProposalStoreWitness

    @property
    def human_review_authenticated(self) -> bool:
        return False

    @property
    def code_change_authorized(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def automatic_retry_authorized(self) -> bool:
        return False


_REPORT = DetachedProposalBatchSnapshot
_REPORT_INIT = vars(_REPORT)["__init__"]
_FIELDS = ("proposal_ids", "tips", "witness")
_DENIALS = (
    "human_review_authenticated", "code_change_authorized",
    "training_authorized", "automatic_retry_authorized",
)
_ORIGINAL_FIELDS = tuple(vars(_REPORT)[n] for n in _FIELDS)
_ORIGINAL_DENIALS = tuple(vars(_REPORT)[n] for n in _DENIALS)
_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_HOOKS = tuple(vars(_REPORT).get(name) for name in _HOOKS)
_STORE_SCAN = store._scan
_STORE_PATH = store._path
_STORE_ASSERT = store._assert_retained
_STORE_WITNESS = store._witness
_LIFECYCLE_ID = lifecycle._id
_LIFECYCLE_REPLAY = lifecycle.replay_disconnected_proposal_lifecycle
_STORE_PROTOCOL = store._protocol
_LIFECYCLE_PROTOCOL = lifecycle._protocol
_MAX_IDS = 32


def _protocol() -> None:
    # Never invoke a substituted dependent control-plane validator.
    if store._protocol is not _STORE_PROTOCOL or lifecycle._protocol is not _LIFECYCLE_PROTOCOL:
        raise DisconnectedProposalBatchRejected("proposal batch protocol changed")
    _STORE_PROTOCOL()
    _LIFECYCLE_PROTOCOL()
    if (
        _protocol is not _ORIGINAL_PROTOCOL
        DetachedProposalBatchSnapshot is not _REPORT
        or vars(_REPORT).get("__init__") is not _REPORT_INIT
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _FIELDS + _DENIALS,
                _ORIGINAL_FIELDS + _ORIGINAL_DENIALS,
                strict=True,
            )
        )
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(_HOOKS, _ORIGINAL_HOOKS, strict=True)
        )
        or store._scan is not _STORE_SCAN
        or store._path is not _STORE_PATH
        or store._assert_retained is not _STORE_ASSERT
        or store._witness is not _STORE_WITNESS
        or lifecycle._id is not _LIFECYCLE_ID
        or lifecycle.replay_disconnected_proposal_lifecycle is not _LIFECYCLE_REPLAY
        or type(_MAX_IDS) is not int or _MAX_IDS != 32
    ):
        raise DisconnectedProposalBatchRejected("proposal batch protocol changed")


_ORIGINAL_PROTOCOL = _protocol


def inspect_disconnected_proposal_batch(
    path: Path,
    *,
    proposal_ids: tuple[str, ...],
    retained: store.DetachedProposalStoreWitness,
    require_latest: bool = False,
) -> DetachedProposalBatchSnapshot:
    """Return ordered tips from one SQLite history epoch, without effects.

    Retained prefix matching detects some local rollbacks, but a hash alone
    cannot authenticate history or prove that an unseen later commit did not
    occur. When require_latest=True, the retained witness must match this
    transaction's full validated event frontier, not merely a past prefix.
    This API never permits proposal state advancement.
    """
    _ORIGINAL_PROTOCOL()
    if type(require_latest) is not bool:
        raise DisconnectedProposalBatchRejected(
            "exact latest-frontier requirement flag required"
        )
    if (
        type(proposal_ids) is not tuple
        or not 1 <= len(proposal_ids) <= _MAX_IDS
        or any(type(p) is not str for p in proposal_ids)
        or len(set(proposal_ids)) != len(proposal_ids)
    ):
        raise DisconnectedProposalBatchRejected(
            "exact bounded unique proposal IDs required"
        )
    try:
        for proposal_id in proposal_ids:
            _LIFECYCLE_ID(proposal_id)
        retained_tuple = _STORE_WITNESS(retained)
        verified_path = _STORE_PATH(path, create=False)
    except (ValueError, TypeError, OSError) as exc:
        raise DisconnectedProposalBatchRejected(
            "proposal batch inputs or local path rejected"
        ) from exc

    pinned_ids = proposal_ids

    def stable() -> None:
        _ORIGINAL_PROTOCOL()
        if (
            proposal_ids is not pinned_ids
            or _STORE_WITNESS(retained) != retained_tuple
            or (retained.event_count, retained.chain_digest) != retained_tuple
        ):
            raise DisconnectedProposalBatchRejected(
                "proposal batch retained evidence changed"
            )

    stable()
    try:
        with closing(sqlite3.connect(
            verified_path.as_uri() + "?mode=ro",
            uri=True, isolation_level=None,
        )) as conn:
            conn.execute("BEGIN")
            try:
                witness, histories, prefixes = _STORE_SCAN(conn)
                _STORE_ASSERT(
                    retained_tuple, prefixes, latest_required=require_latest,
                )
                tips = tuple(
                    _LIFECYCLE_REPLAY(pid, histories[pid])
                    if pid in histories else None
                    for pid in pinned_ids
                )
                stable()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
        _STORE_PATH(verified_path, create=False)
    except (OSError, sqlite3.Error, store.DisconnectedProposalStoreRejected) as exc:
        raise DisconnectedProposalBatchRejected(
            "coherent proposal batch inspection rejected"
        ) from exc

    stable()
    result = _REPORT(pinned_ids, tips, witness)
    stable()
    if (
        type(result) is not _REPORT
        or result.proposal_ids is not pinned_ids
        or result.tips is not tips
        or result.witness is not witness
        or any(getattr(result, name) is not False for name in _DENIALS)
    ):
        raise DisconnectedProposalBatchRejected(
            "proposal batch result gained authority or changed"
        )
    stable()
    return result
