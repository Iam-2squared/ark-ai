"""A retained trigger-history witness cannot transiently change during row hashing.

All preparations are disconnected SQLite fixture markers, never notification
or ToolBackend authorization.
"""

from pathlib import Path

import pytest

import ark.proactive_synthetic_continuity_review as continuity
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _ledger(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "triggers.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "fixture", "mock-trigger", 1, "offline-v1",
        1, 100, 10,
    )
    ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=10, now_ms=20,
    )
    ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="c" * 64,
        observed_at_ms=11, now_ms=22,
    )
    return ledger


def test_stable_trigger_witness_remains_content_free_and_locally_replayable(tmp_path):
    ledger = _ledger(tmp_path)
    earlier = continuity.read_proactive_witness(ledger)
    assert len(earlier.row_hashes) == 2
    current = continuity.read_proactive_witness(ledger, retained=earlier)
    assert current == earlier
    assert all(len(item) == 64 for item in earlier.row_hashes)


@pytest.mark.parametrize("change", ("source", "digest", "equal_rows_carrier"))
def test_row_hash_callback_cannot_hide_transient_source_or_history_change(
    tmp_path, monkeypatch, change,
):
    ledger = _ledger(tmp_path)
    retained = continuity.read_proactive_witness(ledger)
    original_path = ledger.path
    original_rows = retained.row_hashes
    original_digest = retained.digest
    digest_function = continuity._digest
    row_calls = 0

    def interrupted_digest(label, data):
        nonlocal row_calls
        result = digest_function(label, data)
        if label == "ARK-trigger-row-v1":
            row_calls += 1
            if row_calls == 1:
                if change == "source":
                    ledger.path = Path(str(original_path))
                elif change == "digest":
                    object.__setattr__(
                        retained, "digest", "synthetic_triggers_" + "f" * 64,
                    )
                else:
                    object.__setattr__(
                        retained, "row_hashes", tuple(list(original_rows)),
                    )
            elif row_calls == 2:
                ledger.path = original_path
                object.__setattr__(retained, "digest", original_digest)
                object.__setattr__(retained, "row_hashes", original_rows)
        return result

    monkeypatch.setattr(continuity, "_digest", interrupted_digest)
    with pytest.raises(
        SyntheticTriggerRejected, match="source or retained history changed",
    ):
        continuity.read_proactive_witness(ledger, retained=retained)
    assert row_calls == 1
