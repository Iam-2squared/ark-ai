"""Synthetic READ bridge refuses executable class substitutions pre-access.

One subprocess per mutation protects CPython inherited type slots and ensures
the hostile callback was never invoked. No real ToolBackend is involved.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_SCRIPT = """
import sys

import ark.agency.disconnected_read_receipt_bridge as bridge
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_toolbox import execute_disconnected_fixture_tool

request = bridge.DisconnectedToolRequest(
    "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
)
result = execute_disconnected_fixture_tool(request)
binding = bind_disconnected_fixture_result(request, result)
klass = {
    "request": bridge.DisconnectedToolRequest,
    "result": bridge.DisconnectedToolResult,
    "binding": bridge.DisconnectedFixtureBinding,
    "receipt": bridge.ReadReceipt,
}[sys.argv[1]]
name = sys.argv[2]
called = []

def hostile(*args, **kwargs):
    called.append(name)
    raise AssertionError("forbidden executable carrier slot invoked")

if name == "__new__":
    setattr(klass, name, staticmethod(hostile))
elif name.startswith("__"):
    setattr(klass, name, hostile)
else:
    setattr(klass, name, property(hostile))

try:
    bridge.prepare_disconnected_read_receipt(
        "step_" + "a" * 16, request, result, binding,
    )
except bridge.DisconnectedReadBridgeRejected as exc:
    assert "fixture rebinding failed" in str(exc), str(exc)
else:
    raise AssertionError("untrusted bridge carrier accepted")
assert called == [], called
"""


@pytest.mark.parametrize(("carrier", "slot"), [
    ("request", "canonical_args_json"),
    ("request", "__getattribute__"),
    ("request", "__new__"),
    ("result", "canonical_result_json"),
    ("result", "dispatch_authorized"),
    ("result", "__getattribute__"),
    ("binding", "request_bound_digest"),
    ("binding", "external_outcome_verified"),
    ("binding", "__getattribute__"),
    ("binding", "__init__"),
    ("binding", "__new__"),
    ("receipt", "request_id"),
    ("receipt", "__getattribute__"),
    ("receipt", "__init__"),
    ("receipt", "__new__"),
])
def test_preinstalled_executable_carrier_is_never_called(carrier, slot):
    completed = subprocess.run(
        [sys.executable, "-c", _SCRIPT, carrier, slot],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_original_receipt_remains_hash_only_and_non_authorizing():
    from ark.agency.disconnected_fixture_binding import (
        bind_disconnected_fixture_result,
    )
    from ark.agency.disconnected_read_receipt_bridge import (
        DisconnectedToolRequest,
        prepare_disconnected_read_receipt,
    )
    from ark.agency.disconnected_toolbox import execute_disconnected_fixture_tool

    request = DisconnectedToolRequest(
        "req_" + "b" * 32, "math.sum", '{"values":[2,4]}',
    )
    result = execute_disconnected_fixture_tool(request)
    bound = bind_disconnected_fixture_result(request, result)
    row = prepare_disconnected_read_receipt(
        "step_" + "c" * 16, request, result, bound,
    )
    assert row.request_id == request.request_id
    assert row.operation == "math.sum"
    assert row.result_digest == result.result_digest
    assert row.input_digest == result.input_digest
    assert not hasattr(row, "dispatch_authorized")
