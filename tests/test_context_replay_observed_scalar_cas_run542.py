"""Pre-COMMIT Personal Context replay checks require exact observed scalars.

Fixture reservations contain only digests; none establish consent or authorize
context disclosure, a real tool, notification, or automatic retry.
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
    payload = "synthetic context fixture"
    fixture = OfflineContextFixture(
        "rec_" + "c" * 32,
        "a" * 64,
        "b" * 64,
        payload,
        hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        1000,
    )
    preview = build_offline_context_preview(
        (fixture,),
        owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,),
        observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + "1" * 64, preview)


@pytest.mark.parametrize("forgery", ["tip", "count"])
def test_postinsert_sqlite_mismatch_rolls_back_even_if_equality_forged(
    tmp_path, monkeypatch, forgery,
):
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.sqlite", create=True,
    )
    genesis = replay.genesis_offline_context_replay_witness()
    real_inspect = replay._inspect
    reads = 0

    def forged_inspect(connection):
        nonlocal reads
        observed = real_inspect(connection)
        reads += 1
        if reads != 2:
            return observed
        if forgery == "tip":
            return replay.OfflineContextReplayWitness(observed.count, "f" * 64)
        return replay.OfflineContextReplayWitness(
            observed.count + 1, observed.chain_sha256,
        )

    with monkeypatch.context() as patch:
        patch.setattr(replay, "_inspect", forged_inspect)
        patch.setattr(
            replay.OfflineContextReplayWitness,
            "__eq__",
            lambda _left, _right: True,
        )
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context reservation integrity mismatch",
        ):
            ledger.reserve(_binding(), retained=genesis)

    witnessed = ledger.witness()
    assert witnessed.count == genesis.count
    assert witnessed.chain_sha256 == genesis.chain_sha256


def test_valid_postinsert_sqlite_witness_does_not_depend_on_equality(
    tmp_path, monkeypatch,
):
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "context.sqlite", create=True,
    )
    genesis = replay.genesis_offline_context_replay_witness()
    with monkeypatch.context() as patch:
        patch.setattr(
            replay.OfflineContextReplayWitness,
            "__eq__",
            lambda _left, _right: False,
        )
        result = ledger.reserve(_binding(), retained=genesis)
    witnessed = ledger.witness()
    assert witnessed.count == 1
    assert witnessed.chain_sha256 == result.witness.chain_sha256
    assert result.consent_verified is False
    assert result.context_disclosure_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
