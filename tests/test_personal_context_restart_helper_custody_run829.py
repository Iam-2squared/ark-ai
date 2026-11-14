"""Restart-only Personal Context helpers must remain import-original.

All inputs are synthetic, hash-only SQLite fixtures. No content, deletion,
external disclosure, consent or automatic replay is exercised.
"""

from __future__ import annotations

import pytest

import ark.personal_context_replay_ledger as ledger_module
import ark.personal_context_replay_recovery as review
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger


@pytest.mark.parametrize(
    ("target", "attribute"),
    (
        ("review", "_check_witness"),
        ("ledger", "_inspect"),
        ("ledger", "_check_witness"),
        ("class", "_open"),
        ("class", "witness"),
    ),
)
def test_replaced_restart_read_helpers_denied_before_private_callback(
    tmp_path, monkeypatch, target: str, attribute: str,
) -> None:
    ledger = DisconnectedContextReplayLedger(tmp_path / "replay.db", create=True)
    retained = ledger.witness()
    invoked: list[str] = []

    def forbidden(*_args, **_kwargs):
        invoked.append(attribute)
        raise AssertionError("substituted context reader executed")

    owner = {
        "review": review,
        "ledger": ledger_module,
        "class": DisconnectedContextReplayLedger,
    }[target]
    monkeypatch.setattr(owner, attribute, forbidden)
    with pytest.raises(
        review.OfflineContextRecoveryRejected, match="access hook changed",
    ):
        review.review_restarted_context_replay(ledger, retained)
    assert invoked == []


@pytest.mark.parametrize("attribute", ("_check_witness",))
def test_rebinding_during_first_restart_witness_callback_denied_before_next_read(
    tmp_path, monkeypatch, attribute: str,
) -> None:
    ledger = DisconnectedContextReplayLedger(tmp_path / "replay.db", create=True)
    retained = ledger.witness()
    read_original = ledger.witness
    invoked: list[str] = []

    def forbidden(*_args, **_kwargs):
        invoked.append("private callback")
        raise AssertionError("rebound context helper executed")

    def mutate_after_first_read():
        observed = read_original()
        monkeypatch.setattr(review, attribute, forbidden)
        return observed

    monkeypatch.setattr(ledger, "witness", mutate_after_first_read)
    with pytest.raises(
        review.OfflineContextRecoveryRejected, match="access hook changed",
    ):
        review.review_restarted_context_replay(ledger, retained)
    assert invoked == []


def test_unmodified_restart_remains_denial_only(tmp_path) -> None:
    ledger = DisconnectedContextReplayLedger(tmp_path / "replay.db", create=True)
    retained = ledger.witness()
    result = review.review_restarted_context_replay(ledger, retained)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.tool_dispatch_authorized is False
    assert result.context_disclosure_authorized is False
    assert result.automatic_replay_authorized is False
