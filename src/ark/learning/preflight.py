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
    wall_seconds: float
    runtime_error: str | None = None

    def validate(self) -> None:
        if not isinstance(self.device, str) or not self.device.strip():
            raise ValueError("valid accelerator identity required")
        for name in ("vram_gib", "peak_vram_mib", "wall_seconds"):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError("finite positive preflight measurements required")
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


class PreflightBackend(Protocol):
    def run(self, snapshot: dict) -> PreflightEvidence: ...


class DisabledRealPreflightBackend:
    def run(self, snapshot: dict) -> PreflightEvidence:
        raise RuntimeError("real GPU preflight backend is not installed/authorized")


def build_preflight_report(
    snapshot: dict,
    evidence: PreflightEvidence,
    runtime_identity: RuntimeIdentity,
) -> bytes:
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="preflight")
    evidence.validate()
    verify_runtime_identity(snapshot, runtime_identity)
    report = {
        "schema_version": 1,
        "kind": "NON_CANDIDATE_PREFLIGHT",
        "execution_snapshot_sha256": snapshot_sha,
        "execution_core_sha256": execution_core_sha256(snapshot),
        "runtime_identity": asdict(runtime_identity),
        "evidence": asdict(evidence),
        "candidate_created": False,
        "validation_opened": False,
        "historical_v2_opened": False,
        "full_training_authorized": False,
    }
    return canonical_json(report)


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
