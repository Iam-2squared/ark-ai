"""Run943: deterministic disconnected READ fixtures survive a cold interpreter.

All requests are synthetic, bounded, and in memory. No permission, external
ToolBackend, authenticated outcome, clock, or automatic replay is provided.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)

_REQUEST = "req_" + "b" * 32

_CHILD = """
import json
import sys
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest, execute_disconnected_fixture_tool,
)

request = DisconnectedToolRequest(sys.argv[1], sys.argv[2], sys.argv[3])
result = execute_disconnected_fixture_tool(request)
print(json.dumps({
    "request_id": result.request_id,
    "operation": result.operation,
    "input_digest": result.input_digest,
    "result_digest": result.result_digest,
    "denials": [
        result.dispatch_authorized,
        result.automatic_replay_authorized,
        result.external_outcome_known,
    ],
}, sort_keys=True))
"""


@pytest.mark.parametrize(("operation", "args"), (
    ("math.sum", {"values": [12, -7, 5]}),
    ("text.stats", {"text": "two words\nthird"}),
    ("text.find", {"text": "zabcabc", "needle": "abc"}),
    ("json.inspect", {"json": '[1,2,null]'}),
))
def test_cold_process_mock_result_is_stable_and_has_no_execution_authority(operation, args):
    raw = json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    request = DisconnectedToolRequest(_REQUEST, operation, raw)
    local = execute_disconnected_fixture_tool(request)
    remote = subprocess.run(
        [sys.executable, "-c", _CHILD, _REQUEST, operation, raw],
        capture_output=True, text=True, check=True, timeout=20,
    )
    observed = json.loads(remote.stdout)
    assert observed == {
        "request_id": local.request_id,
        "operation": local.operation,
        "input_digest": local.input_digest,
        "result_digest": local.result_digest,
        "denials": [False, False, False],
    }
    assert raw not in remote.stdout
    assert local.dispatch_authorized is False
    assert local.automatic_replay_authorized is False
    assert local.external_outcome_known is False
