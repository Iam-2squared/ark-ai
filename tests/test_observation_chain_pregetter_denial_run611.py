"""Offline observation review must never invoke a counterfeit denial getter.

All inputs are synthetic strings; no camera, microphone, real media, consent,
or external action is involved.
"""

import pytest

import ark.observation_fixture_chain_review as chain
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationKind


def _inspect():
    envelope = fixture_text_observation(
        "test-only",
        kind=ObservationKind.TEXT,
        source_id="fixture",
        privacy_scope="local:private",
        ingested_at_ms=1,
    )
    return chain.review_disconnected_fixture_chain(
        (envelope,), source_id="fixture", privacy_scope="local:private",
    )


class _Counterfeit:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("executed")
        return False


@pytest.mark.parametrize("field", chain._DENIALS)
def test_reflected_result_field_read_cannot_inject_false_denial(
    monkeypatch, field,
):
    calls = []
    original = chain._RESULT.__getattribute__
    replaced = [False]

    def during_result_check(self, name):
        if name == "chain_sha256" and not replaced[0]:
            replaced[0] = True
            monkeypatch.setattr(chain._RESULT, field, _Counterfeit(calls))
        return original(self, name)

    monkeypatch.setattr(chain._RESULT, "__getattribute__", during_result_check)
    with pytest.raises(
        chain.ObservationFixtureChainRejected, match="implementation changed",
    ):
        _inspect()
    # The preaccess hook check now rejects before any result field callback.
    assert replaced == [False]
    assert calls == []


def test_earlier_denial_callback_cannot_replace_later_denial(monkeypatch):
    calls = []
    original = chain._RESULT.__getattribute__

    def during_first_denial(self, name):
        if name == "source_authenticated":
            monkeypatch.setattr(
                chain._RESULT, "consent_verified", _Counterfeit(calls),
            )
        return original(self, name)

    monkeypatch.setattr(chain._RESULT, "__getattribute__", during_first_denial)
    with pytest.raises(
        chain.ObservationFixtureChainRejected, match="implementation changed",
    ):
        _inspect()
    assert calls == []


def test_original_synthetic_fixture_remains_non_authorizing():
    result = _inspect()
    assert result.envelope_count == 1
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
