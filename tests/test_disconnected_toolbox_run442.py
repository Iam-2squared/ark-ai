"""Disconnected READ-only toolbox negative regressions."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark.agency import disconnected_toolbox as mod


def request(operation: str, raw: str) -> mod.DisconnectedToolRequest:
    return mod.DisconnectedToolRequest("req_" + "a" * 32, operation, raw)


@pytest.mark.parametrize("operation,raw,expected", [
    ("math.sum", '{"values":[1,2,-3]}', {"count": 3, "sum": 0}),
    ("math.sum", '{"values":[9223372036854775807]}', {
        "count": 1, "sum": 9223372036854775807,
    }),
    ("math.sum", '{"values":[-9223372036854775808]}', {
        "count": 1, "sum": -9223372036854775808,
    }),
    ("text.stats", '{"text":"hello world\\nsecond"}', {
        "characters": 18, "lines": 2, "words": 3,
    }),
    ("text.stats", '{"text":""}', {
        "characters": 0, "lines": 0, "words": 0,
    }),
    ("text.find", '{"needle":"abc","text":"xabcabc"}', {"index": 1}),
    ("text.find", '{"needle":"not found","text":"hello"}', {"index": -1}),
    ("json.inspect", '{"json":"{\\"a\\":1}"}', {
        "kind": "object", "items": 1,
    }),
    ("json.inspect", '{"json":"[1,2,null]"}', {"kind": "array", "items": 3}),
    ("json.inspect", '{"json":"true"}', {"kind": "scalar", "items": 1}),
])
def test_deterministic_memory_only_results(operation, raw, expected):
    item = request(operation, raw)
    first = mod.execute_disconnected_fixture_tool(item)
    second = mod.execute_disconnected_fixture_tool(item)
    assert first == second
    assert mod._json(first.canonical_result_json) == expected
    assert len(first.input_digest) == 64
    assert len(first.result_digest) == 64
    assert not first.dispatch_authorized
    assert not first.automatic_replay_authorized
    assert not first.external_outcome_known


@pytest.mark.parametrize("operation,raw", [
    ("unsafe.shell", '{"cmd":"powershell"}'),
    ("math.sum", '{"values":[]}'),
    ("math.sum", '{"values":[true]}'),
    ("math.sum", '{"values":[1.0]}'),
    ("math.sum", '{"values":[9223372036854775807,1]}'),
    ("math.sum", '{"values":[-9223372036854775808,-1]}'),
    ("math.sum", '{"values":[9223372036854775808]}'),
    ("math.sum", '{"values":[-9223372036854775809]}'),
    ("text.find", '{"needle":"","text":"abc"}'),
    ("text.find", '{"needle":"a"}'),
    ("text.stats", '{"text":"test","extra":1}'),
    ("text.stats", '{"text":3}'),
    ("text.stats", '{"text":"\\ud800"}'),
    ("math.sum", '{"values":[1],"values":[2]}'),
    ("math.sum", '{"values": [1]}'),
    ("math.sum", '{"values":[1]} '),
    ("json.inspect", '{"json":"{\\"x\\":1,\\"x\\":2}"}'),
    ("json.inspect", '{"json":"{\\"x\\": 1}"}'),
    ("json.inspect", '{"json":"[1.5]"}'),
    ("json.inspect", '{"json":"NaN"}'),
    ("json.inspect", '{"json":"[9223372036854775808]"}'),
    ("json.inspect", '{"json":"[\\"\\\\ud800\\"]"}'),
])
def test_reject_unsafe_requests(operation, raw):
    with pytest.raises(mod.DisconnectedToolRejected):
        mod.execute_disconnected_fixture_tool(request(operation, raw))


def test_input_budget_and_container_budget():
    with pytest.raises(mod.DisconnectedToolRejected):
        mod.execute_disconnected_fixture_tool(
            request("text.stats", '{"text":"' + "a" * 9000 + '"}')
        )
    with pytest.raises(mod.DisconnectedToolRejected):
        mod.execute_disconnected_fixture_tool(
            request("math.sum", '{"values":[' + ",".join(["1"] * 129) + "]}")
        )
    with pytest.raises(mod.DisconnectedToolRejected):
        mod.execute_disconnected_fixture_tool(
            request("json.inspect", '{"json":"' + "[" * 30 + "0" + "]" * 30 + '"}')
        )


@pytest.mark.parametrize("field,value", [
    ("request_id", "req_invalid"), ("request_id", None),
    ("request_id", True), ("operation", True),
    ("canonical_args_json", None), ("canonical_args_json", []),
])
def test_exact_types_and_identity(field, value):
    item = request("math.sum", '{"values":[1]}')
    with pytest.raises(mod.DisconnectedToolRejected):
        mod.execute_disconnected_fixture_tool(replace(item, **{field: value}))


def test_reject_dataclass_subclass():
    class Derived(mod.DisconnectedToolRequest):
        pass

    with pytest.raises(mod.DisconnectedToolRejected):
        mod.execute_disconnected_fixture_tool(
            Derived("req_" + "a" * 32, "math.sum", '{"values":[1]}')
        )


def test_reflective_input_mutation_inside_digest(monkeypatch):
    item = request("math.sum", '{"values":[1]}')
    prior = mod.hashlib.sha256

    def reentrant(payload):
        object.__setattr__(item, "operation", "text.find")
        return prior(payload)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.DisconnectedToolRejected, match="changed"):
        mod.execute_disconnected_fixture_tool(item)


def test_reflective_equal_value_carrier_replacement(monkeypatch):
    item = request("math.sum", '{"values":[1]}')
    prior = mod.hashlib.sha256

    def reentrant(payload):
        same_value = bytes(item.canonical_args_json, "utf-8").decode("utf-8")
        assert same_value == item.canonical_args_json
        object.__setattr__(item, "canonical_args_json", same_value)
        return prior(payload)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=reentrant))
    with pytest.raises(mod.DisconnectedToolRejected, match="changed"):
        mod.execute_disconnected_fixture_tool(item)
