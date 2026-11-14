"""Synthetic occurrence hashing rejects untrusted digest callbacks before tokens.

This fixture never grants consent, backend dispatch, clock authenticity or
external exactly-once effects. No credential or live tool is involved.
"""

from __future__ import annotations

import hashlib
from types import SimpleNamespace

import pytest

from ark.agency import durable_occurrence_review as module
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic reservation cannot dispatch")


def _setup(tmp_path):
    backend = _NeverExecute()
    call = ToolCall("fixture.write", "fixture", "local", {"v": "fixture"})
    registry = ToolRegistry((
        ToolRegistration("fixture.write", "fixture", Effect.WRITE, "mock", backend),
    ))
    token = OneShotAuthorization("private-fixture-token", call.request_id, 500)
    path = tmp_path / "occurrence.sqlite"
    return module.SyntheticOccurrenceStore(path), registry, call, token, backend


def _reserve(store, registry, call, token, suffix="a"):
    return store.reserve_synthetic(
        registry, call, token, occurrence_id="occ_" + suffix * 64, now_ms=25,
    )


@pytest.mark.parametrize("change", ("sha256", "module", "during_bind"))
def test_tampered_digest_cannot_receive_private_token_or_reserve(
    tmp_path, monkeypatch, change,
):
    store, registry, call, token, backend = _setup(tmp_path)
    digest_calls = []

    def forbidden_digest(payload=b""):
        digest_calls.append(payload)
        pytest.fail("substituted digest received private token bytes")

    with monkeypatch.context() as patch:
        if change == "sha256":
            patch.setattr(module.hashlib, "sha256", forbidden_digest)
        elif change == "module":
            patch.setattr(
                module, "hashlib", SimpleNamespace(sha256=forbidden_digest),
            )
        else:
            original_bind = ToolRegistry.bind
            binding_calls = []

            def tampering_bind(self, action):
                bound = original_bind(self, action)
                binding_calls.append(True)
                patch.setattr(
                    module, "hashlib", SimpleNamespace(sha256=forbidden_digest),
                )
                return bound

            patch.setattr(ToolRegistry, "bind", tampering_bind)

        with pytest.raises(
            module.SyntheticReplayRejected, match="digest implementation changed",
        ):
            _reserve(store, registry, call, token)

    assert digest_calls == []
    assert store.count_synthetic() == 0
    assert backend.calls == 0
    # Restoring the digest does not turn the denied attempt into a reservation.
    accepted = _reserve(store, registry, call, token)
    assert accepted.dispatch_authorized is False
    assert accepted.outcome_known is False
    assert accepted.automatic_replay_authorized is False
    assert store.count_synthetic() == 1
    assert backend.calls == 0
    assert hashlib.sha256(b"test").hexdigest()
