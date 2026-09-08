import pytest

from ark.evaluation.coding import test_code as grade_code
from ark.evaluation.scoring import score
from ark.evaluation.suite import load_suite


def case(task_id):
    return next(c for c in load_suite()["cases"] if c["id"] == task_id)


@pytest.mark.parametrize("answer", ["7/8", "0.875", " ０.８７５ "])
def test_numeric_normalization(answer):
    assert score(answer, case("math-02")).passed


@pytest.mark.parametrize("answer", ["", "The answer is 102", "101", "1/0", "NaN", "9" * 500])
def test_wrong_or_ambiguous_math_not_passed(answer):
    result = score(answer, case("math-01"))
    assert not result.passed
    assert result.reason


def test_strict_exact_and_duplicate_json_keys():
    assert score(" yes ", case("reason-01")).passed
    assert not score("YES or NO", case("reason-01")).passed
    assert score('{"status":"ready"}', case("conversation-02")).passed
    assert not score('{"status":"wrong", "status":"ready"}', case("conversation-02")).passed
    assert not score('{"status":true}', case("conversation-02")).passed


@pytest.mark.parametrize(
    "answer",
    [
        "def square(n):\n    return n*n",
        "```python\ndef square(n: int) -> int:\n    return n * n\n```",
    ],
)
def test_coding_uses_test_vectors(answer):
    passed, reason, results = grade_code(answer, case("coding-01"))
    assert passed and reason == "passed"
    assert len(results) == 3
    assert not grade_code("def square(n):\n    return n+n", case("coding-01"))[0]


@pytest.mark.parametrize(
    "answer",
    [
        "import os\ndef square(n):\n    return n*n",
        "def square(n):\n    return abs(n)",
        "def square(n):\n    return n.__class__",
        "def square(n):\n    while True: pass",
        "def square(n):\n    return 2**999999999",
        "def square(n):\n    return [n for x in n]",
        "def square(n):\n    return n*n if True else open('sentinel', 'w')",
        "@anything\ndef square(n):\n    return n*n",
        "def square(n=1):\n    return n*n",
        "def square(n: object.attr):\n    return n*n",
        "def square(n):\n    return 1//0",
        "def square(n):\n    return 999999999999 * 999999999999",
    ],
)
def test_unsupported_code_fails_closed(answer, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    passed, reason, _ = grade_code(answer, case("coding-01"))
    assert not passed and reason.startswith("rejected_or_failed")
    assert not list(tmp_path.iterdir())


def test_boolean_return_type_checked():
    assert not grade_code("def is_even(n):\n    return 1", case("coding-02"))[0]
