"""Cross-check two independent, disconnected READ recovery classifiers.

This is a diagnostic consistency check on caller-supplied synthetic facts.
It never dispatches, replays, opens a database, verifies a historical result,
or grants permission. Matching hashes do not authenticate external custody.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import MappingProxyType

from .disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    ReadRecoveryStep,
    _assert_original_denials,
    schedule_detached_read_recovery,
)
from .disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    _require_original_fence_denials,
    review_disconnected_recovery_fence,
)

_DOMAIN = b"ARK-disconnected-read-recovery-projection-v1\0"
_STATE = MappingProxyType({"NOT_STARTED": "PENDING"})
_CODES = MappingProxyType({
    "COMPLETE_UNVERIFIED": "COMPLETE_UNVERIFIED",
    "TERMINAL_FAILURE": "TERMINAL",
    "QUARANTINE_UNCERTAIN": "QUARANTINE_UNKNOWN",
    "HOLD_FAILED": "HOLD_TERMINAL",
    "HOLD_UNCERTAIN": "HOLD_UNCERTAIN",
    "WAIT_DEPENDENCY": "WAIT_DEPENDENCY",
    "READY_MOCK_ONLY": "READY_MOCK_ONLY",
})
_ORIGINAL_SCHEDULE = schedule_detached_read_recovery
_ORIGINAL_FENCE = review_disconnected_recovery_fence
_ORIGINAL_READ_GUARD = _assert_original_denials
_ORIGINAL_MIXED_GUARD = _require_original_fence_denials
_ORIGINAL_STATE_MAP = _STATE
_ORIGINAL_CODE_MAP = _CODES
_ORIGINAL_STEP_TYPE = ReadRecoveryStep
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


class ReadRecoveryProjectionRejected(ValueError):
    """Two independent mock-only recovery reviewers could not be reconciled."""


@dataclass(frozen=True, slots=True)
class ReadRecoveryProjection:
    request_id: str
    plan_id: str
    read_schedule_digest: str
    mixed_fence_digest: str
    ready_step_ids: tuple[str, ...]
    review_sha256: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def authenticated_history(self) -> bool:
        return False


_RESULT = ReadRecoveryProjection
_FIELDS = (
    "request_id", "plan_id", "read_schedule_digest",
    "mixed_fence_digest", "ready_step_ids", "review_sha256",
)
_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "authenticated_history",
)
_ORIGINAL_FIELDS = tuple(vars(_RESULT)[name] for name in _FIELDS)
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[name] for name in _DENIALS)
_ORIGINAL_INIT = vars(_RESULT)["__init__"]
_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_HOOKS = tuple(vars(_RESULT).get(name) for name in _HOOKS)


def _require_original_protocol() -> None:
    if (
        schedule_detached_read_recovery is not _ORIGINAL_SCHEDULE
        or review_disconnected_recovery_fence is not _ORIGINAL_FENCE
        or _assert_original_denials is not _ORIGINAL_READ_GUARD
        or _require_original_fence_denials is not _ORIGINAL_MIXED_GUARD
        or _STATE is not _ORIGINAL_STATE_MAP
        or _CODES is not _ORIGINAL_CODE_MAP
        or ReadRecoveryStep is not _ORIGINAL_STEP_TYPE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or ReadRecoveryProjection is not _RESULT
        or vars(_RESULT).get("__init__") is not _ORIGINAL_INIT
        or any(
            vars(_RESULT).get(name) is not original
            for names, originals in (
                (_FIELDS, _ORIGINAL_FIELDS),
                (_DENIALS, _ORIGINAL_DENIALS),
                (_HOOKS, _ORIGINAL_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
    ):
        raise ReadRecoveryProjectionRejected("recovery projection protocol changed")
    try:
        _ORIGINAL_READ_GUARD()
        _ORIGINAL_MIXED_GUARD()
    except (DetachedReadRecoveryRejected, OfflineRecoveryFenceRejected) as exc:
        raise ReadRecoveryProjectionRejected(
            "source recovery authority descriptor changed"
        ) from exc


def review_disconnected_read_projection(
    request_id: str, plan_id: str, steps: tuple[ReadRecoveryStep, ...],
) -> ReadRecoveryProjection:
    """Require consistent recovery decisions from READ-only and mixed reviewers.

    The two classifiers intentionally have distinct identity domains and
    independent disposition code sets. The mapping covers only READ claims;
    neither this check nor READY_MOCK_ONLY permits dispatch.
    """
    _require_original_protocol()
    if (
        type(request_id) is not str or type(plan_id) is not str
        or type(steps) is not tuple
        or not 1 <= len(steps) <= 24
        or any(type(step) is not ReadRecoveryStep for step in steps)
    ):
        raise ReadRecoveryProjectionRejected("invalid exact recovery projection input")
    originals = tuple(steps)
    try:
        retained = tuple(
            (step.step_id, step.operation, step.depends_on, step.state,
             step.result_sha256)
            for step in originals
        )

        def unchanged() -> None:
            _require_original_protocol()
            if len(steps) != len(originals) or any(
                step is not original
                or any(
                    current is not expected
                    for current, expected in zip(
                        (step.step_id, step.operation, step.depends_on,
                         step.state, step.result_sha256), values, strict=True,
                    )
                )
                for step, original, values in zip(
                    steps, originals, retained, strict=True,
                )
            ):
                raise ReadRecoveryProjectionRejected(
                    "recovery projection input changed between reviews"
                )

        unchanged()
        read = _ORIGINAL_SCHEDULE(request_id, steps)
        unchanged()
        mixed_steps = tuple(
            OfflineRecoveryStepClaim(
                step_id=name,
                effect="READ",
                depends_on=deps,
                state=_STATE.get(state, state),
                result_sha256=digest,
            )
            for name, _operation, deps, state, digest in retained
        )
        mixed = _ORIGINAL_FENCE(plan_id, mixed_steps)
        unchanged()
        if (
            read.dispatch_authorized is not False
            or read.automatic_replay_authorized is not False
            or read.external_outcome_verified is not False
            or mixed.dispatch_authorized is not False
            or mixed.automatic_replay_authorized is not False
            or mixed.write_authorized is not False
            or mixed.external_outcome_verified is not False
        ):
            raise ReadRecoveryProjectionRejected("recovery source claimed authority")
        read_codes = tuple((d.step_id, d.disposition) for d in read.decisions)
        mixed_codes = tuple((d.step_id, d.code) for d in mixed.decisions)
        if (
            len(read_codes) != len(retained)
            or len(mixed_codes) != len(retained)
            or any(
                name != original[0]
                or mapped not in _CODES
                or (name, _CODES[mapped]) != actual
                for (name, mapped), actual, original in zip(
                    read_codes, mixed_codes, retained, strict=True,
                )
            )
        ):
            raise ReadRecoveryProjectionRejected(
                "independent recovery classifiers disagree"
            )
        ready = tuple(name for name, code in read_codes if code == "READY_MOCK_ONLY")
        payload = json.dumps(
            (request_id, plan_id, read.schedule_digest, mixed.digest, ready),
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
        if len(payload) > 8192:
            raise ReadRecoveryProjectionRejected("recovery projection exceeds budget")
        _require_original_protocol()
        review_sha256 = hashlib.sha256(_DOMAIN + payload).hexdigest()
        unchanged()
        report = _RESULT(
            request_id, plan_id, read.schedule_digest, mixed.digest,
            ready, review_sha256,
        )
        _require_original_protocol()
        if (
            type(report) is not _RESULT
            or any(
                getattr(report, field) is not expected
                for field, expected in zip(
                    _FIELDS,
                    (request_id, plan_id, read.schedule_digest, mixed.digest,
                     ready, review_sha256),
                    strict=True,
                )
            )
            or any(getattr(report, flag) is not False for flag in _DENIALS)
        ):
            raise ReadRecoveryProjectionRejected("invalid inert projection result")
        unchanged()
        return report
    except (DetachedReadRecoveryRejected, OfflineRecoveryFenceRejected) as exc:
        raise ReadRecoveryProjectionRejected(
            "recovery projection source rejected supplied history"
        ) from exc
