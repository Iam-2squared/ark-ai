"""Post-COMMIT replay receipts reject substituted constructors before execution.

A committed local hash reservation can survive a rejected return value.
Neither an intact receipt nor a rejected result authorizes disclosure or tools.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.personal_context_replay_ledger as replay
from ark.personal_context_request_binding import OfflineContextRequestBinding


def _binding() -> OfflineContextRequestBinding:
    return OfflineContextRequestBinding(
        "ctxreq_" + "1" * 64, "a" * 64, "b" * 64, 1, "c" * 64,
    )


@pytest.mark.parametrize(
    "attack", ("class", "initializer", "request_slot", "witness_slot", "denial"),
)
def test_receipt_substitution_never_executes_postcommit_injected_code(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str,
) -> None:
    path = tmp_path / "context-replay.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    genesis = replay.genesis_offline_context_replay_witness()
    binding = _binding()
    invoked: list[str] = []

    def trap(*_args: object, **_kwargs: object) -> object:
        invoked.append("forbidden")
        raise AssertionError("substituted receipt code must not execute")

    with monkeypatch.context() as patch:
        receipt_cls = replay.OfflineContextReplayReceipt
        if attack == "class":
            patch.setattr(replay, "OfflineContextReplayReceipt", trap)
        elif attack == "initializer":
            patch.setattr(receipt_cls, "__init__", trap)
        elif attack == "request_slot":
            patch.setattr(receipt_cls, "request_id", property(trap))
        elif attack == "witness_slot":
            patch.setattr(receipt_cls, "witness", property(trap))
        else:
            patch.setattr(
                receipt_cls, "consent_verified", property(lambda _: False),
            )
        with pytest.raises(
            replay.OfflineContextReplayRejected, match="postcommit",
        ):
            ledger.reserve(binding, retained=genesis)

    assert invoked == []
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM context_requests"
        ).fetchone() == (1,)
    assert replay.DisconnectedContextReplayLedger(path).witness().count == 1
    with pytest.raises(replay.OfflineContextReplayRejected, match="stale"):
        ledger.reserve(binding, retained=genesis)


def test_intact_receipt_retains_denial_only_semantics(tmp_path: Path) -> None:
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.sqlite", create=True,
    )
    receipt = ledger.reserve(
        _binding(), retained=replay.genesis_offline_context_replay_witness(),
    )
    assert receipt.witness.count == 1
    assert receipt.consent_verified is False
    assert receipt.revocation_freshness_verified is False
    assert receipt.context_disclosure_authorized is False
    assert receipt.tool_dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
