"""Local replay witnesses must reject replaced exact-class slots before access.

All fixtures use disposable SQLite or interpreter-local objects; they grant no
context disclosure, authorization, replay, or independent custody.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.personal_context_replay_ledger as replay

_FIELDS = ("count", "chain_sha256")
_HOOKS = ("__init__", "__getattribute__", "__getattr__")


@pytest.mark.parametrize("name", _FIELDS + _HOOKS)
def test_inherited_or_slotted_witness_hook_cannot_run_during_check(monkeypatch, name):
    witness = replay.genesis_offline_context_replay_witness()
    invoked = []

    def poisoned(*_args, **_kwargs):
        invoked.append(name)
        raise AssertionError("poisoned witness hook executed")

    carrier = replay.OfflineContextReplayWitness
    replacement = property(poisoned) if name in _FIELDS else poisoned
    monkeypatch.setattr(carrier, name, replacement, raising=False)
    with pytest.raises(
        replay.OfflineContextReplayRejected,
        match="invalid exact retained context witness",
    ):
        replay._check_witness(witness)
    assert invoked == []


@pytest.mark.parametrize("name", _FIELDS + _HOOKS)
def test_corrupted_witness_class_cannot_enter_genesis_or_row_inspection(
    tmp_path, monkeypatch, name,
):
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "private-fixture.sqlite", create=True,
    )
    invoked = []
    schema_calls = []
    original_schema = replay._schema

    def poisoned(*_args, **_kwargs):
        invoked.append(name)
        raise AssertionError("poisoned witness hook executed")

    def checked_schema(conn):
        schema_calls.append(1)
        return original_schema(conn)

    carrier = replay.OfflineContextReplayWitness
    replacement = property(poisoned) if name in _FIELDS else poisoned
    monkeypatch.setattr(carrier, name, replacement, raising=False)
    monkeypatch.setattr(replay, "_schema", checked_schema)
    with pytest.raises(replay.OfflineContextReplayRejected):
        replay.genesis_offline_context_replay_witness()
    with pytest.raises(replay.OfflineContextReplayRejected):
        ledger.witness()
    assert invoked == []
    assert schema_calls == []


def test_inherited_new_poisoning_is_rejected_in_separate_interpreter():
    # Altering inherited __new__ can permanently poison a CPython type slot
    # even after removing the own attribute. Do not mutate it inside pytest.
    script = textwrap.dedent("""
        import ark.personal_context_replay_ledger as replay
        saved = replay.genesis_offline_context_replay_witness()
        called = []

        def poisoned(*args, **kwargs):
            called.append("new")
            raise AssertionError("poisoned allocation executed")

        replay.OfflineContextReplayWitness.__new__ = staticmethod(poisoned)
        for operation in (
            lambda: replay._check_witness(saved),
            replay.genesis_offline_context_replay_witness,
        ):
            try:
                operation()
            except replay.OfflineContextReplayRejected as exc:
                assert "invalid exact retained context witness" in str(exc)
            else:
                raise AssertionError("poisoned allocation hook was accepted")
        assert not called
    """)
    done = subprocess.run(
        [sys.executable, "-c", script],
        check=False, capture_output=True, text=True, timeout=20,
    )
    assert done.returncode == 0, done.stdout + done.stderr


def test_unmodified_witness_remains_readonly_and_denial_only(tmp_path):
    path = tmp_path / "healthy-fixture.sqlite"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    genesis = replay.genesis_offline_context_replay_witness()
    assert ledger.witness() == genesis
    assert replay._check_witness(genesis) == (genesis.count, genesis.chain_sha256)
    assert ledger.verify_retained_prefix(genesis) == genesis
    assert genesis.independent_custody_proven is False
