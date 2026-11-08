"""Offline scheduler policy class mutations must fail before private reads.

These subprocesses isolate CPython type-slot edits, including __new__. No
notification, trusted clock, external scheduler, or real action is exercised.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
)

ATTRIBUTES = (
    "owner",
    "namespace",
    "minimum_interval_ms",
    "max_preparations_per_window",
    "identity",
    "__post_init__",
    "__init__",
    "__new__",
    "__getattribute__",
    "__getattr__",
)


@pytest.mark.parametrize("attribute", ATTRIBUTES)
def test_policy_mutation_is_rejected_before_sqlite_or_hostile_lookup(attribute):
    script = textwrap.dedent(
        """
        import tempfile
        from pathlib import Path

        from ark.proactive_synthetic_review import (
            SyntheticProactiveLedger,
            SyntheticTriggerPolicy,
            SyntheticTriggerRejected,
        )

        with tempfile.TemporaryDirectory() as location:
            ledger = SyntheticProactiveLedger(Path(location) / "triggers.sqlite")
            policy = SyntheticTriggerPolicy(
                "offline", "private", "fixture", 1, "v1", 1, 10, 3,
            )
            called = []

            def hostile(*args, **kwargs):
                called.append("unexpected-policy-access")
                raise AssertionError("hostile policy callback executed")

            if ATTRIBUTE in {"identity", "__post_init__", "__init__",
                             "__new__", "__getattribute__", "__getattr__"}:
                setattr(SyntheticTriggerPolicy, ATTRIBUTE, hostile)
            else:
                setattr(SyntheticTriggerPolicy, ATTRIBUTE, property(hostile))

            try:
                ledger.prepare(
                    policy, source_digest="b" * 64, observation_digest="c" * 64,
                    observed_at_ms=100, now_ms=100,
                )
            except SyntheticTriggerRejected:
                pass
            else:
                raise AssertionError("mutated policy admitted")
            assert not called, called
            assert ledger.count() == 0
        """
    ).replace("ATTRIBUTE", repr(attribute))
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_original_trigger_policy_still_prepares_only_inert_local_marker(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "healthy.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "private", "fixture", 1, "v1", 1, 10, 3,
    )
    marker = ledger.prepare(
        policy, source_digest="b" * 64, observation_digest="c" * 64,
        observed_at_ms=100, now_ms=100,
    )
    assert ledger.count() == 1
    assert marker.dispatch_authorized is False
    assert marker.notification_authorized is False
    assert marker.automatic_replay_authorized is False
