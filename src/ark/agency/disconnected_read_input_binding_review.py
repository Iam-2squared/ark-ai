"""Offline exact-input join for an independently retained synthetic READ journal.

The existing recovery bridge validates states, topological receipt order, and
result hashes. It does not know the digest of the *intended input* for a step.
This opt-in second check closes that diagnostic gap for a caller-retained input
manifest. A caller-controlled manifest is NOT authentication, execution proof,
consent, or a license to replay.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .disconnected_read_journal import (
    ReadJournalRejected,
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _require_original_read_carriers,
    _require_original_snapshot_class,
)
from .disconnected_read_recovery_journal_bridge import (
    ReadRecoveryJournalRejected,
    ReadRecoveryJournalReview,
    review_detached_read_journal_recovery,
)
from .disconnected_read_recovery_journal_bridge import (
    _require_original_report as _require_original_recovery_report,
)
from .disconnected_read_recovery_schedule import ReadRecoveryStep

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_DOMAIN = b"ARK-detached-read-expected-input-join-v1\0"


class ReadInputBindingRejected(ValueError):
    """The retained input claims do not match the recovered READ receipts."""


@dataclass(frozen=True, slots=True)
class ReadInputBindingReview:
    request_id: str
    successful_step_ids: tuple[str, ...]
    journal_tip_sha256: str
    recovery_review_sha256: str
    input_binding_sha256: str

    @property
    def backend_dispatched(self) -> bool:
        return False

    @property
    def external_result_proven(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False


_REPORT_TYPE = ReadInputBindingReview
_FIELDS = (
    "request_id", "successful_step_ids", "journal_tip_sha256",
    "recovery_review_sha256", "input_binding_sha256",
)
_DENIALS = (
    "backend_dispatched", "external_result_proven",
    "automatic_replay_authorized", "independent_custody_proven",
)
_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_FIELDS = tuple(vars(_REPORT_TYPE)[name] for name in _FIELDS)
_ORIGINAL_DENIALS = tuple(vars(_REPORT_TYPE)[name] for name in _DENIALS)
_ORIGINAL_HOOKS = tuple(vars(_REPORT_TYPE).get(name) for name in _HOOKS)
# These are independent dependency identities, not merely output values. A
# replaced digest/serializer or recovery function can leak the caller's exact
# input manifest, counterfeit a receipt check or execute hostile code.
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_RECOVERY_REVIEW = review_detached_read_journal_recovery
# Rebinding a local digest domain or broadening a regex changes which private
# expected inputs the review accepts, even when the recomputed digest is valid.
# The checks are in-process integrity fences, not authenticated custody.
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_SHA_PATTERN = _SHA
_ORIGINAL_STEP_PATTERN = _STEP


def _require_original_report() -> None:
    if (
        ReadInputBindingReview is not _REPORT_TYPE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or review_detached_read_journal_recovery is not _ORIGINAL_RECOVERY_REVIEW
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _SHA is not _ORIGINAL_SHA_PATTERN
        or _STEP is not _ORIGINAL_STEP_PATTERN
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for names, originals in (
                (_FIELDS, _ORIGINAL_FIELDS),
                (_DENIALS, _ORIGINAL_DENIALS),
                (_HOOKS, _ORIGINAL_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise ReadInputBindingRejected("input-join report authority changed")
    # Do not let hostile substituted snapshot/receipt descriptors inspect caller
    # journal evidence before the delegated recovery reviewer can check them.
    try:
        _require_original_read_carriers()
        _require_original_snapshot_class()
        _require_original_recovery_report()
    except (ReadJournalRejected, ReadRecoveryJournalRejected) as exc:
        raise ReadInputBindingRejected("READ input carrier contract changed") from exc


def review_detached_read_input_binding(
    request_id: str,
    steps: tuple[ReadRecoveryStep, ...],
    snapshot: ReadJournalSnapshot,
    retained: ReadJournalWitness,
    expected_inputs: tuple[tuple[str, str], ...],
) -> ReadInputBindingReview:
    """Match every SUCCEEDED receipt to the expected per-step input digest.

    The manifest is ordered by successful *plan* steps, not receipt append
    order. It must contain exactly those successful steps, no extra or missing
    claims. Failed, running, unknown and unstarted steps have no input proof.
    The caller must independently preserve the expected input manifest and
    journal witness; this function cannot certify their provenance.
    """
    _require_original_report()
    if (
        type(expected_inputs) is not tuple or len(expected_inputs) > 24
        or any(
            type(item) is not tuple or len(item) != 2
            or type(item[0]) is not str or _STEP.fullmatch(item[0]) is None
            or type(item[1]) is not str or _SHA.fullmatch(item[1]) is None
            for item in expected_inputs
        )
    ):
        raise ReadInputBindingRejected("invalid exact input digest manifest")
    # Pin caller-provided built-in immutable scalars before any recovery hook.
    expected = tuple(expected_inputs)
    if len({item[0] for item in expected}) != len(expected):
        raise ReadInputBindingRejected("duplicate expected READ input")
    # Run the original full topological, journal, and result validation first.
    # No input-only hash comparison can substitute for that complete check.
    base: ReadRecoveryJournalReview = review_detached_read_journal_recovery(
        request_id, steps, snapshot, retained,
    )
    _require_original_report()
    if type(base) is not ReadRecoveryJournalReview:
        raise ReadInputBindingRejected("READ recovery receipt class changed")
    if tuple(item[0] for item in expected) != base.successful_step_ids:
        raise ReadInputBindingRejected("expected inputs do not cover exact successes")
    if (
        type(snapshot) is not ReadJournalSnapshot
        or type(snapshot.receipts) is not tuple
        or len(snapshot.receipts) != len(expected)
    ):
        raise ReadInputBindingRejected("READ receipt set changed")
    # Freeze the independently validated journal, retained tip, and plan step
    # identities across the input join, digest and report denial callbacks.
    # Frozen dataclasses alone do not guarantee their slots stay unchanged.
    original_rows = snapshot.receipts
    original_witness = snapshot.witness
    row_epoch = tuple((
        row, row.request_id, row.step_id, row.operation,
        row.input_digest, row.result_digest,
    ) for row in original_rows)
    step_epoch = tuple((
        step, step.step_id, step.operation, step.depends_on,
        step.state, step.result_sha256,
    ) for step in steps)
    witness_epoch = (original_witness.count, original_witness.tip_sha256)
    retained_epoch = (retained.count, retained.tip_sha256)
    base_epoch = (
        base.request_id, base.successful_step_ids,
        base.journal_tip_sha256, base.review_sha256,
    )

    def assert_epoch() -> None:
        _require_original_report()
        if (
            type(snapshot) is not ReadJournalSnapshot
            or snapshot.receipts is not original_rows
            or snapshot.witness is not original_witness
            or type(retained) is not ReadJournalWitness
            or type(original_witness) is not ReadJournalWitness
            or (original_witness.count, original_witness.tip_sha256)
            != witness_epoch
            or (retained.count, retained.tip_sha256) != retained_epoch
            or type(base) is not ReadRecoveryJournalReview
            or any(now is not first for now, first in zip(
                (base.request_id, base.successful_step_ids,
                 base.journal_tip_sha256, base.review_sha256),
                base_epoch, strict=True,
            ))
            or len(original_rows) != len(row_epoch)
            or len(steps) != len(step_epoch)
            or any(
                type(original) is not ReadReceipt
                or original_rows[index] is not original
                or any(now is not first for now, first in zip(
                    (original.request_id, original.step_id, original.operation,
                     original.input_digest, original.result_digest),
                    fields, strict=True,
                ))
                for index, (original, *fields) in enumerate(row_epoch)
            )
            or any(
                steps[index] is not original
                or any(now is not first for now, first in zip(
                    (original.step_id, original.operation, original.depends_on,
                     original.state, original.result_sha256),
                    fields, strict=True,
                ))
                for index, (original, *fields) in enumerate(step_epoch)
            )
        ):
            raise ReadInputBindingRejected("READ input evidence changed during join")

    assert_epoch()
    by_step = {receipt.step_id: receipt for receipt in original_rows}
    if len(by_step) != len(expected):
        raise ReadInputBindingRejected("duplicate recovered READ receipt")
    for step_id, digest in expected:
        assert_epoch()
        row = by_step.get(step_id)
        if row is None or row.input_digest != digest:
            raise ReadInputBindingRejected("recovered READ input digest disagrees")
    assert_epoch()
    payload = (
        request_id, base.review_sha256, base.journal_tip_sha256, expected,
    )
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(
            payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    assert_epoch()
    expected_report = (
        request_id, base.successful_step_ids,
        base.journal_tip_sha256, base.review_sha256, digest,
    )
    result = _REPORT_TYPE(*expected_report)
    assert_epoch()
    def assert_report() -> None:
        assert_epoch()
        if (
            type(result) is not _REPORT_TYPE
            or any(
                getattr(result, field) is not original
                for field, original in zip(_FIELDS, expected_report, strict=True)
            )
        ):
            raise ReadInputBindingRejected("READ input binding result changed")

    assert_report()
    for name in _DENIALS:
        assert_report()
        if getattr(result, name) is not False:
            raise ReadInputBindingRejected("READ input binding gained authority")
        assert_report()
    assert_report()
    return result
