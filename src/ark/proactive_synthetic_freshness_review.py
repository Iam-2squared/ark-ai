"""Read-only stale-trigger guard for disconnected proactive preparation fixtures.

A persisted 'prepared' row is never permission to notify or act. All clocks,
policy identities and source hashes are caller supplied; no external consent,
monotonic time, backend identity or real-world action is authenticated here.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .proactive_synthetic_continuity_review import (
    _ORIGINAL_WITNESS_VALIDATOR,
    _ROWS,
    SyntheticTriggerWitness,
    _digest,
    assert_proactive_history_continues,
)
from .proactive_synthetic_review import (
    _HEX,
    _MAX,
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
    SyntheticTriggerRejected,
    _hash,
    _validate,
)


@dataclass(frozen=True, slots=True)
class SyntheticProactiveFreshnessReview:
    trigger_id: str
    prepared_at_ms: int
    checked_at_ms: int
    history: SyntheticTriggerWitness

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


# Results are inert witnesses, not approval tokens. Preserve the original
# denial descriptors even if an equally False-valued property is substituted
# by a fixture hook; that would be a different (unreviewed) authority epoch.
_FRESHNESS_RESULT = SyntheticProactiveFreshnessReview
_FRESHNESS_DENIALS = (
    "notification_authorized", "dispatch_authorized",
    "automatic_replay_authorized",
)
_FRESHNESS_ORIGINAL_DENIALS = tuple(
    vars(_FRESHNESS_RESULT)[name] for name in _FRESHNESS_DENIALS
)



# In addition to the authority descriptors, the slotted output fields and
# construction/lookup hooks must remain original before private fixture rows
# are read. A substituted constructor is executable code, not evidence.
_FRESHNESS_FIELDS = (
    "trigger_id", "prepared_at_ms", "checked_at_ms", "history",
)
_FRESHNESS_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_FRESHNESS_ORIGINAL_FIELDS = tuple(
    vars(_FRESHNESS_RESULT).get(name) for name in _FRESHNESS_FIELDS
)
_FRESHNESS_ORIGINAL_HOOKS = tuple(
    vars(_FRESHNESS_RESULT).get(name) for name in _FRESHNESS_HOOKS
)


def _assert_original_freshness_carriers() -> None:
    if (
        SyntheticProactiveFreshnessReview is not _FRESHNESS_RESULT
        or any(
            vars(_FRESHNESS_RESULT).get(name) is not original
            for names, originals in (
                (_FRESHNESS_FIELDS, _FRESHNESS_ORIGINAL_FIELDS),
                (_FRESHNESS_HOOKS, _FRESHNESS_ORIGINAL_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticTriggerRejected("freshness output carrier definition changed")

def _assert_original_freshness_denial(name: str) -> None:
    index = _FRESHNESS_DENIALS.index(name)
    if (
        SyntheticProactiveFreshnessReview is not _FRESHNESS_RESULT
        or vars(_FRESHNESS_RESULT).get(name) is not _FRESHNESS_ORIGINAL_DENIALS[index]
    ):
        raise SyntheticTriggerRejected("freshness review output changed authority epoch")


def review_prepared_trigger_freshness(
    ledger: SyntheticProactiveLedger,
    receipt: SyntheticTriggerReceipt,
    policy: SyntheticTriggerPolicy,
    *,
    source_digest: str,
    observation_digest: str,
    now_ms: int,
    max_observation_age_ms: int,
    retained: SyntheticTriggerWitness | None = None,
) -> SyntheticProactiveFreshnessReview:
    """Rebind an earlier prepared marker to exact policy and fresh observation.

    This uses one read-only SQLite snapshot and optional independently retained
    history evidence. A success proves local fixture consistency only. It
    cannot rule out replacement of all unfenced local evidence.
    """
    _assert_original_freshness_carriers()
    if (
        type(ledger) is not SyntheticProactiveLedger
        or type(receipt) is not SyntheticTriggerReceipt
        or type(policy) is not SyntheticTriggerPolicy
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        or type(max_observation_age_ms) is not int
        or not 0 <= max_observation_age_ms <= _MAX
        or type(receipt.prepared_at_ms) is not int
        or not 0 <= receipt.prepared_at_ms <= _MAX
        or type(source_digest) is not str or not _HEX.fullmatch(source_digest)
        or type(observation_digest) is not str
        or not _HEX.fullmatch(observation_digest)
    ):
        raise SyntheticTriggerRejected("exact synthetic freshness inputs required")
    if retained is not None and type(retained) is not SyntheticTriggerWitness:
        raise SyntheticTriggerRejected("exact retained proactive witness required")
    # Frozen carriers remain reflectively mutable: pin the exact inputs
    # before the read transaction and fail closed on an observed edit.
    receipt_epoch = (receipt.trigger_id, receipt.prepared_at_ms)
    ledger_path = ledger.path
    if not isinstance(ledger_path, Path):
        raise SyntheticTriggerRejected("proactive ledger path changed")
    retained_epoch = (
        (retained.row_hashes, retained.digest) if retained is not None else None
    )
    policy_fields = (
        "owner", "namespace", "definition_id", "revision", "policy_revision",
        "minimum_interval_ms", "rolling_window_ms",
        "max_preparations_per_window",
    )
    # Equal-valued replacements are still a different fixture-input epoch:
    # preserve each carrier, not merely the policy's matching field values.
    policy_carriers = tuple(getattr(policy, name) for name in policy_fields)
    policy_epoch = tuple((type(value), value) for value in policy_carriers)

    def assert_epoch() -> None:
        _assert_original_freshness_carriers()
        current_carriers = tuple(getattr(policy, name) for name in policy_fields)
        current_policy = tuple((type(value), value) for value in current_carriers)
        if (
            ledger.path is not ledger_path
            or type(receipt.trigger_id) is not str
            or type(receipt.prepared_at_ms) is not int
            or (receipt.trigger_id, receipt.prepared_at_ms) != receipt_epoch
            or receipt.trigger_id is not receipt_epoch[0]
            or receipt.prepared_at_ms is not receipt_epoch[1]
            or current_policy != policy_epoch
            or any(
                current is not original
                for current, original in zip(
                    current_carriers, policy_carriers, strict=True,
                )
            )
            or retained is not None and (
                (retained.row_hashes, retained.digest) != retained_epoch
                or retained.row_hashes is not retained_epoch[0]
                or retained.digest is not retained_epoch[1]
            )
        ):
            raise SyntheticTriggerRejected(
                "freshness evidence changed during read-only review"
            )

    # The first caller-supplied integrity hook is reentrant. Pin path,
    # receipt, policy and retained witness BEFORE calling it, then run the
    # original validator too: substituting a no-op hook cannot bless an
    # invalid retained digest or a newly retargeted SQLite source.
    if retained is not None:
        assert_epoch()
        retained.assert_integrity()
        assert_epoch()
        _ORIGINAL_WITNESS_VALIDATOR(retained)
        assert_epoch()

    pinned = policy.identity()
    assert_epoch()
    scope = _hash("ARK-trigger-scope-v1", pinned[:4])
    policy_hash = _hash("ARK-trigger-policy-v1", pinned)
    expected = "trigger_" + _hash(
        "ARK-trigger-occurrence-v1",
        (scope, policy_hash, source_digest, observation_digest),
    )
    if receipt.trigger_id != expected:
        raise SyntheticTriggerRejected("stale or mismatched prepared trigger policy")
    assert_epoch()

    uri = ledger_path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
        conn.execute("BEGIN")
        try:
            _validate(conn)
            assert_epoch()
            rows = tuple(conn.execute(_ROWS))
            assert_epoch()
            row_hashes = tuple(sorted(
                _digest("ARK-trigger-row-v1", row) for row in rows
            ))
            assert_epoch()
            current = SyntheticTriggerWitness(
                row_hashes,
                "synthetic_triggers_" + _digest(
                    "ARK-trigger-witness-v1", row_hashes,
                ),
            )
            # The newly constructed witness can be reflected upon by the
            # integrity/continuity hooks; preserve its original carriers
            # independently of the outer caller-input epoch.
            current_rows_epoch = current.row_hashes
            current_digest_epoch = current.digest

            def assert_current_epoch() -> None:
                if (
                    type(current) is not SyntheticTriggerWitness
                    or current.row_hashes is not current_rows_epoch
                    or current.digest is not current_digest_epoch
                ):
                    raise SyntheticTriggerRejected(
                        "freshness history changed during read-only review"
                    )

            current.assert_integrity()
            assert_current_epoch()
            assert_epoch()
            if retained is not None:
                assert_proactive_history_continues(retained, current)
                assert_current_epoch()
                assert_epoch()
            matching = tuple(row for row in rows if row[0] == expected)
            assert_epoch()
            if len(matching) != 1:
                raise SyntheticTriggerRejected("prepared trigger receipt no longer exists")
            (_trigger, row_scope, row_policy, row_source, row_observation,
             observed, prepared) = matching[0]
            if (
                (row_scope, row_policy, row_source, row_observation) != (
                    scope, policy_hash, source_digest, observation_digest,
                )
                or prepared != receipt.prepared_at_ms
            ):
                raise SyntheticTriggerRejected("persisted prepared marker changed")
            if (
                observed > prepared or prepared > now_ms
                or now_ms - observed > max_observation_age_ms
            ):
                raise SyntheticTriggerRejected("prepared observation stale or clock regressed")
            if policy.identity() != pinned:
                raise SyntheticTriggerRejected("policy changed during freshness review")
            assert_current_epoch()
            assert_epoch()
            conn.commit()
            assert_current_epoch()
            assert_epoch()
            # A reflected callback may replace the exported review class
            # or its deny-only descriptors before construction. Do not run a
            # counterfeit constructor even if it returns an inert-looking row.
            for name in _FRESHNESS_DENIALS:
                _assert_original_freshness_denial(name)
            review = _FRESHNESS_RESULT(
                expected, prepared, now_ms, current,
            )
            # A forged or reflectively edited result must not escape merely
            # because the SQLite snapshot and its pre-construction witness
            # were valid. No notification or dispatch authority is created.
            assert_current_epoch()
            assert_epoch()
            if (
                type(review) is not SyntheticProactiveFreshnessReview
                or review.trigger_id is not expected
                or type(review.prepared_at_ms) is not int
                or review.prepared_at_ms != prepared
                or type(review.checked_at_ms) is not int
                or review.checked_at_ms != now_ms
                or review.history is not current
            ):
                raise SyntheticTriggerRejected(
                    "freshness review output changed during construction"
                )
            # A deny-only getter is a synthetic callback: check its exact
            # original descriptor, then revalidate every result/source carrier
            # before proceeding to the next getter. A False-valued replacement
            # must not turn an otherwise valid review into unreviewed authority.
            for name in _FRESHNESS_DENIALS:
                # Prior result/source checks themselves can be reentrant.
                # Validate the original property BEFORE invoking its getter.
                _assert_original_freshness_denial(name)
                if getattr(review, name) is not False:
                    raise SyntheticTriggerRejected(
                        "freshness review output changed authority"
                    )
                _assert_original_freshness_denial(name)
                assert_current_epoch()
                assert_epoch()
                if (
                    type(review) is not _FRESHNESS_RESULT
                    or review.trigger_id is not expected
                    or review.prepared_at_ms != prepared
                    or review.checked_at_ms != now_ms
                    or review.history is not current
                ):
                    raise SyntheticTriggerRejected(
                        "freshness review output changed after authority checks"
                    )
            # A later getter can also replace a *previous* descriptor.
            for name in _FRESHNESS_DENIALS:
                _assert_original_freshness_denial(name)
            assert_current_epoch()
            assert_epoch()
            return review
        except BaseException:
            conn.rollback()
            raise
