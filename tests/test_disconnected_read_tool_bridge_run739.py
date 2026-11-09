"""Run739 integration: replay-unsafe recovery never touches external backends."""

import pytest

from ark.agency import disconnected_read_tool_bridge as mod

_REQUEST = "req_" + "a" * 32
_FIRST = "step_" + "1" * 16
_SECOND = "step_" + "2" * 16
_THIRD = "step_" + "3" * 16


def step(identifier, operation="math.sum", deps=(), state="NOT_STARTED", digest=None):
    return mod.recovery.ReadRecoveryStep(identifier, operation, deps, state, digest)


def binding(identifier, operation="math.sum", raw='{"values":[2,3]}'):
    return mod.DetachedReadToolBinding(
        identifier,
        mod.fixture.DisconnectedToolRequest(
            mod.derive_disconnected_read_fixture_id(_REQUEST, identifier),
            operation,
            raw,
        ),
    )


def test_disconnected_independent_read_fixtures_are_deterministic_and_inert():
    steps = (
        step(_FIRST), step(_SECOND, "text.find"),
    )
    bindings = (
        binding(_FIRST), binding(
            _SECOND, "text.find", '{"needle":"abc","text":"zabc"}',
        ),
    )
    first = mod.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    second = mod.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert first == second
    assert first.ready_step_ids == (_FIRST, _SECOND)
    assert first.withheld_step_ids == ()
    assert len(first.fixture_results) == 2
    assert first.fixture_results[0].canonical_result_json == '{"count":2,"sum":5}'
    assert first.fixture_results[1].canonical_result_json == '{"index":1}'
    assert len(first.fingerprint) == 64
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
    assert first.external_effect_verified is False
    assert first.consent_authenticated is False


@pytest.mark.parametrize("state,held", [
    ("UNKNOWN", "HOLD_UNCERTAIN"),
    ("RUNNING", "HOLD_UNCERTAIN"),
    ("FAILED", "HOLD_FAILED"),
])
def test_uncertain_or_failed_parent_is_never_run_or_retried(state, held):
    steps = (
        step(_FIRST, state=state),
        step(_SECOND, deps=(_FIRST,)),
        step(_THIRD),
    )
    plan = mod.recovery.schedule_detached_read_recovery(_REQUEST, steps)
    assert plan.decisions[1].disposition == held
    preview = mod.preview_disconnected_read_tools(
        _REQUEST, steps, (binding(_THIRD),),
    )
    assert preview.ready_step_ids == (_THIRD,)
    assert preview.withheld_step_ids == (_FIRST, _SECOND)
    assert len(preview.fixture_results) == 1


def test_complete_unverified_step_never_runs_again():
    steps = (
        step(_FIRST, state="SUCCEEDED", digest="b" * 64),
        step(_SECOND, deps=(_FIRST,)),
    )
    preview = mod.preview_disconnected_read_tools(
        _REQUEST, steps, (binding(_SECOND),),
    )
    assert preview.withheld_step_ids == (_FIRST,)
    assert preview.ready_step_ids == (_SECOND,)
    assert preview.automatic_replay_authorized is False


@pytest.mark.parametrize("bindings", [
    (),
    (binding(_SECOND), binding(_FIRST)),
    (binding(_FIRST), binding(_FIRST)),
    (binding(_FIRST, raw='{"values":[1]}'), binding(_FIRST)),
])
def test_missing_duplicate_or_misordered_bindings_are_rejected(bindings):
    steps = (step(_FIRST), step(_SECOND))
    with pytest.raises(mod.DisconnectedReadToolBridgeRejected):
        mod.preview_disconnected_read_tools(_REQUEST, steps, bindings)


def test_binding_for_quarantined_step_is_refused_before_tool_execution(monkeypatch):
    steps = (step(_FIRST, state="UNKNOWN"), step(_SECOND))
    calls = []

    def unsafe(*args):
        calls.append(args)
        raise AssertionError("mock executor must not be invoked")

    monkeypatch.setattr(mod.fixture, "execute_disconnected_fixture_tool", unsafe)
    with pytest.raises(mod.DisconnectedReadToolBridgeRejected):
        mod.preview_disconnected_read_tools(
            _REQUEST, steps, (binding(_FIRST),),
        )
    assert not calls


@pytest.mark.parametrize("operation,raw", [
    ("text.find", '{"needle":"abc","text":"abc"}'),
    ("math.sum", '{"values":[1.5]}'),
    ("math.sum", '{"values":[true]}'),
])
def test_operation_mismatch_or_malformed_mock_payload_refused(operation, raw):
    with pytest.raises((
        mod.DisconnectedReadToolBridgeRejected,
        mod.fixture.DisconnectedToolRejected,
    )):
        mod.preview_disconnected_read_tools(
            _REQUEST, (step(_FIRST),), (binding(_FIRST, operation, raw),),
        )


def test_per_step_request_id_does_not_alias_other_step():
    first = mod.derive_disconnected_read_fixture_id(_REQUEST, _FIRST)
    second = mod.derive_disconnected_read_fixture_id(_REQUEST, _SECOND)
    assert first != second
    assert len(first) == len(second) == 36
    invalid = mod.DetachedReadToolBinding(
        _FIRST, mod.fixture.DisconnectedToolRequest(
            second, "math.sum", '{"values":[1]}',
        ),
    )
    with pytest.raises(mod.DisconnectedReadToolBridgeRejected):
        mod.preview_disconnected_read_tools(
            _REQUEST, (step(_FIRST),), (invalid,),
        )


@pytest.mark.parametrize("request_id,step_id", [
    ("req_bad", _FIRST),
    (_REQUEST, "step_bad"),
    (True, _FIRST),
    (_REQUEST, None),
])
def test_exact_identity_rejected(request_id, step_id):
    with pytest.raises(mod.DisconnectedReadToolBridgeRejected):
        mod.derive_disconnected_read_fixture_id(request_id, step_id)
