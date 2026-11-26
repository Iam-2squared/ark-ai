"""Run966: replay-review veto vectors cannot be shrunk before private reads.

Only empty synthetic SQLite and a retained genesis witness are used. Neither
context disclosure nor a real-world action is performed or authorized.
"""

from __future__ import annotations

import pytest

import ark.personal_context_replay_recovery as recovery
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
)


@pytest.mark.parametrize("name", (
    "_RESULT_FIELDS",
    "_RESULT_HOOKS",
    "_RESULT_DENIALS",
    "_LEDGER_ACCESS_HOOKS",
))
def test_shortened_recovery_guard_vector_cannot_access_replay_ledger(
    tmp_path, monkeypatch, name: str,
) -> None:
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "context-guard.sqlite", create=True,
    )
    retained = ledger.witness()
    with monkeypatch.context() as patch:
        patch.setattr(recovery, name, ())
        with pytest.raises(recovery.OfflineContextRecoveryRejected):
            recovery.review_restarted_context_replay(ledger, retained)
    # The original local witness remains unmodified after a failed review.
    assert ledger.witness().count == 0


def test_unmodified_genesis_review_remains_deny_only(tmp_path) -> None:
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "context-original.sqlite", create=True,
    )
    result = recovery.review_restarted_context_replay(
        ledger, ledger.witness(),
    )
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.context_disclosure_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False
