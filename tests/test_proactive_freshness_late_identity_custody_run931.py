"""Late synthetic proactive callbacks may not install a new policy identity.

All fixtures are disconnected, local, and deny-only. A prepared marker is not
consent, notification authority, or permission to perform a tool action.
"""

from __future__ import annotations

import pytest

import ark.proactive_synthetic_freshness_review as freshness
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


@pytest.mark.parametrize(
    "phase", ("retained_integrity", "sqlite_schema", "row_digest", "continuity")
)
def test_reentrant_policy_method_swap_is_rejected_before_new_method_runs(
    tmp_path, monkeypatch, phase: str,
) -> None:
    ledger = SyntheticProactiveLedger(tmp_path / "late-identity.sqlite3")
    policy = SyntheticTriggerPolicy(
        "offline", "fixtures", "job-one", 1, "policy-one", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    retained = read_proactive_witness(ledger)
    calls: list[str] = []

    def unreviewed_identity(_self):
        calls.append("unreviewed")
        raise AssertionError("replaced policy identity executed")

    def install_unreviewed_identity() -> None:
        monkeypatch.setattr(
            SyntheticTriggerPolicy, "identity", unreviewed_identity
        )

    if phase == "retained_integrity":
        original = freshness.SyntheticTriggerWitness.assert_integrity

        def after_integrity(self):
            original(self)
            install_unreviewed_identity()

        monkeypatch.setattr(
            freshness.SyntheticTriggerWitness, "assert_integrity",
            after_integrity,
        )
    elif phase == "sqlite_schema":
        original = freshness._validate

        def after_schema(conn):
            original(conn)
            install_unreviewed_identity()

        monkeypatch.setattr(freshness, "_validate", after_schema)
    elif phase == "row_digest":
        original = freshness._digest

        def after_digest(domain, value):
            result = original(domain, value)
            install_unreviewed_identity()
            return result

        monkeypatch.setattr(freshness, "_digest", after_digest)
    else:
        original = freshness.assert_proactive_history_continues

        def after_continuity(older, newer):
            original(older, newer)
            install_unreviewed_identity()

        monkeypatch.setattr(
            freshness, "assert_proactive_history_continues", after_continuity
        )

    with pytest.raises(SyntheticTriggerRejected, match="policy contract changed"):
        freshness.review_prepared_trigger_freshness(
            ledger,
            receipt,
            policy,
            source_digest="a" * 64,
            observation_digest="b" * 64,
            now_ms=100,
            max_observation_age_ms=10,
            retained=retained,
        )
    assert calls == []
