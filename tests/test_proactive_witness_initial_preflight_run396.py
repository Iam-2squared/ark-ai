"""A first retained-witness callback cannot rebase an offline scheduler review.

No notification, ToolBackend, consent or real-world effect is involved.
"""

from pathlib import Path

import pytest

from ark.proactive_synthetic_continuity_review import (
    SyntheticTriggerWitness,
    _digest,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _setup(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "offline-scheduler.sqlite")
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "fixture", "mock", 1, "rev1", 5, 100, 4,
    )
    ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=20, now_ms=20,
    )
    return ledger, read_proactive_witness(ledger)


@pytest.mark.parametrize("attack", ("path", "weaker_valid", "equal_tuple"))
def test_first_integrity_hook_cannot_rebase_source_or_history(
    tmp_path, monkeypatch, attack,
):
    ledger, retained = _setup(tmp_path)
    original_path = ledger.path
    original = SyntheticTriggerWitness.assert_integrity
    empty = SyntheticTriggerWitness(
        (), "synthetic_triggers_" + _digest("ARK-trigger-witness-v1", ()),
    )
    empty.assert_integrity()
    checked = 0

    def replace_after_validating(self):
        nonlocal checked
        original(self)
        if self is retained:
            checked += 1
            if checked == 1:
                if attack == "path":
                    ledger.path = Path(str(original_path))
                elif attack == "weaker_valid":
                    object.__setattr__(retained, "row_hashes", empty.row_hashes)
                    object.__setattr__(retained, "digest", empty.digest)
                else:
                    object.__setattr__(
                        retained, "row_hashes", tuple(list(retained.row_hashes)),
                    )

    monkeypatch.setattr(
        SyntheticTriggerWitness, "assert_integrity", replace_after_validating,
    )
    with pytest.raises(
        SyntheticTriggerRejected, match="source or retained history changed",
    ):
        read_proactive_witness(ledger, retained=retained)
    assert checked == 1


def test_unchanged_retained_history_still_rechecks_cleanly(tmp_path):
    ledger, retained = _setup(tmp_path)
    fresh = read_proactive_witness(ledger, retained=retained)
    assert fresh == retained
    assert len(fresh.row_hashes) == 1
