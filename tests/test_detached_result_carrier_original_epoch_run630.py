"""Run630: a disconnected READ receipt never invokes substituted carrier code."""

from __future__ import annotations

import hashlib

import pytest

from ark.agency import disconnected_result_budget as mod

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "b" * 16
_RAW = '{"value":3}'


def _row() -> mod.DetachedReadResult:
    return mod.DetachedReadResult(
        _STEP, "math.sum", _RAW, hashlib.sha256(_RAW.encode()).hexdigest(),
    )


def _seal(row: mod.DetachedReadResult) -> mod.CompleteDetachedReadResults:
    return mod.seal_detached_read_results(
        _REQUEST, ((_STEP, "math.sum"),), (row,),
    )


@pytest.mark.parametrize(("carrier", "attribute"), [
    ("result", "__init__"),
    ("result", "__getattribute__"),
    ("result", "step_id"),
    ("result", "canonical_result_json"),
    ("sealed", "__init__"),
    ("sealed", "__getattribute__"),
    ("sealed", "membership_digest"),
    ("sealed", "dispatch_authorized"),
])
def test_preinstalled_carrier_callback_never_runs(
    monkeypatch: pytest.MonkeyPatch, carrier: str, attribute: str,
) -> None:
    row = _row()
    invoked: list[str] = []

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append(attribute)
        raise AssertionError("untrusted carrier callback executed")

    cls = (
        mod.DetachedReadResult
        if carrier == "result"
        else mod.CompleteDetachedReadResults
    )
    monkeypatch.setattr(cls, attribute, poisoned, raising=False)
    with pytest.raises(
        mod.DisconnectedResultsRejected,
        match="carrier or authority descriptor changed",
    ):
        _seal(row)
    assert invoked == []


def test_late_sealed_constructor_substitution_during_digest_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    invoked: list[str] = []
    original_sha256 = hashlib.sha256
    original_init = mod.CompleteDetachedReadResults.__init__

    def poisoned(*_args: object, **_kwargs: object) -> None:
        invoked.append("constructor")
        raise AssertionError("substituted constructor executed")

    def hash_callback(raw: bytes = b""):
        if raw.startswith(mod._DOMAIN):
            monkeypatch.setattr(
                mod.CompleteDetachedReadResults, "__init__", poisoned,
            )
        return original_sha256(raw)

    monkeypatch.setattr(mod.hashlib, "sha256", hash_callback)
    try:
        with pytest.raises(mod.DisconnectedResultsRejected):
            _seal(row)
        assert invoked == []
    finally:
        monkeypatch.setattr(
            mod.CompleteDetachedReadResults, "__init__", original_init,
        )


def test_unchanged_local_results_remain_non_authorizing() -> None:
    sealed = _seal(_row())
    assert sealed.result_count == 1
    assert sealed.dispatch_authorized is False
    assert sealed.external_result_verified is False
    assert sealed.automatic_replay_authorized is False
