"""Synthetic restart witness metadata must not reach substituted digest callbacks.

No real tool, authenticated custody, clock trust, or startup authorization.
"""
from __future__ import annotations

import pytest

import ark.disconnected_restart_witness_bundle as bundle
from ark.agency.disconnected_due_reservation import DisconnectedDueReservations
from ark.memory.disconnected_witness_ledger import (
    DisconnectedMemoryWitnessLedger,
    genesis_memory_ledger_witness,
)
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger


def _fixture(tmp_path):
    memory = DisconnectedMemoryWitnessLedger(tmp_path / "memory.sqlite", create=True)
    context = DisconnectedContextReplayLedger(tmp_path / "context.sqlite", create=True)
    due = DisconnectedDueReservations(tmp_path / "due.sqlite")
    retained = (genesis_memory_ledger_witness(), context.witness(), due.witness())
    return (memory, context, due), retained


def _review(stores, witnesses):
    return bundle.review_disconnected_restart_witnesses(
        stores[0], witnesses[0], stores[1], witnesses[1],
        stores[2], witnesses[2],
    )


@pytest.mark.parametrize("helper", ("sha256", "json_dumps"))
def test_digest_substitution_rejected_before_local_store_read(
    tmp_path, monkeypatch, helper,
):
    stores, retained = _fixture(tmp_path)
    reads = []
    monkeypatch.setattr(
        stores[0], "inspect",
        lambda **_kwargs: reads.append("memory") or retained[0],
    )
    intercepted = []

    def intercept(*_args, **_kwargs):
        intercepted.append("called")
        raise AssertionError("private restart metadata leaked to helper")

    with monkeypatch.context() as patch:
        if helper == "sha256":
            patch.setattr(bundle.hashlib, "sha256", intercept)
        else:
            patch.setattr(bundle.json, "dumps", intercept)
        with pytest.raises(
            bundle.OfflineRestartWitnessRejected,
            match="authority definition changed",
        ):
            _review(stores, retained)
    assert not reads and not intercepted


@pytest.mark.parametrize(
    ("name", "replacement"),
    (("_DOMAIN", b"invalid"), ("_REPORT", object)),
)
def test_retargeted_domain_or_report_type_rejected_before_read(
    tmp_path, monkeypatch, name, replacement,
):
    stores, retained = _fixture(tmp_path)
    reads = []

    def unexpected(**_kwargs):
        reads.append("read")
        raise AssertionError("no local store read permitted")

    monkeypatch.setattr(stores[0], "inspect", unexpected)
    with monkeypatch.context() as patch:
        patch.setattr(bundle, name, replacement)
        with pytest.raises(
            bundle.OfflineRestartWitnessRejected,
            match="authority definition changed",
        ):
            _review(stores, retained)
    assert not reads


@pytest.mark.parametrize(
    "field", ("__init__", "fingerprint", "dispatch_authorized"),
)
def test_report_constructor_field_or_denial_substitution_denied_before_read(
    tmp_path, monkeypatch, field,
):
    stores, retained = _fixture(tmp_path)
    reads = []

    def unexpected(**_kwargs):
        reads.append("read")
        raise AssertionError("no local store read permitted")

    monkeypatch.setattr(stores[0], "inspect", unexpected)
    with monkeypatch.context() as patch:
        if field == "dispatch_authorized":
            patch.setattr(
                bundle.OfflineRestartWitnessReport,
                field, property(lambda _self: False),
            )
        else:
            patch.setattr(
                bundle.OfflineRestartWitnessReport,
                field, lambda *_args, **_kwargs: None,
            )
        with pytest.raises(
            bundle.OfflineRestartWitnessRejected,
            match="authority definition changed",
        ):
            _review(stores, retained)
    assert not reads


def test_untouched_restart_report_remains_denial_only(tmp_path):
    stores, retained = _fixture(tmp_path)
    result = _review(stores, retained)
    assert (result.memory_epochs, result.context_requests, result.due_occurrences) == (
        0, 0, 0,
    )
    assert len(result.fingerprint) == 64
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.personal_context_use_authorized is False
    assert result.trusted_clock_verified is False
