"""Restart triage reuses original witness class/field custody before metadata reads.

Only disposable synthetic SQLite hashes are used. No consent, live tools, or
automatic replay follows from a locally consistent restart review.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.personal_context_replay_ledger as replay
import ark.personal_context_replay_recovery as recovery

_ATTACKS = ("count", "chain_sha256", "__init__", "__getattribute__", "__getattr__")


def _fixture(tmp_path):
    ledger = replay.DisconnectedContextReplayLedger(
        tmp_path / "recovery-preaccess.sqlite", create=True,
    )
    return ledger, ledger.witness()


def _install(monkeypatch, name, hits):
    def poisoned(*_args, **_kwargs):
        hits.append(name)
        raise AssertionError("untrusted witness hook executed")

    replacement = property(poisoned) if name in ("count", "chain_sha256") else poisoned
    monkeypatch.setattr(
        replay.OfflineContextReplayWitness, name, replacement, raising=False,
    )


@pytest.mark.parametrize("name", _ATTACKS)
def test_direct_recovery_witness_fields_refuse_poisoned_class_before_read(
    tmp_path, monkeypatch, name,
):
    _, witness = _fixture(tmp_path)
    hits = []
    _install(monkeypatch, name, hits)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="invalid exact context replay witness",
    ):
        recovery._witness_fields(witness)
    assert hits == []


@pytest.mark.parametrize("name", _ATTACKS)
def test_preinstalled_witness_poison_never_opens_recovery_sqlite(
    tmp_path, monkeypatch, name,
):
    ledger, witness = _fixture(tmp_path)
    hits = []
    _install(monkeypatch, name, hits)

    def forbidden_open(*_args, **_kwargs):
        raise AssertionError("recovery accessed SQLite before witness guard")

    monkeypatch.setattr(replay.DisconnectedContextReplayLedger, "_open", forbidden_open)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="invalid exact context replay witness",
    ):
        recovery.review_restarted_context_replay(ledger, witness)
    assert hits == []


@pytest.mark.parametrize("name", _ATTACKS)
def test_reentrant_witness_callback_cannot_reinstall_original_field_hooks(
    tmp_path, monkeypatch, name,
):
    ledger, witness = _fixture(tmp_path)
    hits = []
    original = ledger.witness

    def returned_observed_then_poisoned():
        observed = original()
        _install(monkeypatch, name, hits)
        return observed

    monkeypatch.setattr(ledger, "witness", returned_observed_then_poisoned)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="invalid exact context replay witness",
    ):
        recovery.review_restarted_context_replay(ledger, witness)
    assert hits == []


def test_recovery_rejects_replaced_inherited_new_in_child_python():
    # CPython may retain a poisoned tp_new slot after deleting __new__.
    script = textwrap.dedent("""
        import ark.personal_context_replay_ledger as replay
        import ark.personal_context_replay_recovery as recovery

        original = replay.genesis_offline_context_replay_witness()
        calls = []

        def poisoned(*args, **kwargs):
            calls.append("new")
            raise AssertionError("allocation hook executed")

        replay.OfflineContextReplayWitness.__new__ = staticmethod(poisoned)
        try:
            recovery._witness_fields(original)
        except recovery.OfflineContextRecoveryRejected as exc:
            assert "invalid exact context replay witness" in str(exc)
        else:
            raise AssertionError("unsafe allocation hook accepted")
        assert calls == []
    """)
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_healthy_restarted_review_remains_diagnostic_only(tmp_path):
    ledger, witness = _fixture(tmp_path)
    reopened = replay.DisconnectedContextReplayLedger(ledger._path)
    result = recovery.review_restarted_context_replay(reopened, witness)
    assert (result.retained_count, result.observed_count) == (0, 0)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.independent_custody_proven is False
    assert result.consent_verified is False
    assert result.automatic_replay_authorized is False
