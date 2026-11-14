"""Disconnected fixture construction refuses substituted class before execution."""

import hashlib

import pytest

import ark.observation_fixture_adapters as adapters
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture(binary):
    if binary:
        return adapters.fixture_binary_observation(
            b"fixture-bytes", kind=ObservationKind.IMAGE,
            source_id="local", privacy_scope="owner:private", ingested_at_ms=1,
        )
    return adapters.fixture_text_observation(
        "fixture-text", kind=ObservationKind.TEXT,
        source_id="local", privacy_scope="owner:private", ingested_at_ms=1,
    )


@pytest.mark.parametrize("binary", (False, True))
@pytest.mark.parametrize("phase", ("before", "digest"))
def test_forged_fixture_constructor_never_runs(monkeypatch, binary, phase):
    called = []

    def counterfeit(**_kwargs):
        called.append(True)
        raise AssertionError("counterfeit constructor must not execute")

    def tamper():
        monkeypatch.setattr(adapters, "ObservationEnvelope", counterfeit)

    if phase == "before":
        tamper()
    else:
        original_hash = hashlib.sha256
        payload = b"fixture-bytes" if binary else b"fixture-text"

        def hash_and_tamper(value=b""):
            if value == payload:
                tamper()
            return original_hash(value)

        monkeypatch.setattr(adapters.hashlib, "sha256", hash_and_tamper)

    expected = "digest implementation" if phase == "digest" else "non-envelope"
    with pytest.raises(ValueError, match=expected):
        _fixture(binary)
    assert called == []


@pytest.mark.parametrize("binary", (False, True))
def test_constructor_hook_cannot_replace_imported_class(monkeypatch, binary):
    original = ObservationEnvelope.__post_init__
    called = []

    def counterfeit(**_kwargs):
        called.append(True)
        raise AssertionError("counterfeit constructor must not execute")

    def after_construct(self):
        original(self)
        monkeypatch.setattr(adapters, "ObservationEnvelope", counterfeit)

    monkeypatch.setattr(ObservationEnvelope, "__post_init__", after_construct)
    # The original validator is now pinned before the forged callback runs.
    with pytest.raises(ValueError, match="changed during construction"):
        _fixture(binary)
    assert called == []


@pytest.mark.parametrize("binary", (False, True))
def test_original_fixture_remains_minimized(binary):
    result = _fixture(binary)
    assert type(result) is ObservationEnvelope
    expected = b"fixture-bytes" if binary else b"fixture-text"
    assert result.content_sha256 == hashlib.sha256(expected).hexdigest()
    assert result.privacy_scope == "owner:private"
    assert not hasattr(result, "raw_bytes")
