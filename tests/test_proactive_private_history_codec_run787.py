"""Offline proactive history refuses rewritten codecs before private row access.

Only disposable SQLite fixtures. Witnesses are not notification consent or
an execution grant, and in-process Python remains outside the trust boundary.
"""

import pytest

import ark.proactive_synthetic_continuity_review as continuity
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "proactive-codec.sqlite")
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "private", "mock-trigger", 1, "fixture-v1",
        1, 100, 10,
    )
    ledger.prepare(
        policy, source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=10, now_ms=20,
    )
    retained = continuity.read_proactive_witness(ledger)
    return ledger, retained


@pytest.mark.parametrize(
    "target",
    ("sha256", "json_dumps", "row_query", "budget_expand", "budget_bool"),
)
@pytest.mark.parametrize("entrypoint", ("read", "compare"))
def test_rewritten_witness_codec_fails_before_read_or_hash(
    tmp_path, monkeypatch, target, entrypoint,
):
    ledger, retained = _fixture(tmp_path)
    callbacks = []
    opened = []

    def poisoned(*args, **kwargs):
        callbacks.append(target)
        raise AssertionError("private proactive row reached modified codec")

    def forbidden_connect(*args, **kwargs):
        opened.append(target)
        raise AssertionError("private proactive database opened after codec drift")

    with monkeypatch.context() as patch:
        if target == "sha256":
            patch.setattr(continuity.hashlib, "sha256", poisoned)
        elif target == "json_dumps":
            patch.setattr(continuity.json, "dumps", poisoned)
        elif target == "row_query":
            patch.setattr(
                continuity, "_ROWS",
                "SELECT * FROM synthetic_prepared_triggers WHERE 1=0",
            )
        elif target == "budget_expand":
            patch.setattr(continuity, "_MAX_WITNESS_ROWS", 100_001)
        else:
            patch.setattr(continuity, "_MAX_WITNESS_ROWS", True)
        patch.setattr(continuity.sqlite3, "connect", forbidden_connect)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive witness carrier changed",
        ):
            if entrypoint == "read":
                continuity.read_proactive_witness(ledger, retained=retained)
            else:
                continuity.assert_proactive_history_continues(retained, retained)
    assert callbacks == []
    assert opened == []


def test_sqlite_open_rebind_cannot_hash_private_trigger_rows(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    original_connect = continuity.sqlite3.connect
    row_hashes = []
    real_digest = continuity._digest

    def observe_hash(label, data):
        if label == "ARK-trigger-row-v1":
            row_hashes.append(label)
        return real_digest(label, data)

    def rebind_during_open(*args, **kwargs):
        conn = original_connect(*args, **kwargs)
        monkeypatch.setattr(continuity, "_ROWS", "SELECT 1")
        return conn

    with monkeypatch.context() as patch:
        patch.setattr(continuity, "_digest", observe_hash)
        patch.setattr(continuity.sqlite3, "connect", rebind_during_open)
        with pytest.raises(
            SyntheticTriggerRejected, match="proactive witness carrier changed",
        ):
            continuity.read_proactive_witness(ledger, retained=retained)
    assert row_hashes == []


def test_small_test_budget_and_intact_codec_still_deny_dispatch(
    tmp_path, monkeypatch,
):
    ledger, retained = _fixture(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(continuity, "_MAX_WITNESS_ROWS", 1)
        current = continuity.read_proactive_witness(ledger, retained=retained)
    assert current == retained
    assert len(current.row_hashes) == 1
    continuity.assert_proactive_history_continues(retained, current)
