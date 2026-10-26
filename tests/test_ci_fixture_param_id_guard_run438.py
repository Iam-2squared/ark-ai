"""Prevent 4 MiB fixture payloads becoming Windows pytest node IDs.

This AST-only regression check does not collect or allocate the payloads, skip
any tests, modify the CI workflow, or rely on any network/runner service.
"""

import ast
from pathlib import Path


_TARGET = Path(__file__).with_name("test_observation_fixture_production_adapters.py")
_LIMIT = 4 * 1024 * 1024


def _number(node):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, ast.Mult):
            return _number(node.left) * _number(node.right)
        if isinstance(node.op, ast.Add):
            return _number(node.left) + _number(node.right)
    raise AssertionError("fixture multiplier is not a bounded integer expression")


def _payload_length(node):
    if (
        not isinstance(node, ast.BinOp)
        or not isinstance(node.op, ast.Mult)
        or not isinstance(node.left, ast.Constant)
        or type(node.left.value) not in (str, bytes)
    ):
        raise AssertionError("expected immutable repeated fixture literal")
    return len(node.left.value) * _number(node.right)


def _fixture_test():
    module = ast.parse(_TARGET.read_text(encoding="utf-8"))
    items = [
        item for item in module.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == "test_fixture_rejects_oversized_payload"
    ]
    assert len(items) == 1
    test = items[0]
    mark = next(
        (decorator for decorator in test.decorator_list
         if isinstance(decorator, ast.Call)
         and isinstance(decorator.func, ast.Attribute)
         and decorator.func.attr == "parametrize"),
        None,
    )
    assert mark is not None and len(mark.args) == 2
    assert isinstance(mark.args[0], ast.Constant)
    assert mark.args[0].value == "factory,payload"
    assert isinstance(mark.args[1], (ast.List, ast.Tuple))
    return test, mark


def test_oversize_fixture_parameter_ids_are_short_but_payloads_unchanged():
    _test, mark = _fixture_test()
    cases = mark.args[1].elts
    assert len(cases) == 2
    lengths = []
    for case in cases:
        assert isinstance(case, (ast.Tuple, ast.List)) and len(case.elts) == 2
        lengths.append(_payload_length(case.elts[1]))
    assert lengths == [_LIMIT + 1, _LIMIT + 1]
    ids = [keyword.value for keyword in mark.keywords if keyword.arg == "ids"]
    assert len(ids) == 1
    assert isinstance(ids[0], (ast.List, ast.Tuple))
    labels = ast.literal_eval(ids[0])
    assert type(labels) is tuple and len(labels) == len(cases)
    assert len(set(labels)) == len(labels)
    assert all(type(label) is str and 0 < len(label) <= 64 for label in labels)


def test_oversize_fixture_still_requires_rejection_not_skip():
    test, _mark = _fixture_test()
    assert not any(
        isinstance(decorator, ast.Attribute) and decorator.attr == "skip"
        for decorator in test.decorator_list
    )
    expected = [
        call for call in ast.walk(test)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and call.func.attr == "raises"
    ]
    assert len(expected) == 1
    assert any(
        keyword.arg == "match"
        and isinstance(keyword.value, ast.Constant)
        and keyword.value.value == "byte budget exceeded"
        for keyword in expected[0].keywords
    )
