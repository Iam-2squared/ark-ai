"""Offline reference binding rejects poisoned READ/receipt dataclass carriers.

No tool dispatch, filesystem access, model call or authorization is involved.
"""

from __future__ import annotations

import json
from contextlib import contextmanager

import pytest

import ark.agency.disconnected_reference_binding as binding

_MISSING = object()
_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _fixture():
    raw = '{"value":4}'
    row = binding.SyntheticReadResult(
        _STEP, raw, binding.read_result_digest(_STEP, raw),
    )
    template = json.dumps(
        {"n": {"$from": {"pointer": "/value", "step_id": _STEP}}},
        sort_keys=True, separators=(",", ":"),
    )
    return template, (row,)


def _bind(fixture):
    template, rows = fixture
    return binding.bind_synthetic_read_arguments(
        _REQUEST, template, (_STEP,), rows,
    )


@contextmanager
def _poison(cls, name, called):
    prior = vars(cls).get(name, _MISSING)

    def malicious(*_args, **_kwargs):
        called.append(name)
        raise AssertionError("untrusted READ descriptor executed")

    replacement = property(malicious) if name in (
        "step_id", "canonical_result_json", "retained_digest",
        "request_id", "used_step_ids", "canonical_args_json", "binding_digest",
        "dispatch_authorized", "source_authenticated", "replay_authorized",
        "external_result_proven",
    ) else staticmethod(malicious) if name == "__new__" else malicious
    setattr(cls, name, replacement)
    try:
        yield
    finally:
        if prior is _MISSING:
            delattr(cls, name)
        else:
            setattr(cls, name, prior)


@pytest.mark.parametrize("name", (
    "step_id", "canonical_result_json", "retained_digest",
    "__init__", "__getattribute__", "__getattr__",
))
def test_read_carrier_poison_refused_before_untrusted_json_read(name):
    fixture = _fixture()
    called = []
    with _poison(binding.SyntheticReadResult, name, called):
        with pytest.raises(binding.ReadBindingRejected, match="carrier definition"):
            _bind(fixture)
        assert called == []


@pytest.mark.parametrize("name", (
    "request_id", "used_step_ids", "canonical_args_json", "binding_digest",
    "dispatch_authorized", "source_authenticated",
    "replay_authorized", "external_result_proven",
    "__init__", "__getattribute__", "__getattr__",
))
def test_output_carrier_poison_refused_before_result_construction(name):
    fixture = _fixture()
    called = []
    with _poison(binding.SyntheticBoundArguments, name, called):
        with pytest.raises(binding.ReadBindingRejected, match="carrier definition"):
            _bind(fixture)
        assert called == []


def test_reentrant_json_parser_cannot_install_new_receipt_constructor(monkeypatch):
    fixture = _fixture()
    original_load = binding._load
    cls = binding.SyntheticBoundArguments
    constructor = vars(cls)["__init__"]
    called = []

    def malicious(*_args, **_kwargs):
        called.append("constructor")
        raise AssertionError("unexpected receipt construction")

    def changed(raw, *, root_object):
        result = original_load(raw, root_object=root_object)
        cls.__init__ = malicious
        return result

    monkeypatch.setattr(binding, "_load", changed)
    try:
        with pytest.raises(binding.ReadBindingRejected, match="carrier definition"):
            _bind(fixture)
        assert called == []
    finally:
        cls.__init__ = constructor


def test_normal_reference_remains_deny_only():
    result = _bind(_fixture())
    assert result.canonical_args_json == '{"n":4}'
    assert result.used_step_ids == (_STEP,)
    assert result.dispatch_authorized is False
    assert result.source_authenticated is False
    assert result.replay_authorized is False
    assert result.external_result_proven is False
