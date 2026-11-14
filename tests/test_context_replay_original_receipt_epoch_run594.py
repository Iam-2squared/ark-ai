"""Post-COMMIT offline Context replay receipts remain non-authorizing.

These fixtures reserve only hashed request identities in a local SQLite file.
Rejection never implies COMMIT rollback, authenticated consent or disclosure.
"""

from __future__ import annotations

import hashlib
import sqlite3

import pytest

from ark import personal_context_replay_ledger as replay
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import bind_offline_context_request


def _binding():
    text = "disconnected private fixture"
    fixture = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (fixture,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + "1" * 64, preview)


def _ledger(tmp_path):
    return replay.DisconnectedContextReplayLedger(
        tmp_path / "offline-context.sqlite", create=True,
    )


@pytest.mark.parametrize("field", replay._RECEIPT_DENIALS)
def test_equal_false_property_cannot_rebase_committed_receipt_authority(
    tmp_path, monkeypatch, field,
):
    ledger = _ledger(tmp_path)
    retained = replay.genesis_offline_context_replay_witness()
    monkeypatch.setattr(
        replay.OfflineContextReplayReceipt, field, property(lambda _: False),
    )
    with pytest.raises(replay.OfflineContextReplayRejected, match="authority epoch"):
        ledger.reserve(_binding(), retained=retained)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM context_requests").fetchone() == (1,)
    with pytest.raises(replay.OfflineContextReplayRejected, match="stale"):
        ledger.reserve(_binding(), retained=retained)


def test_last_denial_getter_cannot_replace_equal_receipt_id(
    tmp_path, monkeypatch,
):
    ledger = _ledger(tmp_path)
    retained = replay.genesis_offline_context_replay_witness()
    receipt_type = replay.OfflineContextReplayReceipt
    original = receipt_type.__getattribute__
    altered = []

    def reentrant(self, name):
        value = original(self, name)
        if name == "automatic_replay_authorized":
            before = original(self, "request_id")
            substitute = ("!" + before)[1:]
            assert substitute == before and substitute is not before
            object.__setattr__(self, "request_id", substitute)
            altered.append(name)
        return value

    monkeypatch.setattr(receipt_type, "__getattribute__", reentrant)
    with pytest.raises(replay.OfflineContextReplayRejected, match="authority epoch"):
        ledger.reserve(_binding(), retained=retained)
    # Import-pinned receipt lookup now rejects this injected __getattribute__
    # before it can execute, rather than detecting the late equal-ID swap.
    assert altered == []
    assert ledger.witness().count == 1
    with pytest.raises(replay.OfflineContextReplayRejected, match="stale"):
        ledger.reserve(_binding(), retained=retained)


def test_original_receipt_denies_all_external_authority(tmp_path):
    ledger = _ledger(tmp_path)
    receipt = ledger.reserve(
        _binding(), retained=replay.genesis_offline_context_replay_witness(),
    )
    for name in replay._RECEIPT_DENIALS:
        assert getattr(receipt, name) is False
    assert receipt.witness.count == 1
