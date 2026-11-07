"""Retained cancellation evidence and storage identity cannot drift mid-review."""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_approval_cancellation_review as module
from ark.agency.synthetic_approval_cancellation_review import (
    SyntheticCancellationLedger,
    SyntheticCancellationRejected,
)


def _id(label: str) -> str:
    return "approval_" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _fixture(tmp_path: Path):
    ledger = SyntheticCancellationLedger(tmp_path / "veto #1 %.sqlite")
    previous = ledger.cancel_synthetic(_id("first"), at_ms=10)
    return ledger, previous


@pytest.mark.parametrize("operation", ["read", "state", "append"])
def test_retained_witness_cannot_be_replaced_with_valid_older_prefix(
    tmp_path: Path, monkeypatch, operation: str,
):
    ledger, earlier = _fixture(tmp_path)
    original = module._replay

    def reflected_rewrite(conn):
        prefixes = original(conn)
        # A reflected mutation changes the witness to another fully valid
        # prefix. Structural and hash checks alone would now accept it.
        genesis = prefixes[0]
        object.__setattr__(earlier, "event_count", genesis.event_count)
        object.__setattr__(earlier, "tail_hash", genesis.tail_hash)
        object.__setattr__(
            earlier, "last_cancelled_at_ms", genesis.last_cancelled_at_ms,
        )
        return prefixes

    monkeypatch.setattr(module, "_replay", reflected_rewrite)
    with pytest.raises(SyntheticCancellationRejected, match="retained witness changed"):
        if operation == "read":
            ledger.read_witness(retained=earlier)
        elif operation == "state":
            ledger.review_state(_id("first"), retained=earlier)
        else:
            ledger.cancel_synthetic(
                _id("second"), at_ms=11, retained=earlier,
            )
    # Inspect using a fresh, unmodified ledger and its exact persisted row.
    monkeypatch.setattr(module, "_replay", original)
    assert SyntheticCancellationLedger(ledger.path).read_witness().event_count == 1


@pytest.mark.parametrize("operation", ["read", "state", "append"])
def test_reflected_source_retarget_during_transaction_is_rejected(
    tmp_path: Path, monkeypatch, operation: str,
):
    ledger, previous = _fixture(tmp_path)
    original_path = ledger.path
    alternate = tmp_path / "other.sqlite"
    SyntheticCancellationLedger(alternate)
    original = module._replay

    def retarget(conn):
        prefixes = original(conn)
        ledger.path = alternate
        return prefixes

    monkeypatch.setattr(module, "_replay", retarget)
    with pytest.raises(SyntheticCancellationRejected, match="source path changed"):
        if operation == "read":
            ledger.read_witness(retained=previous)
        elif operation == "state":
            ledger.review_state(_id("first"), retained=previous)
        else:
            ledger.cancel_synthetic(_id("second"), at_ms=11, retained=previous)
    monkeypatch.setattr(module, "_replay", original)
    assert SyntheticCancellationLedger(original_path).read_witness().event_count == 1
    assert SyntheticCancellationLedger(alternate).read_witness().event_count == 0


@pytest.mark.parametrize("operation", ["read", "state", "append"])
def test_changed_ledger_source_is_refused_before_open(
    tmp_path: Path, operation: str,
):
    ledger, _previous = _fixture(tmp_path)
    alternate = tmp_path / "other.sqlite"
    SyntheticCancellationLedger(alternate)
    ledger.path = alternate
    with pytest.raises(SyntheticCancellationRejected, match="source path changed"):
        if operation == "read":
            ledger.read_witness()
        elif operation == "state":
            ledger.review_state(_id("first"))
        else:
            ledger.cancel_synthetic(_id("second"), at_ms=11)
    assert SyntheticCancellationLedger(alternate).read_witness().event_count == 0


def test_unchanged_history_accepts_unrelated_later_cancellation(tmp_path: Path):
    ledger, first = _fixture(tmp_path)
    second = ledger.cancel_synthetic(_id("second"), at_ms=11, retained=first)
    assert second.event_count == 2
    assert ledger.read_witness(retained=first) == second
    state = ledger.review_state(_id("third"), retained=first)
    assert state.cancelled is False
    assert state.dispatch_authorized is False
    assert state.human_consent_verified is False
    assert state.automatic_replay_authorized is False
