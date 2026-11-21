"""Disconnected context replay protocol seals guard local private hash metadata.

All stores are disposable fixtures. No context text, consent, notification,
external effect, authenticated provenance or real tool dispatch is used.
"""

from __future__ import annotations

import re

import pytest

import ark.personal_context_replay_ledger as replay


@pytest.mark.parametrize("callback", ("sha256", "dumps"))
@pytest.mark.parametrize(
    "operation", ("create", "restart", "witness", "prefix", "genesis"),
)
def test_replaced_digest_callback_refused_before_private_use(
    tmp_path, monkeypatch, callback: str, operation: str,
) -> None:
    path = tmp_path / "existing.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    retained = ledger.witness()
    new_path = tmp_path / "new.sqlite"
    observed: list[object] = []

    def untrusted(*args, **_kwargs):
        observed.extend(args)
        raise AssertionError("untrusted digest callback accessed context metadata")

    dependency = replay.hashlib if callback == "sha256" else replay.json
    with monkeypatch.context() as patch:
        patch.setattr(dependency, callback, untrusted)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            if operation == "create":
                replay.DisconnectedContextReplayLedger(new_path, create=True)
            elif operation == "restart":
                replay.DisconnectedContextReplayLedger(path, create=False)
            elif operation == "witness":
                ledger.witness()
            elif operation == "prefix":
                ledger.verify_retained_prefix(retained)
            else:
                replay.genesis_offline_context_replay_witness()
    assert observed == []
    assert not new_path.exists()
    assert ledger.witness() == retained


@pytest.mark.parametrize(
    ("constant", "replacement"),
    (
        ("_DOMAIN", b"forged-context-replay-domain"),
        ("_DDL", "CREATE TABLE forged_context(id TEXT)"),
        ("_SHA", re.compile(r".*")),
        ("_REQUEST", re.compile(r".*")),
        ("_MAX_ROWS", 513),
        ("_MAX_ROWS", 512.0),
    ),
)
def test_mutated_protocol_constants_refused_before_file_inventory(
    tmp_path, monkeypatch, constant: str, replacement: object,
) -> None:
    path = tmp_path / "new-context.sqlite"
    with monkeypatch.context() as patch:
        patch.setattr(replay, constant, replacement)
        with pytest.raises(
            replay.OfflineContextReplayRejected,
            match="context replay protocol authority changed",
        ):
            replay.DisconnectedContextReplayLedger(path, create=True)
    assert not path.exists()


def test_unmodified_context_replay_genesis_and_cold_read_are_inert(tmp_path) -> None:
    path = tmp_path / "existing.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    retained = ledger.witness()
    assert retained == replay.genesis_offline_context_replay_witness()
    reopened = replay.DisconnectedContextReplayLedger(path, create=False)
    observed = reopened.verify_retained_prefix(retained)
    assert observed == retained
    assert observed.independent_custody_proven is False
