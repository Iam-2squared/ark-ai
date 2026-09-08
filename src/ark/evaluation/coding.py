"""A bounded integer-expression interpreter, NOT a general Python sandbox.

Generated source is parsed as data. It is never passed to exec/eval or a subprocess.
"""

from __future__ import annotations

import ast
import operator
import re

MAX_SOURCE = 4096
MAX_NODES = 80
MAX_MAGNITUDE = 10**12
BINARY = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
COMPARE = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


class RejectedCode(ValueError):
    pass


def _bounded(value: int | bool) -> int | bool:
    if type(value) not in (int, bool) or abs(value) > MAX_MAGNITUDE:
        raise RejectedCode("integer value outside interpreter bounds")
    return value


def _validate(node: ast.AST, parameters: list[str], depth: int = 0) -> None:
    if depth > 24:
        raise RejectedCode("expression too deep")
    if isinstance(node, ast.Constant) and type(node.value) in (int, bool):
        _bounded(node.value)
        return
    if isinstance(node, ast.Name) and node.id in parameters:
        return
    if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
        children = [node.left, node.right]
    elif isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in COMPARE:
        children = [node.left, node.comparators[0]]
    elif isinstance(node, ast.IfExp):
        children = [node.test, node.body, node.orelse]
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):
        children = [node.operand]
    else:
        raise RejectedCode(f"unsupported syntax: {type(node).__name__}")
    for child in children:
        _validate(child, parameters, depth + 1)


def _interpret(node: ast.AST, values: dict[str, int]) -> int | bool:
    if isinstance(node, ast.Constant):
        result = node.value
    elif isinstance(node, ast.Name):
        result = values[node.id]
    elif isinstance(node, ast.BinOp):
        result = BINARY[type(node.op)](
            _interpret(node.left, values), _interpret(node.right, values)
        )
    elif isinstance(node, ast.Compare):
        result = COMPARE[type(node.ops[0])](
            _interpret(node.left, values), _interpret(node.comparators[0], values)
        )
    elif isinstance(node, ast.IfExp):
        result = _interpret(node.body if _interpret(node.test, values) else node.orelse, values)
    elif isinstance(node, ast.UnaryOp):
        value = _interpret(node.operand, values)
        result = (
            -value
            if isinstance(node.op, ast.USub)
            else (not value if isinstance(node.op, ast.Not) else +value)
        )
    else:
        raise RejectedCode("unexpected unvalidated node")
    return _bounded(result)


def test_code(source: str, case: dict) -> tuple[bool, str, list[dict]]:
    try:
        if len(source.encode("utf-8")) > MAX_SOURCE:
            raise RejectedCode("source too large")
        source = source.strip()
        if source.startswith("```"):
            match = re.fullmatch(r"```(?:python)?\s*\n(.*?)\n```", source, re.DOTALL)
            if not match:
                raise RejectedCode("expected one Python code block")
            source = match.group(1)
        tree = ast.parse(source)
        if sum(1 for _ in ast.walk(tree)) > MAX_NODES:
            raise RejectedCode("too many syntax nodes")
        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            raise RejectedCode("expected one function")
        func = tree.body[0]
        args = func.args
        if (
            func.name != case["entry"]
            or func.decorator_list
            or args.defaults
            or args.kw_defaults
            or args.vararg
            or args.kwarg
            or args.kwonlyargs
            or args.posonlyargs
            or [a.arg for a in args.args] != case["parameters"]
            or len(set(case["parameters"])) != len(case["parameters"])
        ):
            raise RejectedCode("function signature does not match")
        # Even annotations are restricted; they are never evaluated.
        annotations = [a.annotation for a in args.args] + [func.returns]
        if any(
            a is not None and not (isinstance(a, ast.Name) and a.id in {"int", "bool"})
            for a in annotations
        ):
            raise RejectedCode("unsupported annotation")
        if getattr(func, "type_params", []):
            raise RejectedCode("generic type parameters unsupported")
        if len(func.body) != 1 or not isinstance(func.body[0], ast.Return):
            raise RejectedCode("only a single return expression is supported")
        expression = func.body[0].value
        _validate(expression, case["parameters"])
        outcomes = []
        for vector in case["tests"]:
            if len(vector["args"]) != len(case["parameters"]):
                raise RejectedCode("invalid test vector")
            values = dict(zip(case["parameters"], map(_bounded, vector["args"]), strict=True))
            actual = _interpret(expression, values)
            expected = vector["expected"]
            outcomes.append(
                {
                    "args": vector["args"],
                    "expected": expected,
                    "actual": actual,
                    "passed": type(actual) is type(expected) and actual == expected,
                }
            )
        passed = bool(outcomes) and all(o["passed"] for o in outcomes)
        return passed, "passed" if passed else "test_mismatch", outcomes
    except (SyntaxError, ValueError, TypeError, ArithmeticError, RecursionError) as exc:
        return False, f"rejected_or_failed: {type(exc).__name__}: {exc}", []
