"""The Personal Context replay CAS tip must survive post-commit callbacks."""

from __future__ import annotations

import hashlib

import pytest

import ark.personal_context_replay_ledger as replay
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import bind_offline_context_request


def _binding():
    text = "private fixture; must not enter replay ledger"
    item = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (item,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + "1" * 64, preview)


@pytest.mark.parametrize("kind", ("count", "sha", "equal_sha"))
def test_postcommit_context_witness_mutation_is_detected(tmp_path, monkeypatch, kind):
    db = replay.DisconnectedContextReplayLedger(
        tmp_path / "replay.sqlite", create=True,
    )
    old = replay.genesis_offline_context_replay_witness()
    original = replay.OfflineContextReplayReceipt

    def tamper(request_id, witness):
        result = original(request_id, witness)
        if kind == "count":
            object.__setattr__(witness, "count", 2)
        elif kind == "sha":
            object.__setattr__(witness, "chain_sha256", "f" * 64)
        else:
            current = witness.chain_sha256
            equal = "".join((current[:11], current[11:]))
            assert equal == current and equal is not current
            object.__setattr__(witness, "chain_sha256", equal)
        return result

    monkeypatch.setattr(replay, "OfflineContextReplayReceipt", tamper)
    with pytest.raises(replay.OfflineContextReplayRejected, match="postcommit context witness"):
        db.reserve(_binding(), retained=old)
    # This is a real local SQLite COMMIT, not a rollback or retry permit.
    assert db.witness().count == 1


def test_context_replay_receipt_remains_inert_after_restart(tmp_path):
    path = tmp_path / "replay.sqlite"
    db = replay.DisconnectedContextReplayLedger(path, create=True)
    old = replay.genesis_offline_context_replay_witness()
    receipt = db.reserve(_binding(), retained=old)
    reopened = replay.DisconnectedContextReplayLedger(path)
    assert reopened.witness() == receipt.witness
    assert receipt.witness.independent_custody_proven is False
    assert receipt.consent_verified is False
    assert receipt.revocation_freshness_verified is False
    assert receipt.context_disclosure_authorized is False
    assert receipt.tool_dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
