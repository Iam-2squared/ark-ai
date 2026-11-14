"""Read-only, manual-only triage of an uncertain synthetic proposal CAS.

The observations here are SQLite snapshots, not a durable external action
receipt, authenticated approval, or proof that a process did not commit and
roll back. In particular, OBSERVED_UNCHANGED does NOT authorize a retry.
This module never opens a writer, dispatches a tool, or calls a model.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import disconnected_proposal_lifecycle as lifecycle
from . import disconnected_proposal_store as store


class OfflineProposalUnknownCommitRejected(ValueError):
    """The proposed reconciliation input or read-only result is unreliable."""


OBSERVED_UNCHANGED = "OBSERVED_UNCHANGED"
OBSERVED_EXACT_APPEND = "OBSERVED_EXACT_APPEND"
MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class OfflineProposalUnknownCommitReport:
    disposition: str
    observed_witness: store.DetachedProposalStoreWitness
    observed_tip: lifecycle.DetachedProposalLifecycleTip | None
    expected_next_global_digest: str

    @property
    def automatic_retry_authorized(self) -> bool:
        return False

    @property
    def code_change_authorized(self) -> bool:
        return False

    @property
    def human_review_authenticated(self) -> bool:
        return False

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def candidate_promotion_authorized(self) -> bool:
        return False


_REPORT = OfflineProposalUnknownCommitReport
_REPORT_INIT = vars(_REPORT)["__init__"]
_REPORT_NAMES = (
    "disposition", "observed_witness", "observed_tip",
    "expected_next_global_digest",
)
_DENIAL_NAMES = (
    "automatic_retry_authorized", "code_change_authorized",
    "human_review_authenticated", "training_authorized",
    "candidate_promotion_authorized",
)
_REPORT_ORIGINALS = tuple(vars(_REPORT)[n] for n in _REPORT_NAMES + _DENIAL_NAMES)
_REPORT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_HOOKS = tuple(vars(_REPORT).get(n) for n in _REPORT_HOOKS)
_ORIGINAL_DISPOSITIONS = (
    OBSERVED_UNCHANGED, OBSERVED_EXACT_APPEND, MANUAL_REVIEW_REQUIRED,
)
_STORE_INSPECT = store.inspect_disconnected_proposal_store
_STORE_HASH = store._hash
_STORE_WITNESS = store._witness
_STORE_TIP = store._tip
_LIFECYCLE_PREPARE = lifecycle.prepare_disconnected_proposal_transition
_LIFECYCLE_ID = lifecycle._id
_TIP_TYPE = lifecycle.DetachedProposalLifecycleTip
_SNAPSHOT_TYPE = store.DetachedProposalStoreSnapshot
_WITNESS_TYPE = store.DetachedProposalStoreWitness
_STORE_PROTOCOL = store._protocol
_LIFECYCLE_PROTOCOL = lifecycle._protocol


def _protocol() -> None:
    if store._protocol is not _STORE_PROTOCOL or lifecycle._protocol is not _LIFECYCLE_PROTOCOL:
        raise OfflineProposalUnknownCommitRejected("proposal reconciliation protocol changed")
    _STORE_PROTOCOL()
    _LIFECYCLE_PROTOCOL()
    if (
        _protocol is not _ORIGINAL_PROTOCOL
        or _tip_fields is not _ORIGINAL_TIP_FIELDS
        or OfflineProposalUnknownCommitReport is not _REPORT
        or vars(_REPORT).get("__init__") is not _REPORT_INIT
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _REPORT_NAMES + _DENIAL_NAMES, _REPORT_ORIGINALS, strict=True,
            )
        )
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS, strict=True,
            )
        )
        or any(
            now is not original
            for now, original in zip(
                (OBSERVED_UNCHANGED, OBSERVED_EXACT_APPEND, MANUAL_REVIEW_REQUIRED),
                _ORIGINAL_DISPOSITIONS, strict=True,
            )
        )
        or store.inspect_disconnected_proposal_store is not _STORE_INSPECT
        or store._hash is not _STORE_HASH
        or store._witness is not _STORE_WITNESS
        or store._tip is not _STORE_TIP
        or lifecycle.prepare_disconnected_proposal_transition is not _LIFECYCLE_PREPARE
        or lifecycle._id is not _LIFECYCLE_ID
        or lifecycle.DetachedProposalLifecycleTip is not _TIP_TYPE
        or store.DetachedProposalStoreSnapshot is not _SNAPSHOT_TYPE
        or store.DetachedProposalStoreWitness is not _WITNESS_TYPE
    ):
        raise OfflineProposalUnknownCommitRejected(
            "proposal reconciliation protocol changed"
        )


_ORIGINAL_PROTOCOL = _protocol


def _tip_fields(value: lifecycle.DetachedProposalLifecycleTip | None) -> tuple | None:
    if value is None:
        return None
    return (
        value.proposal_id, value.revision, value.state, value.event_digest,
    )


# A replaced local tip-image helper could forge a matching post-commit tip,
# misclassifying an uncertain CAS as OBSERVED_EXACT_APPEND. Pin it before
# inspecting retained SQLite or caller-owned tip metadata.
_ORIGINAL_TIP_FIELDS = _tip_fields


def review_disconnected_proposal_unknown_commit(
    path: Path,
    *,
    proposal_id: str,
    new_state: str,
    expected_revision: int,
    expected_tip: lifecycle.DetachedProposalLifecycleTip | None,
    retained_before: store.DetachedProposalStoreWitness,
) -> OfflineProposalUnknownCommitReport:
    """Classify only an observed persisted snapshot, never resolve authorization.

    OBSERVED_EXACT_APPEND means the *current validated SQLite prefix* has
    precisely the expected next event and no intervening global event. A
    forged/rolled-back database or an untrusted witness still cannot establish
    independent provenance. Every disposition requires manual reconciliation
    before any separate operation; none permits a WRITE replay.
    """
    _ORIGINAL_PROTOCOL()
    try:
        _LIFECYCLE_ID(proposal_id)
        before_count, before_digest = _STORE_WITNESS(retained_before)
        pinned_tip = _STORE_TIP(expected_tip, proposal_id)
        if (
            type(expected_revision) is not int
            or not 0 <= expected_revision < 256
            or expected_revision != (0 if pinned_tip is None else pinned_tip[0])
            or before_count >= 512
        ):
            raise OfflineProposalUnknownCommitRejected(
                "inconsistent proposal CAS expectation"
            )
        event = _LIFECYCLE_PREPARE(proposal_id, expected_tip, new_state)
    except (ValueError, TypeError, AttributeError) as exc:
        raise OfflineProposalUnknownCommitRejected(
            "invalid proposed unknown-commit event"
        ) from exc

    initial_tip = _tip_fields(expected_tip)
    initial_witness = (retained_before.event_count, retained_before.chain_digest)
    candidate_digest = _STORE_HASH((
        "event", before_digest, before_count + 1,
        event.proposal_id, event.revision, event.prior_state,
        event.new_state, event.previous_digest, event.event_digest,
    ))
    proposed_tip = (
        event.proposal_id, event.revision, event.new_state, event.event_digest,
    )

    def stable() -> None:
        _ORIGINAL_PROTOCOL()
        if (
            _STORE_WITNESS(retained_before) != (before_count, before_digest)
            or (
                retained_before.event_count,
                retained_before.chain_digest,
            ) != initial_witness
            or _STORE_TIP(expected_tip, proposal_id) != pinned_tip
            or _tip_fields(expected_tip) != initial_tip
        ):
            raise OfflineProposalUnknownCommitRejected(
                "caller reconciliation evidence changed"
            )

    stable()
    # The only storage operation in this module is the existing read-only
    # coherent-snapshot inspection. It also checks the retained global prefix.
    observed = _STORE_INSPECT(
        path, proposal_id=proposal_id, retained=retained_before,
    )
    stable()
    if (
        type(observed) is not _SNAPSHOT_TYPE
        or type(observed.witness) is not _WITNESS_TYPE
        or observed.human_review_authenticated is not False
        or observed.execution_authorized is not False
        or observed.candidate_promotion_authorized is not False
        or observed.witness.externally_authenticated is not False
    ):
        raise OfflineProposalUnknownCommitRejected(
            "proposal reconciliation snapshot gained authority"
        )
    actual_witness = _STORE_WITNESS(observed.witness)
    actual_tip = _STORE_TIP(observed.proposal_tip, proposal_id)
    if actual_witness == (before_count, before_digest) and actual_tip == pinned_tip:
        disposition = OBSERVED_UNCHANGED
    elif (
        actual_witness == (before_count + 1, candidate_digest)
        and _tip_fields(observed.proposal_tip) == proposed_tip
    ):
        disposition = OBSERVED_EXACT_APPEND
    else:
        disposition = MANUAL_REVIEW_REQUIRED
    stable()
    report = _REPORT(
        disposition, observed.witness, observed.proposal_tip, candidate_digest,
    )
    stable()
    if (
        type(report) is not _REPORT
        or report.disposition != disposition
        or report.observed_witness is not observed.witness
        or report.observed_tip is not observed.proposal_tip
        or report.expected_next_global_digest != candidate_digest
        or any(getattr(report, name) is not False for name in _DENIAL_NAMES)
    ):
        raise OfflineProposalUnknownCommitRejected(
            "proposal reconciliation result changed or gained authority"
        )
    return report
