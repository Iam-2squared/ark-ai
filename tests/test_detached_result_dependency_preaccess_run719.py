"""Detached READ evidence must not reach substituted JSON/hash callbacks."""

from __future__ import annotations

import hashlib

import pytest

from ark.agency import disconnected_result_budget as result_budget

_REQUEST = "req_" + "d" * 32
_STEP = "step_" + "e" * 16
_RAW = '{"private_fixture":"offline-only"}'


@pytest.mark.parametrize("dependency", (
    "sha256", "dumps", "loads", "_pairs_unique", "_int64", "_no_float",
))
def test_detached_result_dependency_replaced_before_payload_access(monkeypatch, dependency):
    row = result_budget.DetachedReadResult(
        _STEP, "math.sum", _RAW, hashlib.sha256(_RAW.encode("utf-8")).hexdigest(),
    )
    calls: list[tuple[object, ...]] = []

    def hostile(*args, **_kwargs):
        calls.append(args)
        raise AssertionError("substituted callback accessed fixture payload")

    module = (
        result_budget.hashlib if dependency == "sha256" else
        result_budget.json if dependency in ("dumps", "loads") else
        result_budget
    )
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, hostile)
        with pytest.raises(
            result_budget.DisconnectedResultsRejected,
            match="sealed READ result carrier or authority descriptor changed",
        ):
            result_budget.seal_detached_read_results(
                _REQUEST, ((_STEP, "math.sum"),), (row,),
            )
    assert calls == []
    receipt = result_budget.seal_detached_read_results(
        _REQUEST, ((_STEP, "math.sum"),), (row,),
    )
    assert receipt.result_count == 1
    assert receipt.dispatch_authorized is False
    assert receipt.external_result_verified is False
