"""Direct observation identity hashing rejects executable class-level slots.

Only synthetic metadata is used. No media capture, network, source attestation,
consent, notification, or tool dispatch occurs.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark import observations

_FIELDS = observations._ENVELOPE_FIELDS
_HOOKS = ("__init__", "__getattribute__", "__getattr__", "__post_init__")


def _envelope():
    return observations.ObservationEnvelope(
        observations.ObservationKind.TRANSCRIPT,
        "synthetic-source", "fixture-local", "private",
        123, "a" * 64,
    )


@pytest.mark.parametrize("name", _FIELDS + _HOOKS)
def test_original_direct_identity_slots_checked_before_field_access(
    monkeypatch, name,
):
    envelope = _envelope()
    called = []

    def poison(*_args, **_kwargs):
        called.append(name)
        raise AssertionError("poisoned metadata descriptor executed")

    replacement = property(poison) if name in _FIELDS else poison
    monkeypatch.setattr(
        observations.ObservationEnvelope, name, replacement, raising=False,
    )
    # Python resolves an instance property through __getattribute__ first.
    # Invoke the original reviewed property's fget directly when testing
    # poisoning of that very lookup hook; otherwise the test itself would
    # execute the injected getter before our guard can possibly run.
    original_property = observations._ORIGINAL_ENVELOPE_HOOKS[
        observations._ENVELOPE_HOOKS.index("observation_id")
    ]
    with pytest.raises(ValueError, match="observation identity definition changed"):
        original_property.fget(envelope)
    assert called == []


@pytest.mark.parametrize("target", ("source_id", "__getattribute__", "__post_init__"))
def test_direct_validation_rejects_hook_before_reading_metadata(
    monkeypatch, target,
):
    envelope = _envelope()
    called = []

    def poison(*_args, **_kwargs):
        called.append(target)
        raise AssertionError("poisoned validation slot executed")

    replacement = property(poison) if target == "source_id" else poison
    monkeypatch.setattr(
        observations.ObservationEnvelope, target, replacement, raising=False,
    )
    # Call the original validator directly so an overridden instance
    # __getattribute__ or __post_init__ cannot run merely when obtaining it.
    original_validator = observations._ORIGINAL_ENVELOPE_HOOKS[
        observations._ENVELOPE_HOOKS.index("__post_init__")
    ]
    with pytest.raises(ValueError, match="observation identity definition changed"):
        original_validator(envelope)
    assert called == []


@pytest.mark.parametrize("callback,slot", (
    ("json", "source_id"),
    ("hash", "__post_init__"),
))
def test_reentrant_serialization_cannot_install_executable_metadata_slot(
    monkeypatch, callback, slot,
):
    envelope = _envelope()
    invoked = []
    digest_calls = []

    def poisoned(*_args, **_kwargs):
        invoked.append(slot)
        raise AssertionError("poisoned reentrant accessor executed")

    replacement = property(poisoned) if slot == "source_id" else poisoned
    if callback == "json":
        original = observations.json.dumps

        def injected(*args, **kwargs):
            digest_calls.append("unsafe serializer")
            output = original(*args, **kwargs)
            monkeypatch.setattr(observations.ObservationEnvelope, slot, replacement)
            return output

        monkeypatch.setattr(observations.json, "dumps", injected)
    else:
        original = observations.hashlib.sha256

        def injected(*args, **kwargs):
            digest_calls.append("unsafe hash")
            output = original(*args, **kwargs)
            monkeypatch.setattr(observations.ObservationEnvelope, slot, replacement)
            return output

        monkeypatch.setattr(observations.hashlib, "sha256", injected)
    with pytest.raises(ValueError, match="digest implementation changed"):
        _ = envelope.observation_id
    assert digest_calls == []
    assert invoked == []


def test_observation_allocation_override_is_isolated_from_pytest_interpreter():
    script = textwrap.dedent("""
        from ark import observations
        envelope = observations.ObservationEnvelope(
            observations.ObservationKind.TEXT, 'synthetic', 'fixture',
            'private', 1, 'a' * 64,
        )
        called = []

        def bad(*args, **kwargs):
            called.append("new")
            raise AssertionError("allocation hook executed")

        observations.ObservationEnvelope.__new__ = staticmethod(bad)
        try:
            _ = envelope.observation_id
        except ValueError as exc:
            assert 'identity definition changed' in str(exc)
        else:
            raise AssertionError("poisoned class allocation hook accepted")
        assert called == []
    """)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_unchanged_observation_identity_is_still_deterministic():
    before = _envelope()
    second = _envelope()
    assert before.observation_id == second.observation_id
    assert before.observation_id.startswith("obs_")
