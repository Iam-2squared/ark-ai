"""Offline-only READ result reference binding tests."""

from __future__ import annotations

import json

import pytest

from ark.agency.disconnected_reference_binding import (
    ReadBindingRejected,
    SyntheticReadResult,
    bind_synthetic_read_arguments,
    read_result_digest,
)

REQUEST = "req_" + "a" * 32
STEP1 = "step_" + "1" * 16
STEP2 = "step_" + "2" * 16
STEP3 = "step_" + "3" * 16


def row(step=STEP1, payload='{"items":[7,{"a/b":22}],"value":4}'):
    return SyntheticReadResult(step, payload, read_result_digest(step, payload))


def template(reference=STEP1, pointer="/value"):
    return json.dumps(
        {"numbers": [{"$from": {"step_id": reference, "pointer": pointer}}, 5]},
        sort_keys=True, separators=(",", ":"),
    )


def bind(t=None, results=None, prefix=None):
    return bind_synthetic_read_arguments(
        REQUEST, template() if t is None else t,
        (STEP1,) if prefix is None else prefix,
        (row(),) if results is None else results,
    )


def test_reference_binds_nested_value_and_denies_external_dispatch():
    result = bind()
    assert result.canonical_args_json == '{"numbers":[4,5]}'
    assert result.used_step_ids == (STEP1,)
    assert len(result.binding_digest) == 64
    assert not result.dispatch_authorized
    assert not result.source_authenticated
    assert not result.replay_authorized
    assert not result.external_result_proven


def test_reference_escaped_pointer_and_array_index():
    result = bind(template(STEP1, "/items/1/a~1b"))
    assert result.canonical_args_json == '{"numbers":[22,5]}'
    result = bind(template(STEP1, "/items/0"))
    assert result.canonical_args_json == '{"numbers":[7,5]}'


def test_literal_template_requires_no_result_fixture():
    result = bind('{"a":1}', results=(), prefix=())
    assert result.canonical_args_json == '{"a":1}'
    assert result.used_step_ids == ()


def test_multiple_prior_reads_ordered_by_plan_prefix():
    earlier = (row(STEP1), row(STEP3, '{"value":19}'))
    t = '{"a":{"$from":{"pointer":"/value","step_id":"' + STEP3 + '"}},'
    t += '"b":{"$from":{"pointer":"/value","step_id":"' + STEP1 + '"}}}'
    result = bind(t, results=earlier, prefix=(STEP1, STEP2, STEP3))
    assert result.canonical_args_json == '{"a":19,"b":4}'
    assert result.used_step_ids == (STEP1, STEP3)


@pytest.mark.parametrize("payload", [
    '{"x":1,"x":2}', '{"x":1.5}', '{"x":NaN}',
    '{"x":9223372036854775808}', '{ "x":1}', '[1,2]',
])
def test_template_rejects_unsafe_json(payload):
    with pytest.raises(ReadBindingRejected):
        bind(payload)


@pytest.mark.parametrize("pointer", [
    "/missing", "bad/path", "/items/-", "/items/02",
    "/items/20", "/items/~2", "/items/1/a~", "/" * 14,
])
def test_noncanonical_or_missing_pointers_fail_closed(pointer):
    with pytest.raises(ReadBindingRejected):
        bind(template(STEP1, pointer))


@pytest.mark.parametrize("payload", [
    '{"items":[1],"items":[2]}', '{"value":3.14}',
    '{"a":1e309}', '3.5', '{"value":9223372036854775808}',
])
def test_result_json_rejects_unsafe_values(payload):
    with pytest.raises(ReadBindingRejected):
        row(STEP1, payload)


def test_forged_digest_is_rejected():
    corrupt = SyntheticReadResult(STEP1, '{"value":5}', "a" * 64)
    with pytest.raises(ReadBindingRejected):
        bind(results=(corrupt,))


def test_prior_result_reordering_rejected():
    with pytest.raises(ReadBindingRejected):
        bind(results=(row(STEP2, '{"value":2}'), row()), prefix=(STEP1, STEP2))


def test_ref_to_missing_and_future_result_rejected():
    with pytest.raises(ReadBindingRejected):
        bind(template(STEP2, "/value"))
    with pytest.raises(ReadBindingRejected):
        bind(template(STEP2, "/value"), prefix=(STEP1, STEP2))


def test_duplicate_result_and_prefix_rejected():
    with pytest.raises(ReadBindingRejected):
        bind(results=(row(), row()))
    with pytest.raises(ReadBindingRejected):
        bind(prefix=(STEP1, STEP1))


def test_ambiguous_marker_rejected():
    bad = '{"x":{"$from":{"step_id":"' + STEP1 + '","pointer":""},"else":2}}'
    with pytest.raises(ReadBindingRejected):
        bind(bad)


def test_array_root_result_supported():
    result = row(STEP1, '[2,3]')
    bound = bind(template(STEP1, "/1"), results=(result,))
    assert bound.canonical_args_json == '{"numbers":[3,5]}'


def test_result_digest_changes_on_step_identity():
    payload = '{"a":1}'
    assert read_result_digest(STEP1, payload) != read_result_digest(STEP2, payload)


def test_large_expanded_result_rejected():
    content = "a" * 4000
    result = row(STEP1, json.dumps({"value": content}, separators=(",", ":")))
    bound = bind(template(), results=(result,))
    assert len(bound.canonical_args_json) > 4000
    t = json.dumps({"x": [{"$from": {"step_id": STEP1, "pointer": "/value"}}] * 2},
                   sort_keys=True, separators=(",", ":"))
    with pytest.raises(ReadBindingRejected):
        bind(t, results=(result,))


def test_absent_prior_cannot_resolve():
    with pytest.raises(ReadBindingRejected):
        bind(results=())


def test_noncanonical_pointer_null_root_is_supported():
    result = row(STEP1, "null")
    bound = bind(template(STEP1, ""), results=(result,))
    assert bound.canonical_args_json == '{"numbers":[null,5]}'
