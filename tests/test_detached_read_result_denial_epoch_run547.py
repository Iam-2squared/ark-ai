"""Run547: content-minimized READ results can never confer execution authority."""

from __future__ import annotations

import hashlib

import pytest

from ark.agency import disconnected_result_budget as mod

REQUEST = "req_" + "c" * 32
STEP = "step_" + "d" * 16
RAW = '{"answer":42}'


def _seal():
    receipt = mod.DetachedReadResult(
        STEP, "math.sum", RAW, hashlib.sha256(RAW.encode("utf-8")).hexdigest(),
    )
    return mod.seal_detached_read_results(
        REQUEST, ((STEP, "math.sum"),), (receipt,),
    )


def test_complete_local_result_remains_non_authorizing():
    result = _seal()
    assert result.result_count == 1
    assert result.result_bytes == len(RAW)
    assert result.external_result_verified is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("flag", (
    "external_result_verified",
    "dispatch_authorized",
    "automatic_replay_authorized",
))
def test_forged_true_authority_descriptor_is_rejected(monkeypatch, flag):
    monkeypatch.setattr(
        mod.CompleteDetachedReadResults, flag, property(lambda _self: True),
    )
    with pytest.raises(mod.DisconnectedResultsRejected, match="descriptor changed"):
        _seal()


@pytest.mark.parametrize("flag", (
    "external_result_verified",
    "dispatch_authorized",
    "automatic_replay_authorized",
))
def test_replaced_false_authority_descriptor_is_not_accepted(monkeypatch, flag):
    monkeypatch.setattr(
        mod.CompleteDetachedReadResults, flag, property(lambda _self: False),
    )
    with pytest.raises(mod.DisconnectedResultsRejected, match="descriptor changed"):
        _seal()


def test_mutating_false_authority_callback_fails_closed(monkeypatch):
    def malicious(self):
        object.__setattr__(self, "result_bytes", self.result_bytes + 1)
        return False

    monkeypatch.setattr(
        mod.CompleteDetachedReadResults,
        "automatic_replay_authorized",
        property(malicious),
    )
    with pytest.raises(mod.DisconnectedResultsRejected):
        _seal()
