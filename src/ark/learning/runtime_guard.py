"""Runtime identity and wall-time guards for V3 experiment 001.

Collection is local-only and occurs only inside an already-authorized GPU runtime.
No provider API, cloud provisioning, model download, or billing action is performed here.
"""

from __future__ import annotations

import importlib.metadata
import os
import platform
import subprocess
import time
from dataclasses import dataclass


class RuntimeIdentityMismatch(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimeIdentity:
    os_or_image_digest: str
    python: str
    torch: str
    transformers: str
    peft: str
    accelerate: str
    cuda_runtime: str
    device: str
    vram_gib: float
    driver: str


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeIdentityMismatch(f"required package is not installed: {name}") from exc


def _driver_version() -> str:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=driver_version",
                "--format=csv,noheader,nounits",
                "--id=0",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeIdentityMismatch("unable to measure NVIDIA driver identity") from exc
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise RuntimeIdentityMismatch("expected exactly one visible GPU driver identity")
    return lines[0]


def collect_runtime_identity(torch) -> RuntimeIdentity:
    """Measure the actual already-provisioned runtime without touching the network."""
    image_digest = os.environ.get("ARK_V3_OS_IMAGE_DIGEST", "").strip()
    if not image_digest:
        raise RuntimeIdentityMismatch(
            "ARK_V3_OS_IMAGE_DIGEST must identify the approved OS/container image"
        )
    if not torch.cuda.is_available():
        raise RuntimeIdentityMismatch("CUDA GPU is unavailable")
    cuda_runtime = str(getattr(torch.version, "cuda", "") or "").strip()
    if not cuda_runtime:
        raise RuntimeIdentityMismatch("PyTorch CUDA runtime identity is unavailable")
    properties = torch.cuda.get_device_properties(0)
    return RuntimeIdentity(
        os_or_image_digest=image_digest,
        python=platform.python_version(),
        torch=str(torch.__version__),
        transformers=_package_version("transformers"),
        peft=_package_version("peft"),
        accelerate=_package_version("accelerate"),
        cuda_runtime=cuda_runtime,
        device=str(torch.cuda.get_device_name(0)),
        vram_gib=float(properties.total_memory / (1024**3)),
        driver=_driver_version(),
    )


def verify_runtime_identity(
    snapshot: dict,
    actual: RuntimeIdentity,
    *,
    vram_tolerance_gib: float = 0.05,
) -> None:
    """Require the measured runtime to match the user-reviewed execution snapshot."""
    expected_environment = snapshot["environment"]
    for field in (
        "os_or_image_digest",
        "python",
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "cuda_runtime",
    ):
        expected = str(expected_environment[field])
        observed = str(getattr(actual, field))
        if observed != expected:
            raise RuntimeIdentityMismatch(
                f"runtime identity mismatch for {field}: "
                f"expected {expected!r}, observed {observed!r}"
            )

    expected_hardware = snapshot["hardware"]
    if actual.device != str(expected_hardware["device"]):
        raise RuntimeIdentityMismatch("GPU device identity does not match frozen snapshot")
    if actual.driver != str(expected_hardware["driver"]):
        raise RuntimeIdentityMismatch("GPU driver identity does not match frozen snapshot")
    expected_vram = float(expected_hardware["vram_gib"])
    if abs(actual.vram_gib - expected_vram) > vram_tolerance_gib:
        raise RuntimeIdentityMismatch(
            f"GPU VRAM identity mismatch: expected {expected_vram:.3f} GiB, "
            f"observed {actual.vram_gib:.3f} GiB"
        )


class WallTimeBudget:
    """Soft fail-closed wall-time guard checked at every controlled runtime boundary."""

    def __init__(self, timeout_minutes: float, *, started: float | None = None):
        if isinstance(timeout_minutes, bool) or timeout_minutes <= 0:
            raise ValueError("positive wall-clock timeout required")
        self.timeout_seconds = float(timeout_minutes) * 60.0
        self.started = time.monotonic() if started is None else float(started)

    def check(self, phase: str, *, now: float | None = None) -> None:
        current = time.monotonic() if now is None else float(now)
        elapsed = current - self.started
        if elapsed < 0:
            raise RuntimeError("monotonic clock moved backwards")
        if elapsed > self.timeout_seconds:
            raise RuntimeError(
                f"approved wall-clock timeout exceeded during {phase}: "
                f"{elapsed:.1f}s > {self.timeout_seconds:.1f}s"
            )
