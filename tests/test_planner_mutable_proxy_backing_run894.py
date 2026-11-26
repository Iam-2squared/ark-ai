"""PlanGraph must re-admit a reflected proxy's mutable backing on every read.

These are disconnected fault fixtures, not a way to mutate canonical ToolCall
or a proof of independently trusted input provenance.
"""

from types import MappingProxyType

import pytest

from ark.agency import contracts
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


class _NoCallbacks:
    def __getattribute__(self, _name):
        raise AssertionError("untrusted backing value callback was executed")


def _graph_with_reflected_backing():
    # A public ToolCall freezes arguments. Only test-only reflection can
    # install a proxy backed by a separately retained mutable dictionary.
    call = ToolCall("offline.inspect", "fixture.read", "synthetic", {"safe": 1})
    backing = {"safe": 1}
    object.__setattr__(call, "arguments", MappingProxyType(backing))
    graph = PlanGraph((PlanStep("step", call),))
    return graph, backing


@pytest.mark.parametrize("operation", ("topology", "ready", "statuses", "transition"))
def test_mutated_backing_is_refused_before_toolcall_json_hash(
    monkeypatch, operation,
):
    graph, backing = _graph_with_reflected_backing()
    backing["safe"] = _NoCallbacks()
    invoked = []

    def forbidden_hash(_value):
        invoked.append("hash")
        raise AssertionError("hostile JSON reached the ToolCall serializer")

    monkeypatch.setattr(contracts, "_canonical_json", forbidden_hash)
    with pytest.raises(PlanConflictError, match="carrier changed"):
        if operation == "topology":
            graph.topology_digest()
        elif operation == "ready":
            graph.ready_steps()
        elif operation == "statuses":
            graph.statuses()
        else:
            graph.transition("step", StepState.RUNNING, expected_revision=0)
    assert invoked == []
    assert graph._status["step"].revision == 0


@pytest.mark.parametrize(
    "replacement",
    (
        float("nan"),
        1 << 20_000,
        {"nested": "not a frozen JSON mapping"},
        "\ud800",
    ),
    ids=("nonfinite", "huge-int", "foreign-mapping", "invalid-unicode"),
)
def test_invalid_mutated_backing_is_denied_without_digest(replacement, monkeypatch):
    graph, backing = _graph_with_reflected_backing()
    backing["safe"] = replacement

    def forbidden_hash(_value):
        raise AssertionError("invalid reflected JSON reached canonical hashing")

    monkeypatch.setattr(contracts, "_canonical_json", forbidden_hash)
    with pytest.raises(PlanConflictError, match="carrier changed"):
        graph.topology_digest()


def test_bounded_exact_backing_value_change_is_still_detected_by_request_identity():
    graph, backing = _graph_with_reflected_backing()
    original_topology = graph.topology_digest()
    assert original_topology.startswith("plan_")
    backing["safe"] = 2
    with pytest.raises(PlanConflictError, match="action identity changed"):
        graph.topology_digest()
    assert graph._status["step"].revision == 0
