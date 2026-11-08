"""Offline Context prefix reviews never feed linkable metadata to swapped digests.

Synthetic SQLite fixtures only; no consent, disclosure, external action or
independent custody is inferred from matching retained chain hashes.
"""

from types import SimpleNamespace

import pytest

import ark.personal_context_replay_prefix_review as prefix
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    genesis_offline_context_replay_witness,
)


def _review_inputs(tmp_path):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "context-prefix.sqlite", create=True,
    )
    return ledger, genesis_offline_context_replay_witness()


@pytest.mark.parametrize(
    "mutation", ("hash_module", "sha256", "json_module", "dumps", "domain"),
)
def test_swapped_primitive_denied_before_retained_data_or_sqlite(
    tmp_path, monkeypatch, mutation,
):
    ledger, retained = _review_inputs(tmp_path)
    called = []

    def hostile(*_args, **_kwargs):
        called.append("hostile")
        raise AssertionError("linkable context digest reached hostile callback")

    def no_sqlite(*_args, **_kwargs):
        called.append("sqlite")
        raise AssertionError("SQLite accessed after primitive substitution")

    with monkeypatch.context() as patch:
        patch.setattr(ledger, "_open", no_sqlite)
        if mutation == "hash_module":
            patch.setattr(prefix, "hashlib", SimpleNamespace(sha256=hostile))
        elif mutation == "sha256":
            patch.setattr(prefix.hashlib, "sha256", hostile)
        elif mutation == "json_module":
            patch.setattr(prefix, "json", SimpleNamespace(dumps=hostile))
        elif mutation == "dumps":
            patch.setattr(prefix.json, "dumps", hostile)
        else:
            patch.setattr(prefix, "_DOMAIN", bytes(prefix._DOMAIN) + b"altered")
        with pytest.raises(
            prefix.OfflineContextPrefixRejected,
            match="context prefix digest implementation changed",
        ):
            prefix.review_retained_context_replay_prefix(ledger, retained)

    assert called == []


def test_post_read_primitive_swap_is_rejected_before_digest(
    tmp_path, monkeypatch,
):
    ledger, retained = _review_inputs(tmp_path)
    original_inspect = prefix.replay._inspect
    called = []

    def hostile(*_args, **_kwargs):
        called.append("digest")
        raise AssertionError("linkable chain metadata reached hostile hash")

    with monkeypatch.context() as patch:
        def mutate_at_read(conn):
            observed = original_inspect(conn)
            patch.setattr(prefix.hashlib, "sha256", hostile)
            return observed

        patch.setattr(prefix.replay, "_inspect", mutate_at_read)
        with pytest.raises(
            prefix.OfflineContextPrefixRejected,
            match="context prefix digest implementation changed",
        ):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    assert called == []


def test_unchanged_genesis_review_remains_strictly_non_authorizing(tmp_path):
    ledger, retained = _review_inputs(tmp_path)
    result = prefix.review_retained_context_replay_prefix(ledger, retained)
    assert result.retained_count == 0
    assert result.current_count == 0
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    for name in prefix._DENIAL_NAMES:
        assert getattr(result, name) is False
