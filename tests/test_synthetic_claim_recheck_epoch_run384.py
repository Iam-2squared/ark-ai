"""Disconnected claim-source review pins saved provenance and source epochs."""

import hashlib
from pathlib import Path

import pytest

import ark.agency.synthetic_claim_occurrence_recheck_review as module
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_approval_cancellation_review import SyntheticCancellationLedger
from ark.agency.synthetic_approval_claim_review import make_synthetic_approval_claim
from ark.agency.synthetic_claim_occurrence_link_review import (
    SyntheticClaimOccurrenceLinkStore,
)
from ark.agency.synthetic_occurrence_continuity_review import (
    read_synthetic_ledger_witness,
)


class DisconnectedBackend:
    def execute(self, call):
        raise AssertionError("offline synthetic review must never execute")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _state(tmp_path: Path, *, populated: bool = True):
    registry = ToolRegistry((
        ToolRegistration(
            "fixture", "write", Effect.WRITE, "offline", DisconnectedBackend(),
        ),
    ))
    call = ToolCall("fixture", "write", "offline-request", {"secret": "NOT-USED"})
    source_path = tmp_path / "reservations.sqlite"
    reservations = SyntheticOccurrenceStore(source_path)
    veto = SyntheticCancellationLedger(tmp_path / "veto.sqlite")
    links = SyntheticClaimOccurrenceLinkStore(tmp_path / "links.sqlite")
    if populated:
        claim = make_synthetic_approval_claim(
            registry, call, issuer_digest=_digest("issuer"),
            subject_digest=_digest("subject"),
            purpose_digest=_digest("purpose"),
            recipient_digest=_digest("recipient"),
            nonce_digest=_digest("nonce"), issued_at_ms=10, expires_at_ms=100,
        )
        reserved = reservations.reserve_synthetic(
            registry, call,
            OneShotAuthorization("offline-token", call.request_id, 500),
            occurrence_id="occ_" + _digest("occurrence"), now_ms=11,
        )
        links.link_synthetic(
            claim, veto, registry, call, reservations, reserved, now_ms=20,
        )
    return links, source_path


def _read(state, **kwargs):
    links, path = state
    return module.review_synthetic_claim_occurrence_sources(
        links, path, **kwargs,
    )


def test_reflected_link_source_retarget_rejected_even_for_identical_empty_db(
    tmp_path: Path, monkeypatch,
):
    state = _state(tmp_path, populated=False)
    replacement = SyntheticClaimOccurrenceLinkStore(tmp_path / "other.sqlite")
    original = module.read_synthetic_ledger_witness

    def retarget_after_first_read(path):
        result = original(path)
        state[0].path = replacement.path
        return result

    monkeypatch.setattr(module, "read_synthetic_ledger_witness", retarget_after_first_read)
    with pytest.raises(module.SyntheticClaimSourceRejected, match="source changed"):
        _read(state)


def test_reflected_retained_link_witness_replacement_rejected(
    tmp_path: Path, monkeypatch,
):
    state = _state(tmp_path)
    retained = state[0].read_witness()
    genesis = SyntheticClaimOccurrenceLinkStore(
        tmp_path / "empty_links.sqlite",
    ).read_witness()
    original = module.read_synthetic_ledger_witness

    def swap_retained_after_first_read(path):
        result = original(path)
        for field in ("event_count", "tail_hash", "last_linked_at_ms"):
            object.__setattr__(retained, field, getattr(genesis, field))
        return result

    monkeypatch.setattr(module, "read_synthetic_ledger_witness", swap_retained_after_first_read)
    with pytest.raises(module.SyntheticClaimSourceRejected, match="retained witness"):
        _read(state, retained_links=retained)


def test_reflected_retained_reservation_witness_replacement_rejected(
    tmp_path: Path, monkeypatch,
):
    state = _state(tmp_path)
    retained = read_synthetic_ledger_witness(state[1])
    empty_path = tmp_path / "empty_reservations.sqlite"
    SyntheticOccurrenceStore(empty_path)
    genesis = read_synthetic_ledger_witness(empty_path)
    original = module.read_synthetic_ledger_witness

    def swap_retained_after_first_read(path):
        result = original(path)
        object.__setattr__(retained, "row_hashes", genesis.row_hashes)
        object.__setattr__(retained, "digest", genesis.digest)
        return result

    monkeypatch.setattr(module, "read_synthetic_ledger_witness", swap_retained_after_first_read)
    with pytest.raises(module.SyntheticClaimSourceRejected, match="retained witness"):
        _read(state, retained_reservations=retained)


def test_untouched_retained_witnesses_never_authorize_effects(tmp_path: Path):
    state = _state(tmp_path)
    result = _read(
        state, retained_links=state[0].read_witness(),
        retained_reservations=read_synthetic_ledger_witness(state[1]),
    )
    assert result.link_event_count == 1
    assert result.human_consent_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert "NOT-USED" not in repr(result)
