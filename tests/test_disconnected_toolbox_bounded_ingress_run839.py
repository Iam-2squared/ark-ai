"""Disconnected mock toolbox rejects unbounded IDs before fixture parsing.

No real ToolBackend, network, effect, consent, trusted clock or replay.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.disconnected_toolbox import (
    DisconnectedToolRejected,
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)

ID = "req_" + "a" * 32


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("request_id", "req_" + "a" * 100_000),
        ("request_id", "req_" + "\ud800" * 100),
        ("operation", "math.sum" + "X" * 100_000),
        ("operation", "text.stats" + "\ud800" * 100),
    ],
)
def test_unbounded_identity_and_operation_denied(field, bad):
    request = DisconnectedToolRequest(ID, "math.sum", '{"values":[1,2]}')
    with pytest.raises(DisconnectedToolRejected, match="unbounded fixture request"):
        execute_disconnected_fixture_tool(replace(request, **{field: bad}))


@pytest.mark.parametrize("operation,raw", (
    ("math.sum", '{"values":[1,2]}'),
    ("text.find", '{"needle":"a","text":"bat"}'),
    ("json.inspect", '{"json":"true"}'),
))
def test_valid_bounded_inmemory_tool_remains_denial_only(operation, raw):
    report = execute_disconnected_fixture_tool(
        DisconnectedToolRequest(ID, operation, raw),
    )
    assert report.operation == operation
    assert report.dispatch_authorized is False
    assert report.external_outcome_known is False
    assert report.automatic_replay_authorized is False
