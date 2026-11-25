"""Run1414: observation envelope guards distinguish absent class hooks."""

from __future__ import annotations

import subprocess
import sys


def test_absent_envelope_hooks_reject_none_and_sentinel_installation() -> None:
    script = r"""
import ark.observations as observations
import ark.observation_fixture_adapters as adapters

envelope_type = observations.ObservationEnvelope
assert envelope_type is adapters._ENVELOPE_TYPE
observations._require_original_identity_carrier()
adapters._require_original_envelope()

def require_rejected(guard, label):
    try:
        guard()
    except ValueError:
        return
    raise AssertionError(f"{label} was accepted")

hooks = ("__new__", "__getattribute__", "__getattr__")
replacements = (
    None,
    observations._ABSENT_ENVELOPE_HOOK,
    adapters._ABSENT_ENVELOPE_HOOK,
)
for hook in hooks:
    for replacement in replacements:
        setattr(envelope_type, hook, replacement)
        require_rejected(
            observations._require_original_identity_carrier,
            f"observation guard accepted {hook}={replacement!r}",
        )
        require_rejected(
            adapters._require_original_envelope,
            f"adapter guard accepted {hook}={replacement!r}",
        )
        delattr(envelope_type, hook)
        observations._require_original_identity_carrier()
        adapters._require_original_envelope()

def replace_and_restore(module, name, replacement, guard):
    original = getattr(module, name)
    setattr(module, name, replacement)
    require_rejected(guard, f"{module.__name__}.{name} replacement")
    setattr(module, name, original)
    guard()

replace_and_restore(
    observations,
    "_ABSENT_ENVELOPE_HOOK",
    object(),
    observations._require_original_identity_carrier,
)
replace_and_restore(
    observations,
    "_ENVELOPE_HOOKS",
    tuple(list(observations._ENVELOPE_HOOKS)),
    observations._require_original_identity_carrier,
)
replace_and_restore(
    observations,
    "_ORIGINAL_ENVELOPE_HOOKS",
    tuple(list(observations._ORIGINAL_ENVELOPE_HOOKS)),
    observations._require_original_identity_carrier,
)
replace_and_restore(
    observations,
    "_ORIGINAL_ENVELOPE_IDENTITY_EPOCH",
    tuple(list(observations._ORIGINAL_ENVELOPE_IDENTITY_EPOCH)),
    observations._require_original_identity_carrier,
)
replace_and_restore(
    adapters,
    "_ABSENT_ENVELOPE_HOOK",
    object(),
    adapters._require_original_envelope,
)
replace_and_restore(
    adapters,
    "_ENVELOPE_HOOKS",
    tuple(list(adapters._ENVELOPE_HOOKS)),
    adapters._require_original_envelope,
)
replace_and_restore(
    adapters,
    "_ORIGINAL_ENVELOPE_HOOKS",
    tuple(list(adapters._ORIGINAL_ENVELOPE_HOOKS)),
    adapters._require_original_envelope,
)
replace_and_restore(
    adapters,
    "_ORIGINAL_ENVELOPE_GUARD_EPOCH",
    tuple(list(adapters._ORIGINAL_ENVELOPE_GUARD_EPOCH)),
    adapters._require_original_envelope,
)

original_observation_type = observations._ENVELOPE_TYPE
original_observation_alias = observations.ObservationEnvelope
replacement_type = type("ReplacementEnvelope", (), {})
observations._ENVELOPE_TYPE = replacement_type
observations.ObservationEnvelope = replacement_type
require_rejected(
    observations._require_original_identity_carrier,
    "joint observation type-alias replacement",
)
observations._ENVELOPE_TYPE = original_observation_type
observations.ObservationEnvelope = original_observation_alias
observations._require_original_identity_carrier()

original_adapter_type = adapters._ENVELOPE_TYPE
original_adapter_alias = adapters.ObservationEnvelope
adapters._ENVELOPE_TYPE = replacement_type
adapters.ObservationEnvelope = replacement_type
require_rejected(
    adapters._require_original_envelope,
    "joint adapter type-alias replacement",
)
adapters._ENVELOPE_TYPE = original_adapter_type
adapters.ObservationEnvelope = original_adapter_alias
adapters._require_original_envelope()
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_observation_identity_guard_denies_before_digest_callback() -> None:
    script = r"""
import ark.observations as observations

envelope_type = observations.ObservationEnvelope
envelope = envelope_type(
    kind=observations.ObservationKind.TEXT,
    source_id="synthetic",
    adapter_id="fixture:text:v1",
    privacy_scope="local:test",
    ingested_at_ms=1,
    content_sha256="a" * 64,
)
calls = []
original_sha256 = observations.hashlib.sha256

def forbidden_sha256(*args, **kwargs):
    calls.append(True)
    raise AssertionError("digest callback must not run")

observations.hashlib.sha256 = forbidden_sha256
setattr(envelope_type, "__getattr__", None)
try:
    vars(envelope_type)["observation_id"].fget(envelope)
except ValueError as exc:
    assert "definition changed" in str(exc)
else:
    raise AssertionError("absent-hook substitution was accepted")
assert calls == []
observations.hashlib.sha256 = original_sha256
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
