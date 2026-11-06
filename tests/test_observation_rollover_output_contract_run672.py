"""Observation rollover witnesses reject class-level callbacks before evidence reads.

Only disconnected synthetic observation envelopes are used. Child processes
isolate tests that replace Python allocation or lookup hooks.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys

import pytest

import ark.observation_rollover_review as rollover
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _window(now=100):
    scope = "local:private"
    return ObservationWindowReview(
        scope, now, 20,
        (
            ObservationEnvelope(
                ObservationKind.TEXT, "fixture", "fixture-adapter",
                scope, now - 1, hashlib.sha256(b"synthetic").hexdigest(),
            ),
        ),
    )


@pytest.mark.parametrize("name", rollover._WITNESS_FIELDS)
def test_replaced_witness_slot_denied_before_callback(monkeypatch, name):
    def forbidden(_self):
        pytest.fail("untrusted rollover field executed before preflight")

    current = _window()
    monkeypatch.setattr(
        rollover.ObservationRolloverWitness, name, property(forbidden),
    )
    with pytest.raises(ValueError, match="result changed before construction"):
        rollover.review_observation_rollover(current)


@pytest.mark.parametrize("hook", rollover._WITNESS_HOOKS)
def test_replaced_witness_constructor_or_lookup_denied_in_child(hook):
    script = """
import hashlib
import ark.observation_rollover_review as review
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind

scope = "local:private"
current = ObservationWindowReview(
    scope, 100, 20,
    (ObservationEnvelope(
        ObservationKind.TEXT, "fixture", "fixture-adapter",
        scope, 99, hashlib.sha256(b"synthetic").hexdigest(),
    ),),
)

def forbidden(*args, **kwargs):
    raise AssertionError("untrusted rollover witness hook ran")

setattr(review.ObservationRolloverWitness, HOOK, forbidden)
try:
    review.review_observation_rollover(current)
except ValueError as exc:
    assert "result changed before construction" in str(exc), str(exc)
else:
    raise AssertionError("replaced rollover witness hook was accepted")
""".replace("HOOK", repr(hook))
    child = subprocess.run(
        [sys.executable, "-c", script],
        check=False, capture_output=True, text=True,
    )
    assert child.returncode == 0, child.stdout + child.stderr


def test_normal_rollover_and_replay_remain_deterministic_and_inert():
    first = rollover.review_observation_rollover(_window(100))
    second = rollover.review_observation_rollover(_window(110), retained=first)
    same = rollover.review_observation_rollover(_window(110), retained=second)
    assert second == same
    assert second.generation == 2
    assert second.chain_sha256 != first.chain_sha256
    assert not hasattr(second, "notification_authorized")
