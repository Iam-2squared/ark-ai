"""Detached disconnected-tool plan tests; no action or ToolBackend invoked."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from ark.agency import disconnected_batch_plan as mod

REQ = "req_" + "a" * 32


def step(number=1, op="math.sum", args='{"values":[1,2]}', depends=()):
    return mod.DisconnectedBatchStep(f"step_{number:016x}", op, args, depends)


def make(steps=None):
    return mod.build_disconnected_batch_plan(REQ, steps or (step(),))


def test_positive_independent_and_dependent_batch():
    first = step()
    second = step(2, "text.find", '{"needle":"x","text":"xyz"}', (first.step_id,))
    batch = make((first, second))
    assert batch == make((first, second))
    assert len(batch.plan_digest) == 64
    mod.verify_disconnected_batch_plan(batch, retained_digest=batch.plan_digest)
    assert not batch.dispatch_authorized
    assert not batch.write_authorized
    assert not batch.replay_authorized
    assert not batch.execution_proven


@pytest.mark.parametrize("args", [
    '{"values": [1]}', '{"values":[1]} ', '{"values":[1],"values":[2]}',
    '{"values":[1.0]}', '{"values":[NaN]}',
    '{"values":[9223372036854775808]}', '{"values":[-9223372036854775809]}',
    '{"values":["\\ud800"]}', '[1,2]', 'null', '',
])
def test_invalid_json_is_rejected(args):
    with pytest.raises(mod.DisconnectedBatchRejected):
        make((step(args=args),))


@pytest.mark.parametrize("field,value", [
    ("step_id", "step_invalid"), ("step_id", True),
    ("operation", "os.exec"), ("operation", True),
    ("canonical_args_json", None), ("depends_on", ("step_0000000000000002",)),
    ("depends_on", ["step_0000000000000002"]),
    ("depends_on", ("step_0000000000000001",)),
])
def test_unsafe_step_is_rejected(field, value):
    with pytest.raises(mod.DisconnectedBatchRejected):
        make((replace(step(), **{field: value}),))


def test_duplicate_and_forward_dependent_and_unsorted_deps():
    first, second = step(), step(2)
    for rows in (
        (first, first),
        (replace(first, depends_on=(second.step_id,)), second),
        (first, second, step(3, depends=(second.step_id, first.step_id))),
    ):
        with pytest.raises(mod.DisconnectedBatchRejected):
            make(rows)


def test_bounded_batch_and_schema():
    with pytest.raises(mod.DisconnectedBatchRejected):
        make(tuple(step(n) for n in range(1, 27)))
    with pytest.raises(mod.DisconnectedBatchRejected):
        make((step(args='{"text":"' + 'a' * 5000 + '"}'),))
    with pytest.raises(mod.DisconnectedBatchRejected):
        mod.build_disconnected_batch_plan("bad", (step(),))


def test_reflective_mutation_during_hash_rejected(monkeypatch):
    first = step()
    initial = mod.hashlib.sha256

    def altered(data):
        object.__setattr__(first, "operation", "text.find")
        return initial(data)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=altered))
    with pytest.raises(mod.DisconnectedBatchRejected, match="mutated"):
        make((first,))


def test_reverification_requires_independent_witness():
    original = make()
    with pytest.raises(mod.DisconnectedBatchRejected):
        mod.verify_disconnected_batch_plan(
            replace(original, plan_digest="f" * 64), retained_digest=original.plan_digest,
        )
    with pytest.raises(mod.DisconnectedBatchRejected):
        mod.verify_disconnected_batch_plan(
            original, retained_digest="f" * 64,
        )
    with pytest.raises(mod.DisconnectedBatchRejected):
        mod.verify_disconnected_batch_plan(
            replace(original, canonical_plan_json="{}"),
            retained_digest=original.plan_digest,
        )


def test_mutating_plan_during_verify_rejected(monkeypatch):
    batch = make()
    original = mod.hashlib.sha256

    def altered(data):
        object.__setattr__(batch, "plan_digest", "f" * 64)
        return original(data)

    monkeypatch.setattr(mod, "hashlib", SimpleNamespace(sha256=altered))
    with pytest.raises(mod.DisconnectedBatchRejected, match="mutated"):
        mod.verify_disconnected_batch_plan(batch, retained_digest=batch.plan_digest)


def test_no_implicit_execution_and_stable_empty_dependency():
    batch = make((step(), step(2)))
    assert '"depends_on":[]' in batch.canonical_plan_json
    assert '"operation":"math.sum"' in batch.canonical_plan_json
    assert len(batch.steps) == 2
