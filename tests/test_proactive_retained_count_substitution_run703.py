"""Proactive restart refuses count-preserving local history substitution.

The independent retained digest is supplied by the fixture caller. It is not
consent, notification authority, or authenticated remote scheduler evidence.
"""

import sqlite3

import pytest

from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)

SOURCE = "a" * 64
OBSERVATIONS = tuple(char * 64 for char in "bcde")
POLICY = SyntheticTriggerPolicy(
    "fixture-user", "private", "daily-check", 1, "v1",
    1, 10, 3,
)


def _prepare(ledger, index, at_ms, *, retained=None):
    return ledger.prepare(
        POLICY, source_digest=SOURCE, observation_digest=OBSERVATIONS[index],
        observed_at_ms=at_ms, now_ms=at_ms, retained=retained,
    )


@pytest.mark.parametrize("removed_index", (0, 1, 2))
def test_reopened_proactive_history_refuses_delete_and_new_append_substitution(
    tmp_path, removed_index,
):
    path = tmp_path / "proactive-wal.sqlite"
    ledger = SyntheticProactiveLedger(path)
    original_receipts = tuple(_prepare(ledger, i, 100 + i) for i in range(3))
    retained = read_proactive_witness(ledger)
    assert len(retained.row_hashes) == 3

    # Separate SQLite writer replaces one historical occurrence with a new
    # independently valid marker. The resulting database still has three
    # rows, valid digests and a syntactically legitimate schema.
    with sqlite3.connect(path) as conn:
        conn.execute(
            "DELETE FROM synthetic_prepared_triggers WHERE trigger_id=?",
            (original_receipts[removed_index].trigger_id,),
        )

    replacement = _prepare(SyntheticProactiveLedger(path), 3, 110)
    assert replacement.notification_authorized is False
    assert replacement.dispatch_authorized is False

    restarted = SyntheticProactiveLedger(path)
    current = read_proactive_witness(restarted)
    assert len(current.row_hashes) == len(retained.row_hashes) == 3
    assert current.digest != retained.digest

    with pytest.raises(
        SyntheticTriggerRejected, match="retained proactive trigger history changed",
    ):
        read_proactive_witness(restarted, retained=retained)

    # A rejected old witness must not silently admit another preparation.
    with pytest.raises(SyntheticTriggerRejected):
        _prepare(restarted, removed_index, 120, retained=retained)
    assert restarted.count() == 3
