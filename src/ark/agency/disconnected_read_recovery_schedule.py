"""Pure, deny-only recovery schedule for synthetic disconnected READ graphs.

This module never runs or retries a tool. A READY_MOCK_ONLY state is a
planning hint, not an authorization. All identities/results are caller-supplied,
not authenticated, and no real-world effect is attested.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_REQUEST = re.compile(r"req_[0-9a-f]{32}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OPS = frozenset(("math.sum", "text.stats", "text.find", "json.inspect"))
_STATES = frozenset(("NOT_STARTED", "SUCCEEDED", "FAILED", "RUNNING", "UNKNOWN"))
_DOMAIN = b"ARK-detached-read-recovery-schedule-v1\0"


class DetachedReadRecoveryRejected(ValueError):
    """An untrusted READ history is incomplete, contradictory or mutable."""


@dataclass(frozen=True, slots=True)
class ReadRecoveryStep:
    step_id: str
    operation: str
    depends_on: tuple[str, ...]
    state: str
    result_sha256: str | None = None


@dataclass(frozen=True, slots=True)
class ReadRecoveryDecision:
    step_id: str
    disposition: str


@dataclass(frozen=True, slots=True)
class DetachedReadRecoverySchedule:
    request_id: str
    decisions: tuple[ReadRecoveryDecision, ...]
    schedule_digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False


# Inspect untrusted step carriers statically before touching any slot. A
# replacement slot descriptor or __getattribute__ can execute when validating
# a supplied frozen dataclass; it must not become the recovery authority.
_STEP_TYPE = ReadRecoveryStep
_STEP_FIELDS = ("step_id", "operation", "depends_on", "state", "result_sha256")
_ORIGINAL_STEP_SLOTS = tuple(vars(_STEP_TYPE)[field] for field in _STEP_FIELDS)
_STEP_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_STEP_HOOKS = tuple(vars(_STEP_TYPE).get(hook) for hook in _STEP_HOOKS)
_ORIGINAL_STEP_FIELDS_VECTOR = _STEP_FIELDS
_ORIGINAL_STEP_HOOKS_VECTOR = _STEP_HOOKS

_DECISION_TYPE = ReadRecoveryDecision
_SCHEDULE_TYPE = DetachedReadRecoverySchedule
_ORIGINAL_DECISION_INIT = vars(_DECISION_TYPE)["__init__"]
_ORIGINAL_SCHEDULE_INIT = vars(_SCHEDULE_TYPE)["__init__"]
_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_DECISION_FIELDS = ("step_id", "disposition")
_SCHEDULE_FIELDS = ("request_id", "decisions", "schedule_digest")
_ORIGINAL_DECISION_FIELDS = tuple(
    vars(_DECISION_TYPE)[field] for field in _DECISION_FIELDS
)
_ORIGINAL_SCHEDULE_FIELDS = tuple(
    vars(_SCHEDULE_TYPE)[field] for field in _SCHEDULE_FIELDS
)
_ORIGINAL_DECISION_HOOKS = tuple(
    vars(_DECISION_TYPE).get(hook) for hook in _RESULT_HOOKS
)
_ORIGINAL_SCHEDULE_HOOKS = tuple(
    vars(_SCHEDULE_TYPE).get(hook) for hook in _RESULT_HOOKS
)
_DENIAL_NAMES = (
    "dispatch_authorized", "automatic_replay_authorized",
    "external_outcome_verified",
)
_ORIGINAL_DENIAL_DESCRIPTORS = tuple(
    vars(_SCHEDULE_TYPE)[name] for name in _DENIAL_NAMES
)


# Schedule hashes and accepted graph states are part of the reviewed
# diagnostic protocol. A replacement JSON/SHA callback must not see a
# caller-retained READ graph, and broadened parser/state sets are not valid.
# These are process-local checks, not trusted external provenance.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_REQUEST = _REQUEST
_ORIGINAL_STEP = _STEP
_ORIGINAL_SHA = _SHA
_ORIGINAL_OPS = _OPS
_ORIGINAL_STATES = _STATES


def _assert_original_denials() -> None:
    """Do not bless a preinstalled False-only replacement after processing."""
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _REQUEST is not _ORIGINAL_REQUEST
        or _STEP is not _ORIGINAL_STEP
        or _SHA is not _ORIGINAL_SHA
        or _OPS is not _ORIGINAL_OPS
        or _STATES is not _ORIGINAL_STATES
        or ReadRecoveryStep is not _STEP_TYPE
        or _STEP_FIELDS is not _ORIGINAL_STEP_FIELDS_VECTOR
        or _STEP_HOOKS is not _ORIGINAL_STEP_HOOKS_VECTOR
        or any(
            vars(_STEP_TYPE).get(field) is not original
            for field, original in zip(_STEP_FIELDS, _ORIGINAL_STEP_SLOTS, strict=True)
        )
        or any(
            vars(_STEP_TYPE).get(hook) is not original
            for hook, original in zip(_STEP_HOOKS, _ORIGINAL_STEP_HOOKS, strict=True)
        )
        or DetachedReadRecoverySchedule is not _SCHEDULE_TYPE
        or ReadRecoveryDecision is not _DECISION_TYPE
        or vars(_DECISION_TYPE).get("__init__") is not _ORIGINAL_DECISION_INIT
        or vars(_SCHEDULE_TYPE).get("__init__") is not _ORIGINAL_SCHEDULE_INIT
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in (
                (_DECISION_TYPE, _DECISION_FIELDS, _ORIGINAL_DECISION_FIELDS),
                (_SCHEDULE_TYPE, _SCHEDULE_FIELDS, _ORIGINAL_SCHEDULE_FIELDS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or any(
            vars(cls).get(name) is not original
            for cls, originals in (
                (_DECISION_TYPE, _ORIGINAL_DECISION_HOOKS),
                (_SCHEDULE_TYPE, _ORIGINAL_SCHEDULE_HOOKS),
            )
            for name, original in zip(_RESULT_HOOKS, originals, strict=True)
        )
        or any(
            vars(_SCHEDULE_TYPE).get(name) is not original
            for name, original in zip(
                _DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise DetachedReadRecoveryRejected(
            "recovery schedule authority descriptor changed"
        )


def schedule_detached_read_recovery(
    request_id: str, steps: tuple[ReadRecoveryStep, ...],
) -> DetachedReadRecoverySchedule:
    """Classify each mock READ without authorizing execution or replay.

    A SUCCEEDED step requires every predecessor to be SUCCEEDED; impossible
    recovered histories fail closed. Unknown/RUNNING ancestors contaminate
    all pending descendants. Only unrelated NOT_STARTED branches are marked
    READY_MOCK_ONLY. A FAILED predecessor holds descendants terminally.
    """
    _assert_original_denials()
    if (
        type(request_id) is not str or _REQUEST.fullmatch(request_id) is None
        or type(steps) is not tuple or not 1 <= len(steps) <= 24
        or any(type(row) is not ReadRecoveryStep for row in steps)
    ):
        raise DetachedReadRecoveryRejected("invalid exact READ recovery input")
    original_id, original_steps = request_id, steps
    originals = tuple(steps)
    pinned = tuple(
        (row.step_id, row.operation, row.depends_on, row.state, row.result_sha256)
        for row in originals
    )

    def epoch() -> None:
        _assert_original_denials()
        if (
            request_id is not original_id or steps is not original_steps
            or any(row is not old or any(
                current is not expected for current, expected in zip(
                    (row.step_id, row.operation, row.depends_on, row.state,
                     row.result_sha256), values, strict=True,
                )
            ) for row, old, values in zip(steps, originals, pinned, strict=True))
        ):
            raise DetachedReadRecoveryRejected("READ history carrier changed")

    epoch()
    prior_states: dict[str, str] = {}
    dispositions: dict[str, str] = {}
    manifest: list[dict[str, object]] = []
    decisions: list[ReadRecoveryDecision] = []
    decision_epoch: list[tuple[ReadRecoveryDecision, str, str]] = []

    def stable_decisions() -> None:
        # A frozen dataclass can still be rewritten by object.__setattr__.
        # Retain every earlier constructed decision across later callbacks.
        if len(decisions) != len(decision_epoch) or any(
            type(value) is not _DECISION_TYPE
            or value is not original
            or value.step_id is not name
            or value.disposition is not code
            for value, (original, name, code) in zip(
                decisions, decision_epoch, strict=True,
            )
        ):
            raise DetachedReadRecoveryRejected("READ recovery decision carrier changed")

    for name, operation, deps, state, digest in pinned:
        epoch()
        stable_decisions()
        if (
            type(name) is not str or _STEP.fullmatch(name) is None
            or name in prior_states or type(operation) is not str
            or operation not in _OPS or type(deps) is not tuple
            or len(deps) > 16 or any(type(dep) is not str for dep in deps)
            or deps != tuple(sorted(set(deps)))
            or any(dep not in prior_states for dep in deps)
            or type(state) is not str or state not in _STATES
            or (state == "SUCCEEDED") != (
                type(digest) is str and _SHA.fullmatch(digest) is not None
            )
            or (state != "SUCCEEDED" and digest is not None)
        ):
            raise DetachedReadRecoveryRejected("invalid ordered READ state or digest")
        ancestors = tuple(dispositions[dep] for dep in deps)
        # A failed, running, or unknown *started* child cannot legitimately
        # precede its dependency's success. Do not launder such contradictory
        # restart history into a seemingly terminal or quarantined decision.
        # An unstarted child remains a valid HOLD/WAIT diagnostic.
        if state in ("FAILED", "RUNNING", "UNKNOWN") and any(
            prior_states[dep] != "SUCCEEDED" for dep in deps
        ):
            raise DetachedReadRecoveryRejected(
                "started READ after unresolved dependency"
            )
        if state == "SUCCEEDED":
            if any(prior_states[dep] != "SUCCEEDED" for dep in deps):
                raise DetachedReadRecoveryRejected("success after unresolved dependency")
            disposition = "COMPLETE_UNVERIFIED"
        elif state == "FAILED":
            disposition = "TERMINAL_FAILURE"
        elif state in ("RUNNING", "UNKNOWN"):
            disposition = "QUARANTINE_UNCERTAIN"
        elif any(item in ("TERMINAL_FAILURE", "HOLD_FAILED") for item in ancestors):
            disposition = "HOLD_FAILED"
        elif any(item in ("QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN") for item in ancestors):
            disposition = "HOLD_UNCERTAIN"
        elif ancestors and any(item != "COMPLETE_UNVERIFIED" for item in ancestors):
            disposition = "WAIT_DEPENDENCY"
        else:
            disposition = "READY_MOCK_ONLY"
        # Do not invoke a substituted initializer even if it would return an
        # apparently inert decision after executing arbitrary Python.
        _assert_original_denials()
        decision = _DECISION_TYPE(name, disposition)
        _assert_original_denials()
        if (
            type(decision) is not _DECISION_TYPE
            or decision.step_id is not name
            or decision.disposition is not disposition
        ):
            raise DetachedReadRecoveryRejected("invalid READ recovery decision carrier")
        decisions.append(decision)
        decision_epoch.append((decision, name, disposition))
        stable_decisions()
        prior_states[name] = state
        dispositions[name] = disposition
        manifest.append({
            "step_id": name, "operation": operation, "depends_on": deps,
            "state": state, "result_sha256": digest, "disposition": disposition,
        })
        epoch()
        stable_decisions()
    payload = json.dumps(
        {"request_id": request_id, "steps": manifest},
        sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    if len(payload) > 32_768:
        raise DetachedReadRecoveryRejected("recovery manifest too large")
    epoch()
    stable_decisions()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    epoch()
    stable_decisions()
    frozen_decisions = tuple(decisions)
    _assert_original_denials()
    schedule = _SCHEDULE_TYPE(request_id, frozen_decisions, digest)
    _assert_original_denials()
    denial_names = _DENIAL_NAMES
    denial_descriptors = _ORIGINAL_DENIAL_DESCRIPTORS
    epoch()
    stable_decisions()

    def assert_inert_schedule() -> None:
        # A false-valued getter can substitute another false-valued property.
        # Compare original class descriptors as well as output field carriers
        # before and AFTER all denial callbacks.
        if any(
            getattr(_SCHEDULE_TYPE, name) is not original
            for name, original in zip(
                denial_names, denial_descriptors, strict=True,
            )
        ):
            raise DetachedReadRecoveryRejected(
                "recovery schedule authority descriptor changed"
            )
        if (
            type(schedule) is not _SCHEDULE_TYPE
            or schedule.request_id is not request_id
            or schedule.decisions is not frozen_decisions
            or schedule.schedule_digest is not digest
            or schedule.dispatch_authorized is not False
            or schedule.automatic_replay_authorized is not False
            or schedule.external_outcome_verified is not False
            or any(
                getattr(_SCHEDULE_TYPE, name) is not original
                for name, original in zip(
                    denial_names, denial_descriptors, strict=True,
                )
            )
        ):
            raise DetachedReadRecoveryRejected("recovery schedule altered before return")

    assert_inert_schedule()
    # A false-valued final denial getter is still a callback: it can mutate
    # an earlier witness field, a previously checked flag or a nested decision.
    # Check those carriers after all three non-authority getters have run.
    epoch()
    stable_decisions()
    assert_inert_schedule()
    epoch()
    stable_decisions()
    return schedule
