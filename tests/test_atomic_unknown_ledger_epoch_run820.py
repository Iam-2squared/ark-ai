"""Fail-closed ledger instance/epoch custody for inert COMMIT-UNKNOWN review."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.agency.disconnected_atomic_unknown_outcome_review as review
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _claim() -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)


def _ledger(tmp_path: Path) -> DisconnectedAtomicPreactionLedger:
    return DisconnectedAtomicPreactionLedger.create(tmp_path / "audit.sqlite")


def test_unmodified_ledger_remains_inert_and_readable(tmp_path: Path) -> None:
    result = review.review_atomic_unknown_outcome(
        _ledger(tmp_path), genesis_atomic_preaction_witness(), _claim(),
    )
    assert result.local_state == "UNCHANGED"
    assert result.locally_present is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_verified is False
    assert result.manual_review_required is True


def test_instance_shadow_open_is_refused_before_execution(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    executed = []

    def forged_open(*, read_only: bool):
        executed.append(read_only)
        raise AssertionError("untrusted instance method must never execute")

    ledger._open = forged_open
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="ledger instance changed",
    ):
        review.review_atomic_unknown_outcome(
            ledger, genesis_atomic_preaction_witness(), _claim(),
        )
    assert executed == []


def test_unexpected_ledger_instance_state_is_refused(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    ledger.untrusted_callback = object()
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="ledger instance changed",
    ):
        review.review_atomic_unknown_outcome(
            ledger, genesis_atomic_preaction_witness(), _claim(),
        )


def test_connector_rebind_refused_before_instance_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = _ledger(tmp_path)
    original_connect = review.sqlite3.connect
    calls = []

    def rebinding_connect(*args, **kwargs):
        calls.append(True)
        ledger._path = tmp_path / "different.sqlite"
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(review.sqlite3, "connect", rebinding_connect)
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="protocol changed",
    ):
        review.review_atomic_unknown_outcome(
            ledger, genesis_atomic_preaction_witness(), _claim(),
        )
    assert calls == []


def test_connector_rebind_refused_before_shadow_installation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = _ledger(tmp_path)
    original_connect = review.sqlite3.connect
    calls = []

    def rebinding_connect(*args, **kwargs):
        calls.append(True)
        ledger._open = lambda *, read_only: pytest.fail("forged late open")
        return original_connect(*args, **kwargs)

    monkeypatch.setattr(review.sqlite3, "connect", rebinding_connect)
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="protocol changed",
    ):
        review.review_atomic_unknown_outcome(
            ledger, genesis_atomic_preaction_witness(), _claim(),
        )
    assert calls == []


def test_class_attribute_interception_denied_without_invocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = _ledger(tmp_path)
    called = []

    def hijack(self, name):
        called.append(name)
        raise AssertionError("untrusted class getter must not run")

    monkeypatch.setattr(DisconnectedAtomicPreactionLedger, "__getattribute__", hijack)
    with pytest.raises(
        review.AtomicUnknownOutcomeRejected, match="protocol changed",
    ):
        review.review_atomic_unknown_outcome(
            ledger, genesis_atomic_preaction_witness(), _claim(),
        )
    assert called == []
