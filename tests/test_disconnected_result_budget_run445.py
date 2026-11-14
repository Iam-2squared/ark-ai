"""Isolated deterministic fixtures for complete READ result-set budget checks."""

import hashlib
import json
from dataclasses import FrozenInstanceError

import pytest

from ark.agency.disconnected_result_budget import (
    CompleteDetachedReadResults,
    DetachedReadResult,
    DisconnectedResultsRejected,
    seal_detached_read_results,
)

REQ = "req_" + "a" * 32
ONE = "step_" + "0" * 16
TWO = "step_" + "1" * 16
THREE = "step_" + "2" * 16


def row(step=ONE, operation="math.sum", raw='{"value":3}', sha=None):
    return DetachedReadResult(
        step, operation, raw, (
            hashlib.sha256(raw.encode("utf-8", "surrogatepass")).hexdigest()
            if sha is None else sha
        ),
    )


def seal(expected=((ONE, "math.sum"),), rows=None, request=REQ):
    return seal_detached_read_results(
        request, expected, (row(),) if rows is None else rows,
    )


def test_single_and_capability_boundary():
    result = seal()
    assert type(result) is CompleteDetachedReadResults
    assert result.request_id == REQ
    assert result.step_ids == (ONE,)
    assert result.result_bytes == len('{"value":3}')
    assert result.result_count == 1
    assert len(result.membership_digest) == 64
    assert not result.dispatch_authorized
    assert not result.external_result_verified
    assert not result.automatic_replay_authorized


def test_determinism_and_complete_ordinal():
    expected = ((ONE, "math.sum"), (TWO, "text.stats"))
    rows = (row(), row(TWO, "text.stats", '{"lines":2}'))
    left = seal(expected, rows)
    right = seal(expected, rows)
    assert left == right
    assert left.membership_digest != seal().membership_digest


def test_plan_defined_nonlexical_order_is_respected():
    steps = ((TWO, "math.sum"), (ONE, "math.sum"))
    rows = (row(TWO), row())
    result = seal(steps, rows)
    assert result.step_ids == (TWO, ONE)
    assert result.membership_digest != seal(
        ((ONE, "math.sum"), (TWO, "math.sum")), (row(), row(TWO)),
    ).membership_digest


def test_no_raw_payload_leaks_to_sealed_result():
    secret = "syntheticPrivateValue"
    raw = json.dumps({"secret": secret}, sort_keys=True, separators=(",", ":"))
    sealed = seal(rows=(row(raw=raw),))
    assert secret not in repr(sealed)
    assert not hasattr(sealed, "canonical_result_json")
    with pytest.raises(FrozenInstanceError):
        sealed.result_bytes = 0


@pytest.mark.parametrize("req_value", [None, True, "req_x", "req_" + "A" * 32, "a" * 32])
def test_invalid_request(req_value):
    with pytest.raises(DisconnectedResultsRejected):
        seal(request=req_value)


@pytest.mark.parametrize("expected,rows", [
    ((), ()),
    (((ONE, "math.sum"), (TWO, "math.sum")), (row(),)),
    (((ONE, "math.sum"),), (row(), row(TWO))),
    (((ONE, "math.sum"), (ONE, "math.sum")), (row(), row())),
    (((TWO, "math.sum"), (ONE, "math.sum")), (row(), row(TWO))),
    (((ONE, "math.sum"),), (row(TWO),)),
    (((ONE, "math.sum"),), (row(operation="json.inspect"),)),
    (((ONE, "shell.exec"),), (row(operation="shell.exec"),)),
    (((ONE,),), (row(),)),
    ((("step_bad", "math.sum"),), (row(step="step_bad"),)),
    (((ONE, "math.sum"),), (row(sha="f" * 64),)),
    (((ONE, "math.sum"),), (row(sha="not_sha"),)),
])
def test_membership_denials(expected, rows):
    with pytest.raises(DisconnectedResultsRejected):
        seal(expected, rows)


@pytest.mark.parametrize("raw", [
    '{"b":2,"a":1}', '{"a":1,"a":2}', '{"n":1.0}', '{"n":NaN}',
    '{"n":9223372036854775808}', '{"n":-9223372036854775809}',
    '{"v":"\ud800"}', "[]  ", "{", "", " " * 8193,
    '{"x":true, "z":1}',
])
def test_noncanonical_or_invalid_json(raw):
    with pytest.raises(DisconnectedResultsRejected):
        seal(rows=(row(raw=raw),))


def test_signed_int64_and_utf8_escaping():
    value = '{"n":-9223372036854775808,"text":"\\u65e5"}'
    assert seal(rows=(row(raw=value),)).result_count == 1


def test_total_bytes_capped_independently_of_individual_results():
    big = json.dumps({"s": "x" * 8170}, separators=(",", ":"))
    expected = tuple(("step_" + f"{i:016x}", "math.sum") for i in range(9))
    rows = tuple(row(step, raw=big) for step, _ in expected)
    assert len(big) < 8192
    with pytest.raises(DisconnectedResultsRejected, match="aggregate"):
        seal(expected, rows)


def test_max24_complete_results():
    expected = tuple(("step_" + f"{i:016x}", "math.sum") for i in range(24))
    result = seal(expected, tuple(row(step) for step, _ in expected))
    assert result.result_count == 24
    with pytest.raises(DisconnectedResultsRejected):
        seal(expected + (("step_" + "f" * 16, "math.sum"),),
             tuple(row(step) for step, _ in expected) + (row("step_" + "f" * 16),))


def test_mutation_during_sha_callback_denied(monkeypatch):
    target = row()
    actual_hash = hashlib.sha256
    def switched(payload=b""):
        object.__setattr__(target, "step_id", target.step_id.encode().decode())
        return actual_hash(payload)
    monkeypatch.setattr(
        "ark.agency.disconnected_result_budget.hashlib.sha256", switched,
    )
    with pytest.raises(DisconnectedResultsRejected):
        seal(rows=(target,))


def test_exact_type_required():
    class Child(DetachedReadResult):
        pass
    with pytest.raises(DisconnectedResultsRejected):
        seal(rows=(Child(ONE, "math.sum", "{}", hashlib.sha256(b"{}").hexdigest()),))
    with pytest.raises(DisconnectedResultsRejected):
        seal(rows=[row()])
    with pytest.raises(DisconnectedResultsRejected):
        seal(expected=[(ONE, "math.sum")])


def test_bool_and_nesting_result_canonical():
    assert seal(rows=(row(raw='{"a":[true,false,null]}'),)).result_count == 1
    payload = '[0]'
    for _ in range(13):
        payload = '[' + payload + ']'
    with pytest.raises(DisconnectedResultsRejected):
        seal(rows=(row(raw=payload),))
