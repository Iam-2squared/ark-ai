"""SQLite-observed context witness must be exact, not merely equal.

The fixture stores only request digests; tests never authorize disclosure.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import personal_context_replay_ledger as replay
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_request_binding import bind_offline_context_request


def _binding():
    text = "synthetic private context"
    record = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64, text,
        hashlib.sha256(text.encode("utf-8")).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (record,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + "1" * 64, preview)


@pytest.mark.parametrize("forged_read", (1, 2))
def test_reserve_rejects_equal_value_nonexact_sqlite_witness(
    tmp_path, monkeypatch, forged_read,
):
    path = tmp_path / "context.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    genesis = replay.genesis_offline_context_replay_witness()
    original = replay._inspect

    class StringSubtype(str):
        pass

    checks = 0

    def altered_inspect(conn):
        nonlocal checks
        result = original(conn)
        checks += 1
        if checks != forged_read:
            return result
        forged = replay.OfflineContextReplayWitness(
            result.count, StringSubtype(result.chain_sha256),
        )
        assert forged == result
        assert type(forged.chain_sha256) is not str
        return forged

    with monkeypatch.context() as patch:
        patch.setattr(replay, "_inspect", altered_inspect)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="invalid exact retained context witness",
        ):
            ledger.reserve(_binding(), retained=genesis)

    # This must not be a post-COMMIT refusal with a newly reserved request.
    assert ledger.witness() == genesis
