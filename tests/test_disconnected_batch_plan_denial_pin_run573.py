"""Detached batch plan denial callbacks are original and inert, before parsing.

Synthetic data only; this plan and its digest grant no tool execution, write,
trusted-clock, owner-consent or automatic replay authority.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_batch_plan as batch

_REQUEST = "req_" + "b" * 32


def _build():
    step = batch.DisconnectedBatchStep(
        "step_0000000000000001", "math.sum", '{"values":[1,2,3]}',
    )
    return batch.build_disconnected_batch_plan(_REQUEST, (step,))


@pytest.mark.parametrize("flag", (
    "dispatch_authorized", "write_authorized",
    "replay_authorized", "execution_proven",
))
@pytest.mark.parametrize("entrypoint", ("build", "verify"))
def test_rebound_false_only_denial_is_rejected_before_parse(
    monkeypatch, flag, entrypoint,
):
    original_plan = _build()
    called = []

    def injected_false(_self):
        called.append("denial")
        return False

    def forbidden_parse(*_args, **_kwargs):
        called.append("parse")
        raise AssertionError("untrusted parser should not be reached")

    monkeypatch.setattr(batch.DisconnectedBatchPlan, flag, property(injected_false))
    monkeypatch.setattr(batch, "_make_payload", forbidden_parse)

    with pytest.raises(
        batch.DisconnectedBatchRejected, match="authority definition changed",
    ):
        if entrypoint == "build":
            _build()
        else:
            batch.verify_disconnected_batch_plan(
                original_plan, retained_digest=original_plan.plan_digest,
            )
    assert not called


@pytest.mark.parametrize("entrypoint", ("build", "verify"))
def test_rebound_plan_class_denied_before_parsing(monkeypatch, entrypoint):
    original_plan = _build()
    called = []

    class Counterfeit:
        def __init__(self, *_args, **_kwargs):
            called.append("constructor")

    def forbidden_parse(*_args, **_kwargs):
        called.append("parse")
        raise AssertionError("parser must not be invoked")

    monkeypatch.setattr(batch, "DisconnectedBatchPlan", Counterfeit)
    monkeypatch.setattr(batch, "_make_payload", forbidden_parse)
    with pytest.raises(
        batch.DisconnectedBatchRejected, match="authority definition changed",
    ):
        if entrypoint == "build":
            _build()
        else:
            batch.verify_disconnected_batch_plan(
                original_plan, retained_digest=original_plan.plan_digest,
            )
    assert called == []


def test_original_detached_plan_retains_no_action_or_replay_authority():
    original = _build()
    batch.verify_disconnected_batch_plan(
        original, retained_digest=original.plan_digest,
    )
    assert original.dispatch_authorized is False
    assert original.write_authorized is False
    assert original.replay_authorized is False
    assert original.execution_proven is False
