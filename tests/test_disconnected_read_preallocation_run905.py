"""Run905: detached synthetic READ payloads fail closed before expensive input work.

All fixtures are disconnected; they carry no backend execution authority.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency import disconnected_result_budget as mod

REQUEST = "req_" + "a" * 32
STEP = "step_" + "b" * 16
RAW = '{"answer":42}'


def _row(*, step: str = STEP, operation: str = "math.sum",
         raw: str = RAW, digest: str | None = None) -> mod.DetachedReadResult:
    return mod.DetachedReadResult(
        step, operation, raw,
        hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if digest is None else digest,
    )


def _seal(*, request: str = REQUEST, step: str = STEP,
          operation: str = "math.sum",
          result: mod.DetachedReadResult | None = None):
    return mod.seal_detached_read_results(
        request,
        ((step, operation),),
        (_row() if result is None else result,),
    )


def test_valid_digest_only_result_remains_non_authorizing():
    result = _seal()
    assert result.result_count == 1
    assert result.result_bytes == len(RAW)
    assert result.dispatch_authorized is False
    assert result.external_result_verified is False
    assert result.automatic_replay_authorized is False


class _RegexMustNotRun:
    def fullmatch(self, _value):
        raise AssertionError("unbounded text reached regex")


def test_oversized_request_rejected_before_regex(monkeypatch):
    monkeypatch.setattr(mod, "_REQ", _RegexMustNotRun())
    with pytest.raises(mod.DisconnectedResultsRejected, match="membership"):
        _seal(request="req_" + "a" * 200_000)


def test_oversized_expected_step_rejected_before_regex(monkeypatch):
    monkeypatch.setattr(mod, "_STEP", _RegexMustNotRun())
    long_step = "step_" + "a" * 200_000
    with pytest.raises(mod.DisconnectedResultsRejected, match="identity"):
        _seal(step=long_step)


def test_oversized_provided_digest_rejected_before_regex(monkeypatch):
    monkeypatch.setattr(mod, "_SHA", _RegexMustNotRun())
    with pytest.raises(mod.DisconnectedResultsRejected, match="identity"):
        _seal(result=_row(digest="a" * 200_000))


class _ComparisonBomb(str):
    def __ne__(self, _other):
        raise AssertionError("untrusted string comparison executed")

    def __eq__(self, _other):
        raise AssertionError("untrusted string comparison executed")

    __hash__ = str.__hash__


@pytest.mark.parametrize("field", ["step_id", "operation"])
def test_reflected_str_subclass_denied_before_comparison(field):
    supplied = STEP if field == "step_id" else "math.sum"
    replacement = _ComparisonBomb(supplied)
    result = _row(
        step=replacement if field == "step_id" else STEP,
        operation=replacement if field == "operation" else "math.sum",
    )
    with pytest.raises(mod.DisconnectedResultsRejected, match="identity"):
        _seal(result=result)


def test_multi_megabyte_result_rejected_by_size():
    huge = '{"text":"' + "x" * (3 * 1024 * 1024) + '"}'
    result = _row(raw=RAW)
    object.__setattr__(result, "canonical_result_json", huge)
    with pytest.raises(mod.DisconnectedResultsRejected, match="byte budget"):
        _seal(result=result)


def test_legal_utf8_result_still_passes_digest_and_bytes():
    raw = '{"text":"\\u65e5"}'
    result = _seal(result=_row(raw=raw))
    assert result.result_bytes == len(raw.encode("utf-8"))
    assert result.membership_digest != "0" * 64
