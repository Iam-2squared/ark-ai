"""Runtime identity and wall-time guards for V3 experiment 001.

Collection is local-only and occurs only inside an already-authorized GPU runtime.
No provider API, cloud provisioning, model download, or billing action is performed here.
"""

from __future__ import annotations

import importlib.metadata
import math
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

    def validate(self) -> None:
        text_fields = (
            "os_or_image_digest",
            "python",
            "torch",
            "transformers",
            "peft",
            "accelerate",
            "cuda_runtime",
            "device",
            "driver",
        )
        for field in text_fields:
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise RuntimeIdentityMismatch(
                    f"invalid measured runtime identity for {field}"
                )
        if type(self.vram_gib) not in (int, float) or self.vram_gib <= 0:
            raise RuntimeIdentityMismatch("invalid measured GPU VRAM identity")
        try:
            measured_vram = float(self.vram_gib)
        except (OverflowError, ValueError) as exc:
            raise RuntimeIdentityMismatch("invalid measured GPU VRAM identity") from exc
        if not math.isfinite(measured_vram) or not math.isfinite(measured_vram * 1024.0):
            raise RuntimeIdentityMismatch("invalid measured GPU VRAM identity")


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
    actual.validate()
    if type(vram_tolerance_gib) not in (int, float):
        raise ValueError("finite non-negative VRAM tolerance required")
    try:
        tolerance = float(vram_tolerance_gib)
    except (OverflowError, ValueError) as exc:
        raise ValueError("finite non-negative VRAM tolerance required") from exc
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("finite non-negative VRAM tolerance required")

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
        expected = expected_environment[field]
        if not isinstance(expected, str) or not expected.strip():
            raise RuntimeIdentityMismatch(f"invalid frozen runtime identity for {field}")
        observed = getattr(actual, field)
        if observed != expected:
            raise RuntimeIdentityMismatch(
                f"runtime identity mismatch for {field}: "
                f"expected {expected!r}, observed {observed!r}"
            )

    expected_hardware = snapshot["hardware"]
    expected_device = expected_hardware["device"]
    expected_driver = expected_hardware["driver"]
    if not isinstance(expected_device, str) or not expected_device.strip():
        raise RuntimeIdentityMismatch("invalid frozen GPU device identity")
    if not isinstance(expected_driver, str) or not expected_driver.strip():
        raise RuntimeIdentityMismatch("invalid frozen GPU driver identity")
    if actual.device != expected_device:
        raise RuntimeIdentityMismatch("GPU device identity does not match frozen snapshot")
    if actual.driver != expected_driver:
        raise RuntimeIdentityMismatch("GPU driver identity does not match frozen snapshot")

    expected_vram = expected_hardware["vram_gib"]
    if type(expected_vram) not in (int, float) or expected_vram <= 0:
        raise RuntimeIdentityMismatch("invalid frozen GPU VRAM identity")
    try:
        expected_vram_float = float(expected_vram)
    except (OverflowError, ValueError) as exc:
        raise RuntimeIdentityMismatch("invalid frozen GPU VRAM identity") from exc
    if not math.isfinite(expected_vram_float):
        raise RuntimeIdentityMismatch("invalid frozen GPU VRAM identity")
    actual_vram = float(actual.vram_gib)
    if abs(actual_vram - expected_vram_float) > tolerance:
        raise RuntimeIdentityMismatch(
            f"GPU VRAM identity mismatch: expected {expected_vram_float:.3f} GiB, "
            f"observed {actual_vram:.3f} GiB"
        )


class WallTimeBudget:
    """Soft fail-closed wall-time guard checked at every controlled runtime boundary."""

    def __init__(self, timeout_minutes: float, *, started: float | None = None):
        message = "finite positive wall-clock timeout required"
        if type(timeout_minutes) not in (int, float):
            raise ValueError(message)
        try:
            minutes = float(timeout_minutes)
        except (OverflowError, ValueError) as exc:
            raise ValueError(message) from exc
        if not math.isfinite(minutes) or minutes <= 0:
            raise ValueError(message)
        seconds = minutes * 60.0
        if not math.isfinite(seconds):
            raise ValueError("wall-clock timeout seconds overflow")
        self.timeout_seconds = seconds
        if type(started) is bool:
            raise ValueError("finite wall-clock start required")
        try:
            measured_start = time.monotonic() if started is None else float(started)
        except (OverflowError, ValueError, TypeError) as exc:
            raise ValueError("finite wall-clock start required") from exc
        if not math.isfinite(measured_start):
            raise ValueError("finite wall-clock start required")
        self.started = measured_start

    def check(self, phase: str, *, now: float | None = None) -> None:
        if type(now) is bool:
            raise RuntimeError("finite wall-clock reading required")
        try:
            current = time.monotonic() if now is None else float(now)
        except (OverflowError, ValueError, TypeError) as exc:
            raise RuntimeError("finite wall-clock reading required") from exc
        if not math.isfinite(current):
            raise RuntimeError("finite wall-clock reading required")
        elapsed = current - self.started
        if not math.isfinite(elapsed):
            raise RuntimeError("finite wall-clock elapsed time required")
        if elapsed < 0:
            raise RuntimeError("monotonic clock moved backwards")
        if elapsed > self.timeout_seconds:
            raise RuntimeError(
                f"approved wall-clock timeout exceeded during {phase}: "
                f"{elapsed:.1f}s > {self.timeout_seconds:.1f}s"
            )
