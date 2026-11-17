"""Run946: disconnected tools do not echo synthetic private payloads on denial.

These are memory-only fixtures, never external ToolBackend invocations.
"""

from __future__ import annotations

import json

import pytest

from ark.agency.disconnected_toolbox import (
    DisconnectedToolRejected,
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)

_SECRET = "ARK_PRIVATE_SENTINEL_946"
_REQUEST_ID = "req_" + "c" * 32


@pytest.mark.parametrize(("operation", "args"), (
    ("math.sum", {"values": [2**63, 1], "private": _SECRET}),
    ("math.sum", {"values": [2**63 - 1, 1], "private": _SECRET}),
    ("text.stats", {"text": _SECRET, "unexpected": True}),
    ("text.find", {"text": _SECRET, "needle": ""}),
    ("text.find", {"text": _SECRET, "needle": "\ud800"}),
    ("json.inspect", {"json": '{"private":"' + _SECRET + '","private":"x"}'}),
    ("json.inspect", {"json": '{"private": "' + _SECRET + '"}'}),
    ("unsafe.shell", {"text": _SECRET}),
))
def test_rejected_synthetic_private_args_are_not_echoed(
    operation: str, args: dict[str, object],
) -> None:
    raw = json.dumps(args, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    assert _SECRET in raw
    request = DisconnectedToolRequest(_REQUEST_ID, operation, raw)
    assert _SECRET not in repr(request)
    with pytest.raises(DisconnectedToolRejected) as error:
        execute_disconnected_fixture_tool(request)
    assert _SECRET not in str(error.value)
    assert _SECRET not in repr(error.value)
    assert _SECRET not in repr(request)


@pytest.mark.parametrize(("operation", "args"), (
    ("math.sum", {"values": [5, -2, 7]}),
    ("text.stats", {"text": _SECRET + "\nsynthetic"}),
    ("text.find", {"text": _SECRET, "needle": "SENTINEL"}),
    ("json.inspect", {"json": '{"private":"' + _SECRET + '"}'}),
))
def test_success_receipt_is_digest_only_and_cannot_authorize_dispatch(
    operation: str, args: dict[str, object],
) -> None:
    raw = json.dumps(args, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    result = execute_disconnected_fixture_tool(
        DisconnectedToolRequest(_REQUEST_ID, operation, raw),
    )
    assert _SECRET not in repr(result)
    assert len(result.input_digest) == 64
    assert len(result.result_digest) == 64
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    # Only bounded derived numbers and kind labels are ever returned.
    assert _SECRET not in result.canonical_result_json
