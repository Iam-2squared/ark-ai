"""Read-only, restart-safe correlation of a retained act_/req_ link and journal.

Journal v1 deliberately has NO registered-action column. A caller-supplied
link and witness are separate, untrusted local evidence; neither their hashes
nor successful SQLite reconciliation authenticate a historical actor or grant
execution/replay. This module never appends a row or calls a ToolBackend.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from .contracts import CapabilityGrant, ToolCall
from .disconnected_fixture_binding import DisconnectedFixtureBinding
from .disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadJournalWitness,
    _check_receipt,
    _check_witness,
)
from .disconnected_read_receipt_bridge import (
    DisconnectedReadBridgeRejected,
    prepare_disconnected_read_receipt,
)
from .disconnected_registered_fixture_join import (
    RegisteredFixtureLink,
    RegisteredFixtureLinkRejected,
    review_registered_disconnected_fixture,
)
from .disconnected_toolbox import DisconnectedToolRequest, DisconnectedToolResult
from .policy import PermissionGate
from .registry import ToolRegistry

_LINK_FIELDS = (
    "step_id", "action_request_id", "fixture_request_id", "registry_revision",
    "bound_action_id", "request_bound_digest", "result_digest", "link_sha256",
)
_LINK_DENIALS = (
    "backend_dispatched", "external_result_proven", "write_authorized",
    "replay_authorized", "trusted_clock_or_consent_proven",
)


class RegisteredReceiptReviewRejected(ValueError):
    """The retained local READ link cannot be reconciled to this snapshot."""


@dataclass(frozen=True, slots=True)
class RegisteredReceiptReview:
    step_id: str
    action_request_id: str
    fixture_request_id: str
    link_sha256: str
    journal_count: int
    journal_tip_sha256: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


_REVIEW_TYPE = RegisteredReceiptReview
_REVIEW_DENIALS = (
    "backend_dispatched", "external_effect_proven",
    "replay_authorized", "independent_custody_proven",
)
_ORIGINAL_REVIEW_DENIALS = tuple(
    vars(_REVIEW_TYPE)[name] for name in _REVIEW_DENIALS
)
# Frozen instances do not freeze their class. Original result/link slot
# descriptors and allocation/lookup hooks must survive before the first
# retained SQLite read, even when a replacement returns an inert False.
_REVIEW_FIELDS = (
    "step_id", "action_request_id", "fixture_request_id",
    "link_sha256", "journal_count", "journal_tip_sha256",
)
_REVIEW_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REVIEW_FIELDS = tuple(
    vars(_REVIEW_TYPE)[name] for name in _REVIEW_FIELDS
)
_ORIGINAL_REVIEW_HOOKS = tuple(
    vars(_REVIEW_TYPE).get(name) for name in _REVIEW_HOOKS
)
_LINK_TYPE = RegisteredFixtureLink
_ORIGINAL_LINK_DENIALS = tuple(
    vars(_LINK_TYPE)[name] for name in _LINK_DENIALS
)
_LINK_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_LINK_FIELDS = tuple(vars(_LINK_TYPE)[name] for name in _LINK_FIELDS)
_ORIGINAL_LINK_HOOKS = tuple(
    vars(_LINK_TYPE).get(name) for name in _LINK_HOOKS
)


def _assert_original_denial_definitions() -> None:
    if (
        RegisteredReceiptReview is not _REVIEW_TYPE
        or RegisteredFixtureLink is not _LINK_TYPE
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in (
                (_REVIEW_TYPE, _REVIEW_FIELDS, _ORIGINAL_REVIEW_FIELDS),
                (_REVIEW_TYPE, _REVIEW_HOOKS, _ORIGINAL_REVIEW_HOOKS),
                (_REVIEW_TYPE, _REVIEW_DENIALS, _ORIGINAL_REVIEW_DENIALS),
                (_LINK_TYPE, _LINK_FIELDS, _ORIGINAL_LINK_FIELDS),
                (_LINK_TYPE, _LINK_HOOKS, _ORIGINAL_LINK_HOOKS),
                (_LINK_TYPE, _LINK_DENIALS, _ORIGINAL_LINK_DENIALS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise RegisteredReceiptReviewRejected(
            "read-only reconciliation authority definition changed"
        )


def review_retained_registered_receipt(
    journal: DisconnectedReadJournal,
    retained: ReadJournalWitness,
    link: RegisteredFixtureLink,
    registry: ToolRegistry,
    gate: PermissionGate,
    call: ToolCall,
    grants: tuple[CapabilityGrant, ...],
    step_id: str,
    request: DisconnectedToolRequest,
    result: DisconnectedToolResult,
    binding: DisconnectedFixtureBinding,
    *,
    observed_at_ms: int,
) -> RegisteredReceiptReview:
    """Reconcile one exact persisted row inside ONE SQLite read transaction.

    A stale witness, edited row, mismatched registered identity, or changed
    caller carrier is rejected. Even a successful review is diagnostic only.
    The original retained witness/link must come from independently retained
    evidence for historical tamper detection; this function cannot certify it.
    """
    _assert_original_denial_definitions()
    if (
        type(journal) is not DisconnectedReadJournal
        or type(retained) is not ReadJournalWitness
        or type(link) is not RegisteredFixtureLink
    ):
        raise RegisteredReceiptReviewRejected("exact detached journal/link required")

    try:
        _check_witness(retained)
        link_epoch = tuple(getattr(link, name) for name in _LINK_FIELDS)
        witness_epoch = (retained.count, retained.tip_sha256)

        def stable() -> None:
            _assert_original_denial_definitions()
            _check_witness(retained)
            if (
                type(link) is not RegisteredFixtureLink
                or type(retained) is not ReadJournalWitness
                or any(
                    getattr(link, name) is not original
                    for name, original in zip(_LINK_FIELDS, link_epoch, strict=True)
                )
                or retained.count is not witness_epoch[0]
                or retained.tip_sha256 is not witness_epoch[1]
                or any(getattr(link, name) is not False for name in _LINK_DENIALS)
            ):
                raise RegisteredReceiptReviewRejected("retained READ link/witness changed")

        def rebind() -> None:
            # Deliberately repeat the original registry/grant/fixture verification
            # AFTER the database snapshot too: reading a synthetic SQL row does
            # not prevent mutation of independently supplied Python carriers.
            actual = review_registered_disconnected_fixture(
                registry, gate, call, grants, step_id, request, result,
                binding, observed_at_ms=observed_at_ms,
            )
            stable()
            if (
                type(actual) is not RegisteredFixtureLink
                or tuple(getattr(actual, name) for name in _LINK_FIELDS) != link_epoch
                or any(getattr(actual, name) is not False for name in _LINK_DENIALS)
            ):
                raise RegisteredReceiptReviewRejected(
                    "registered action or fixture differs from retained link"
                )

        stable()
        rebind()
        receipt = prepare_disconnected_read_receipt(step_id, request, result, binding)
        _check_receipt(receipt)
        receipt_epoch = (
            receipt.request_id, receipt.step_id, receipt.operation,
            receipt.input_digest, receipt.result_digest,
        )
        stable()
        if receipt_epoch[0] != link_epoch[2] or receipt_epoch[1] != link_epoch[0]:
            raise RegisteredReceiptReviewRejected("retained link and receipt differ")

        started = False
        try:
            journal._connection.execute("BEGIN")
            started = True
            # The complete chain and the target row must be examined under the
            # SAME read snapshot, not two consecutive verify/select epochs.
            actual_witness = journal._scan()
            rows = journal._connection.execute(
                "SELECT request_id, step_id, operation, input_digest, result_digest "
                "FROM receipts WHERE request_id=? AND step_id=?",
                (receipt_epoch[0], receipt_epoch[1]),
            ).fetchall()
            stable()
            if (
                type(actual_witness) is not ReadJournalWitness
                or (actual_witness.count, actual_witness.tip_sha256) != witness_epoch
                or len(rows) != 1
                or tuple(rows[0]) != receipt_epoch
                or any(getattr(actual_witness, name) is not False for name in (
                    "dispatch_authorized", "effect_proven", "replay_authorized",
                    "independent_custody_proven",
                ))
            ):
                raise RegisteredReceiptReviewRejected(
                    "retained witness or READ row differs from SQLite snapshot"
                )
            journal._connection.execute("COMMIT")
            started = False
        finally:
            if started and journal._connection.in_transaction:
                journal._connection.execute("ROLLBACK")

        stable()
        rebind()
        # Re-read the retained output carriers after the last authority getter.
        reviewed = RegisteredReceiptReview(
            link_epoch[0], link_epoch[1], link_epoch[2], link_epoch[7],
            witness_epoch[0], witness_epoch[1],
        )
        expected = (
            *link_epoch[:3], link_epoch[7], *witness_epoch,
        )
        def stable_review() -> None:
            _assert_original_denial_definitions()
            fields = (
                reviewed.step_id, reviewed.action_request_id,
                reviewed.fixture_request_id, reviewed.link_sha256,
                reviewed.journal_count, reviewed.journal_tip_sha256,
            )
            if (
                type(reviewed) is not RegisteredReceiptReview
                or any(a is not b for a, b in zip(fields, expected, strict=True))
                or reviewed.backend_dispatched is not False
                or reviewed.external_effect_proven is not False
                or reviewed.replay_authorized is not False
                or reviewed.independent_custody_proven is not False
            ):
                raise RegisteredReceiptReviewRejected(
                    "read-only reconciliation gained authority"
                )
            # A false-valued authority getter can still mutate frozen dataclass
            # fields through object.__setattr__. Inspect *after* the last getter;
            # never return a result whose witness/identity changed mid-denial.
            after = (
                reviewed.step_id, reviewed.action_request_id,
                reviewed.fixture_request_id, reviewed.link_sha256,
                reviewed.journal_count, reviewed.journal_tip_sha256,
            )
            _assert_original_denial_definitions()
            if any(a is not b for a, b in zip(after, expected, strict=True)):
                raise RegisteredReceiptReviewRejected(
                    "read-only reconciliation changed after authority denial"
                )

        stable_review()
        stable()
        stable_review()
        # Last denial callbacks may mutate *either* the detached witness or
        # the original registry/call/grant/fixture carriers. Repeat the READ
        # binding without dispatch and inspect our output one final time.
        stable()
        rebind()
        stable()
        if any(a is not b for a, b in zip((
            reviewed.step_id, reviewed.action_request_id,
            reviewed.fixture_request_id, reviewed.link_sha256,
            reviewed.journal_count, reviewed.journal_tip_sha256,
        ), expected, strict=True)):
            raise RegisteredReceiptReviewRejected(
                "read-only reconciliation changed at return"
            )
        return reviewed
    except (
        ReadJournalRejected, DisconnectedReadBridgeRejected,
        RegisteredFixtureLinkRejected, sqlite3.Error,
    ) as exc:
        raise RegisteredReceiptReviewRejected(
            "retained READ reconciliation failed closed"
        ) from exc
