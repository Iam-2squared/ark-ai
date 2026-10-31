"""Local READ fixture -> request binding -> SQLite journal integration."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_read_receipt_bridge as bridge
from ark.agency.disconnected_fixture_binding import (
    DisconnectedFixtureBinding,
    bind_disconnected_fixture_result,
)
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadReceipt,
    genesis_witness,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)

STEP = "step_" + "a" * 16


def _case(suffix="a", args='{"values":[1,2]}'):
    request = DisconnectedToolRequest("req_" + suffix * 32, "math.sum", args)
    result = execute_disconnected_fixture_tool(request)
    return request, result, bind_disconnected_fixture_result(request, result)


def test_exact_fixture_is_mapped_to_v1_journal_without_new_authority():
    request, result, bound = _case()
    receipt = bridge.prepare_disconnected_read_receipt(
        STEP, request, result, bound,
    )
    assert type(receipt) is ReadReceipt
    assert receipt == ReadReceipt(
        request.request_id, STEP, request.operation,
        result.input_digest, result.result_digest,
    )
    assert bound.request_bound_digest != result.result_digest
    assert bound.dispatch_authorized is False


def test_full_offline_journal_restart_and_external_witness(tmp_path):
    path = tmp_path / "read-fixtures.sqlite"
    request, result, bound = _case()
    second_request, second_result, second_bound = _case("b")
    with DisconnectedReadJournal.create(path) as journal:
        first = bridge.append_disconnected_fixture_read(
            journal, genesis_witness(), STEP, request, result, bound,
        )
        second = bridge.append_disconnected_fixture_read(
            journal, first, STEP, second_request, second_result, second_bound,
        )
        assert second.count == 2
        assert second.dispatch_authorized is False
        assert second.effect_proven is False
        assert second.replay_authorized is False
        assert second.independent_custody_proven is False
    with DisconnectedReadJournal.open(path) as journal:
        assert journal.verify(second) == second
        with pytest.raises(ReadJournalRejected, match="external witness"):
            journal.verify(first)


def test_duplicate_is_not_replayed_or_retried(tmp_path):
    request, result, bound = _case()
    with DisconnectedReadJournal.create(tmp_path / "read.sqlite") as journal:
        first = bridge.append_disconnected_fixture_read(
            journal, genesis_witness(), STEP, request, result, bound,
        )
        with pytest.raises(ReadJournalRejected, match="stale"):
            bridge.append_disconnected_fixture_read(
                journal, genesis_witness(), "step_" + "b" * 16,
                request, result, bound,
            )
        with pytest.raises(ReadJournalRejected, match="duplicate"):
            bridge.append_disconnected_fixture_read(
                journal, first, STEP, request, result, bound,
            )
        assert journal.verify(first) == first


@pytest.mark.parametrize("bad", [
    "step_wrong", "step_" + "A" * 16, "step_" + "b" * 17,
    True, 0, None,
])
def test_invalid_step_is_rejected_before_any_journal_append(bad):
    request, result, bound = _case()
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="exact"):
        bridge.prepare_disconnected_read_receipt(bad, request, result, bound)


def test_cross_request_binding_mismatch_denied():
    request, result, _ = _case()
    _, _, other = _case("b")
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="binding"):
        bridge.prepare_disconnected_read_receipt(STEP, request, result, other)


def test_stale_result_must_not_be_silently_recomputed():
    request, result, bound = _case()
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="rebinding"):
        bridge.prepare_disconnected_read_receipt(
            STEP, request, replace(result, result_digest="f" * 64), bound,
        )


@pytest.mark.parametrize("field", [
    "dispatch_authorized", "external_outcome_verified",
    "automatic_replay_authorized",
])
def test_forged_receipt_binding_execution_grant_denied(monkeypatch, field):
    request, result, bound = _case()
    monkeypatch.setattr(
        DisconnectedFixtureBinding, field, property(lambda _: True),
    )
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="authority"):
        bridge.prepare_disconnected_read_receipt(STEP, request, result, bound)


def test_equal_value_binding_replacement_during_callback_denied(monkeypatch):
    request, result, bound = _case()
    old = bridge.bind_disconnected_fixture_result

    def tamper(req, res):
        replaced = "".join((
            bound.request_bound_digest[:32], bound.request_bound_digest[32:],
        ))
        assert replaced == bound.request_bound_digest
        assert replaced is not bound.request_bound_digest
        object.__setattr__(bound, "request_bound_digest", replaced)
        return old(req, res)

    monkeypatch.setattr(bridge, "bind_disconnected_fixture_result", tamper)
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="changed"):
        bridge.prepare_disconnected_read_receipt(STEP, request, result, bound)


def test_other_journal_or_binding_types_denied():
    request, result, bound = _case()
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="exact"):
        bridge.prepare_disconnected_read_receipt(STEP, request, result, object())
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="journal"):
        bridge.append_disconnected_fixture_read(
            object(), genesis_witness(), STEP, request, result, bound,
        )
