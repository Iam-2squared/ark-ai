"""Read-only stale-trigger guard for disconnected proactive preparation fixtures.

A persisted 'prepared' row is never permission to notify or act. All clocks,
policy identities and source hashes are caller supplied; no external consent,
monotonic time, backend identity or real-world action is authenticated here.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .proactive_synthetic_continuity_review import (
    _ROWS,
    SyntheticTriggerWitness,
    _digest,
    assert_proactive_history_continues,
)
from .proactive_synthetic_review import (
    _MAX,
    _HEX,
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
    if retained is not None:
        if type(retained) is not SyntheticTriggerWitness:
            raise SyntheticTriggerRejected("exact retained proactive witness required")
        retained.assert_integrity()
    pinned = policy.identity()
    scope = _hash("ARK-trigger-scope-v1", pinned[:4])
    policy_hash = _hash("ARK-trigger-policy-v1", pinned)
    expected = "trigger_" + _hash(
        "ARK-trigger-occurrence-v1",
        (scope, policy_hash, source_digest, observation_digest),
    )
    if receipt.trigger_id != expected:
        raise SyntheticTriggerRejected("stale or mismatched prepared trigger policy")

    uri = ledger.path.resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, isolation_level=None)) as conn:
        conn.execute("BEGIN")
        try:
            _validate(conn)
            rows = tuple(conn.execute(_ROWS))
            row_hashes = tuple(sorted(
                _digest("ARK-trigger-row-v1", row) for row in rows
            ))
            current = SyntheticTriggerWitness(
                row_hashes,
                "synthetic_triggers_" + _digest(
                    "ARK-trigger-witness-v1", row_hashes,
                ),
            )
            current.assert_integrity()
            if retained is not None:
                assert_proactive_history_continues(retained, current)
            matching = tuple(row for row in rows if row[0] == expected)
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
            conn.commit()
            return SyntheticProactiveFreshnessReview(
                expected, prepared, now_ms, current,
            )
        except BaseException:
            conn.rollback()
            raise
