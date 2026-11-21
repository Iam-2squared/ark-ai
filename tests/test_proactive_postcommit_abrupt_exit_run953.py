"""Run953: proactive synthetic marker cannot become a notification after exit.

No OS timer, notification, model invocation, real source or trusted clock.
The child and parent use disposable on-disk fixture state only.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "owner", "private", "synthetic-definition", 1, "revision-1",
        100, 10_000, 2,
    )


@pytest.mark.parametrize("committed", (False, True))
def test_abrupt_exit_does_not_reissue_committed_proactive_occurrence(
    tmp_path, committed: bool,
) -> None:
    path = tmp_path / "synthetic-proactive-child-exit.sqlite3"
    code = """
import os
import sys
from pathlib import Path
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger, SyntheticTriggerPolicy,
)
policy = SyntheticTriggerPolicy(
    "owner", "private", "synthetic-definition", 1, "revision-1",
    100, 10_000, 2,
)
ledger = SyntheticProactiveLedger(Path(sys.argv[1]))
if sys.argv[2] == "commit":
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=100, now_ms=100,
    )
    assert receipt.dispatch_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
os._exit(43)
"""
    child = subprocess.run(
        [
            sys.executable, "-c", code, str(path),
            "commit" if committed else "no-commit",
        ],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert child.returncode == 43, child.stderr

    cold = SyntheticProactiveLedger(path)
    assert cold.count() == int(committed)
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT trigger_id,source_digest,observation_digest,"
            "observed_at_ms,prepared_at_ms FROM synthetic_prepared_triggers"
        ).fetchall()
    assert len(rows) == int(committed)

    # A fresh local preparation may succeed only if the earlier COMMIT never
    # happened. An old occurrence is never manufactured twice by cold reopen.
    if committed:
        with pytest.raises(SyntheticTriggerRejected):
            cold.prepare(
                _policy(), source_digest="a" * 64, observation_digest="b" * 64,
                observed_at_ms=100, now_ms=250,
            )
    else:
        receipt = cold.prepare(
            _policy(), source_digest="a" * 64, observation_digest="b" * 64,
            observed_at_ms=100, now_ms=250,
        )
        assert receipt.notification_authorized is False
        assert receipt.dispatch_authorized is False
        assert receipt.automatic_replay_authorized is False

    assert cold.count() == 1
    with sqlite3.connect(path) as conn:
        final_rows = conn.execute(
            "SELECT trigger_id,source_digest,observation_digest,"
            "observed_at_ms,prepared_at_ms FROM synthetic_prepared_triggers"
        ).fetchall()
    assert len(final_rows) == 1
    assert final_rows[0][1:4] == ("a" * 64, "b" * 64, 100)
    if committed:
        assert final_rows == rows
    # Local marker presence is not a proven notification or external effect.
