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


_DECISION_TYPE = ReadRecoveryDecision
_SCHEDULE_TYPE = DetachedReadRecoverySchedule


def schedule_detached_read_recovery(
    request_id: str, steps: tuple[ReadRecoveryStep, ...],
) -> DetachedReadRecoverySchedule:
    """Classify each mock READ without authorizing execution or replay.

    A SUCCEEDED step requires every predecessor to be SUCCEEDED; impossible
    recovered histories fail closed. Unknown/RUNNING ancestors contaminate
    all pending descendants. Only unrelated NOT_STARTED branches are marked
    READY_MOCK_ONLY. A FAILED predecessor holds descendants terminally.
    """
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
        decision = ReadRecoveryDecision(name, disposition)
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
    schedule = DetachedReadRecoverySchedule(request_id, frozen_decisions, digest)
    epoch()
    stable_decisions()
    if (
        type(schedule) is not _SCHEDULE_TYPE
        or schedule.request_id is not request_id
        or schedule.decisions is not frozen_decisions
        or schedule.schedule_digest is not digest
        or schedule.dispatch_authorized is not False
        or schedule.automatic_replay_authorized is not False
        or schedule.external_outcome_verified is not False
    ):
        raise DetachedReadRecoveryRejected("recovery schedule altered before return")
    return schedule
