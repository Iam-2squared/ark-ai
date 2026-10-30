"""Authorization-gated preflight boundary for V3 experiment 001.

No cloud provisioning, model download, or training occurs in this module. The real
GPU implementation is dependency-injected and cannot be reached with an unresolved
or unauthorized execution snapshot.
"""

from __future__ import annotations

import math
import re
from dataclasses import asdict, dataclass
from typing import Protocol

from .execution import (
    canonical_json,
    execution_core_sha256,
    sha256_bytes,
    validate_experiment_001,
)
from .runtime_guard import RuntimeIdentity, verify_runtime_identity


@dataclass(frozen=True)
class PreflightEvidence:
    device: str
    vram_gib: float
    base_loaded: bool
    tokenizer_probe_sha256: str
    forward_backward_ok: bool
    optimizer_step_ok: bool
    peak_vram_mib: float
    peak_reserved_vram_mib: float
    wall_seconds: float
    runtime_error: str | None = None

    def validate(self) -> None:
        if not isinstance(self.device, str) or not self.device.strip():
            raise ValueError("valid accelerator identity required")
        for name in ("vram_gib", "peak_vram_mib", "peak_reserved_vram_mib", "wall_seconds"):
            value = getattr(self, name)
            message = "finite positive preflight measurements required"
            if type(value) not in (int, float):
                raise ValueError(message)
            try:
                measured = float(value)
            except (OverflowError, ValueError) as exc:
                raise ValueError(message) from exc
            if not math.isfinite(measured) or measured <= 0:
                raise ValueError(message)
        if any(
            value is not True
            for value in (self.base_loaded, self.forward_backward_ok, self.optimizer_step_ok)
        ):
            raise ValueError("preflight mechanics did not complete")
        if (
            not isinstance(self.tokenizer_probe_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.tokenizer_probe_sha256) is None
        ):
            raise ValueError("tokenizer probe SHA-256 required")
        if self.runtime_error is not None:
            raise ValueError("preflight runtime failure")


_EVIDENCE_TYPE = PreflightEvidence
_IDENTITY_TYPE = RuntimeIdentity
_EVIDENCE_FIELDS = tuple(PreflightEvidence.__dataclass_fields__)
_IDENTITY_FIELDS = tuple(RuntimeIdentity.__dataclass_fields__)


def _pin_json_tree(value: object, depth: int = 0) -> tuple:
    """Retain original execution-snapshot carriers, including nested scalars.

    This is a callback-epoch guard, not a signature or authorization grant.
    """
    if depth > 16:
        raise ValueError("preflight snapshot exceeds review depth")
    if type(value) is dict:
        if len(value) > 128:
            raise ValueError("preflight snapshot exceeds review object budget")
        return (
            value, "object",
            tuple(
                (key, _pin_json_tree(item, depth + 1))
                for key, item in value.items()
            ),
        )
    if type(value) is list:
        if len(value) > 256:
            raise ValueError("preflight snapshot exceeds review array budget")
        return (
            value, "array",
            tuple(_pin_json_tree(item, depth + 1) for item in value),
        )
    return value, "scalar", None


def _assert_json_tree_epoch(value: object, pinned: tuple) -> None:
    original, kind, children = pinned
    if value is not original:
        raise ValueError("preflight snapshot changed during evidence binding")
    if kind == "object":
        if type(value) is not dict or len(value) != len(children):
            raise ValueError("preflight snapshot mapping changed")
        for (current_key, current), (key, child) in zip(
            value.items(), children, strict=True,
        ):
            if current_key is not key:
                raise ValueError("preflight snapshot key carrier changed")
            _assert_json_tree_epoch(current, child)
    elif kind == "array":
        if type(value) is not list or len(value) != len(children):
            raise ValueError("preflight snapshot array changed")
        for current, child in zip(value, children, strict=True):
            _assert_json_tree_epoch(current, child)


class PreflightBackend(Protocol):
    def run(self, snapshot: dict) -> PreflightEvidence: ...


class DisabledRealPreflightBackend:
    def run(self, snapshot: dict) -> PreflightEvidence:
        raise RuntimeError("real GPU preflight backend is not installed/authorized")


def verify_preflight_measurements(
    snapshot: dict,
    evidence: PreflightEvidence,
    runtime_identity: RuntimeIdentity,
) -> None:
    """Bind non-Candidate evidence to the same measured, frozen execution.

    This is validation only: no GPU calls, model loading, training or billing.
    The caller's report remains non-authoritative without an independently
    authorized snapshot and retained evidence bytes.
    """
    evidence.validate()
    verify_runtime_identity(snapshot, runtime_identity)
    if evidence.device != runtime_identity.device:
        raise ValueError("preflight device does not match measured runtime")
    if abs(float(evidence.vram_gib) - float(runtime_identity.vram_gib)) > 0.05:
        raise ValueError("preflight VRAM does not match measured runtime")
    if evidence.tokenizer_probe_sha256 != snapshot["tokenizer"]["chat_template_probe_sha256"]:
        raise ValueError("preflight tokenizer probe does not match frozen snapshot")
    if evidence.peak_vram_mib > evidence.peak_reserved_vram_mib:
        raise ValueError("preflight allocated VRAM exceeds reserved VRAM")
    measured_capacity_mib = float(runtime_identity.vram_gib) * 1024
    if not math.isfinite(measured_capacity_mib):
        raise ValueError("preflight measured GPU capacity conversion overflow")
    if evidence.peak_reserved_vram_mib > measured_capacity_mib:
        raise ValueError("preflight reserved VRAM exceeds measured GPU capacity")
    budget_seconds = float(snapshot["budget"]["wall_clock_timeout_minutes"]) * 60
    if not math.isfinite(budget_seconds):
        raise ValueError("preflight frozen wall-clock budget conversion overflow")
    if evidence.wall_seconds > budget_seconds:
        raise ValueError("preflight wall time exceeds frozen execution budget")


def build_preflight_report(
    snapshot: dict,
    evidence: PreflightEvidence,
    runtime_identity: RuntimeIdentity,
) -> bytes:
    """Create a non-authorizing report bound to one unchanged input epoch."""
    if (
        type(snapshot) is not dict
        or type(evidence) is not _EVIDENCE_TYPE
        or type(runtime_identity) is not _IDENTITY_TYPE
    ):
        raise ValueError("exact preflight report input types required")
    snapshot_epoch = _pin_json_tree(snapshot)
    evidence_epoch = tuple(getattr(evidence, name) for name in _EVIDENCE_FIELDS)
    identity_epoch = tuple(getattr(runtime_identity, name) for name in _IDENTITY_FIELDS)

    def assert_epoch() -> None:
        _assert_json_tree_epoch(snapshot, snapshot_epoch)
        try:
            stable = (
                type(evidence) is _EVIDENCE_TYPE
                and type(runtime_identity) is _IDENTITY_TYPE
                and all(
                    getattr(evidence, name) is value
                    for name, value in zip(
                        _EVIDENCE_FIELDS, evidence_epoch, strict=True,
                    )
                )
                and all(
                    getattr(runtime_identity, name) is value
                    for name, value in zip(
                        _IDENTITY_FIELDS, identity_epoch, strict=True,
                    )
                )
            )
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("preflight result input epoch invalid") from exc
        if not stable:
            raise ValueError("preflight result input epoch changed")

    assert_epoch()
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="preflight")
    assert_epoch()
    verify_preflight_measurements(snapshot, evidence, runtime_identity)
    assert_epoch()
    core_sha = execution_core_sha256(snapshot)
    assert_epoch()
    identity_dict = asdict(runtime_identity)
    assert_epoch()
    evidence_dict = asdict(evidence)
    assert_epoch()
    report = {
        "schema_version": 1,
        "kind": "NON_CANDIDATE_PREFLIGHT",
        "execution_snapshot_sha256": snapshot_sha,
        "execution_core_sha256": core_sha,
        "runtime_identity": identity_dict,
        "evidence": evidence_dict,
        "candidate_created": False,
        "validation_opened": False,
        "historical_v2_opened": False,
        "full_training_authorized": False,
    }
    payload = canonical_json(report)
    assert_epoch()
    return payload


def preflight_report_sha256(
    snapshot: dict,
    evidence: PreflightEvidence,
    runtime_identity: RuntimeIdentity,
) -> str:
    return sha256_bytes(build_preflight_report(snapshot, evidence, runtime_identity))


def run_authorized_preflight(snapshot: dict, backend: PreflightBackend) -> PreflightEvidence:
    """Run only after exact identities and preflight compute authorization are frozen.

    This remains a non-Candidate mechanics test. The preflight authorization scope
    explicitly forbids treating the same approval as permission for the full Candidate run.
    """
    validate_experiment_001(snapshot, authorization_scope="preflight")
    evidence = backend.run(snapshot)
    evidence.validate()
    return evidence
