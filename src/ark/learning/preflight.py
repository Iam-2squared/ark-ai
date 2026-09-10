"""Authorization-gated preflight boundary for V3 experiment 001.

No cloud provisioning, model download, or training occurs in this module. The real
GPU implementation is dependency-injected and cannot be reached with an unresolved
or unauthorized execution snapshot.
"""

from __future__ import annotations

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
        if not self.device.strip() or self.vram_gib <= 0 or self.peak_vram_mib <= 0:
            raise ValueError("valid accelerator measurements required")
        if not self.base_loaded or not self.forward_backward_ok or not self.optimizer_step_ok:
            raise ValueError("preflight mechanics did not complete")
        if len(self.tokenizer_probe_sha256) != 64:
            raise ValueError("tokenizer probe SHA-256 required")
        if self.wall_seconds <= 0 or self.runtime_error is not None:
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
