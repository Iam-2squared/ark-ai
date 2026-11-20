"""Deterministic, non-executing paired-Q4 export plan for V3 experiment 001."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from .execution import canonical_json, sha256_bytes, validate_experiment_001
from .identity import build_tool_identity


@dataclass(frozen=True)
class CommandSpec:
    role: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class ExportPlan:
    execution_snapshot_sha256: str
    output_dir: str
    commands: tuple[CommandSpec, ...]
    candidate_q4km: str
    paired_current_q4km: str
    quantization: str = "Q4_K_M"
    schema_version: int = 1

    def canonical_bytes(self) -> bytes:
        return canonical_json(asdict(self))

    @property
    def sha256(self) -> str:
        return sha256_bytes(self.canonical_bytes())


_NATIVE_PATH_TYPE = type(Path("."))
_MAX_PYTHON_EXECUTABLE_BYTES = 4096
_ORIGINAL_MAX_PYTHON_EXECUTABLE_BYTES = _MAX_PYTHON_EXECUTABLE_BYTES


def _require_python_executable(value: object) -> str:
    """Bound the exact argv carrier before snapshot or file-identity work.

    The plan is data only, but its first argv element is intended for a later
    non-shell subprocess boundary. Keep it an exact, bounded UTF-8 string and
    preserve it verbatim; never coerce a caller-owned object with __str__.
    """
    if (
        type(_MAX_PYTHON_EXECUTABLE_BYTES) is not int
        or _MAX_PYTHON_EXECUTABLE_BYTES is not _ORIGINAL_MAX_PYTHON_EXECUTABLE_BYTES
    ):
        raise ValueError("python executable byte budget changed")
    if type(value) is not str:
        raise ValueError("python executable must be an exact non-empty string")
    if not 1 <= len(value) <= _MAX_PYTHON_EXECUTABLE_BYTES:
        raise ValueError("python executable exceeds the bounded identity budget")
    if not value.strip() or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise ValueError("python executable contains blank or control text")
    if "\x00" in value:
        raise ValueError("python executable contains a NUL separator")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("python executable must be valid UTF-8") from exc
    if len(encoded) > _MAX_PYTHON_EXECUTABLE_BYTES:
        raise ValueError("python executable exceeds the bounded identity budget")
    return value


def _require_native_path(value: object, name: str) -> Path:
    """Reject caller-owned PathLike callbacks before pathlib invokes __fspath__."""
    if type(value) is not _NATIVE_PATH_TYPE:
        raise ValueError(f"{name} must be an exact native Path")
    return value


def _require_export_path_inputs(
    *,
    base_dir: object,
    merged_candidate_dir: object,
    converter_path: object,
    quantizer_path: object,
    output_dir: object,
    current_model_path: object | None,
) -> None:
    for name, value in (
        ("base_dir", base_dir),
        ("merged_candidate_dir", merged_candidate_dir),
        ("converter_path", converter_path),
        ("quantizer_path", quantizer_path),
        ("output_dir", output_dir),
    ):
        _require_native_path(value, name)
    if current_model_path is not None:
        _require_native_path(current_model_path, "current_model_path")


def _validate_export_output_path(
    output_dir: Path,
    *,
    base_dir: Path,
    merged_candidate_dir: Path,
    current_model_path: Path | None,
) -> None:
    """Validation-only export destination check; never creates or executes it.

    Reject input-tree overlap, aliasing and deployed-model identity collisions.
    This is a preflight path check, not an OS-handle/TOCTOU-proof guarantee.
    """
    _require_export_path_inputs(
        base_dir=base_dir,
        merged_candidate_dir=merged_candidate_dir,
        converter_path=Path("."),
        quantizer_path=Path("."),
        output_dir=output_dir,
        current_model_path=current_model_path,
    )
    output = output_dir
    if (
        ".." in output.parts
        or len(str(output)) > 4096
        or output.name in ("", ".", "..")
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
        or any(parent.is_symlink() for parent in output.parents)
    ):
        raise ValueError("export output requires a new directory under safe parents")
    try:
        resolved_parent = output.parent.resolve(strict=True)
        if resolved_parent != output.parent.absolute():
            raise ValueError("export output parent resolves through an alias")
        candidate_dir = resolved_parent / output.name
        protected_dirs = (
            base_dir.resolve(strict=False),
            merged_candidate_dir.resolve(strict=False),
        )
        if any(candidate_dir.is_relative_to(root) for root in protected_dirs):
            raise ValueError("export output overlaps protected input tree")
        if current_model_path is not None:
            deployed = current_model_path.resolve(strict=False)
            names = (
                "paired-current-f16.gguf", "paired-current-Q4_K_M.gguf",
                "candidate-f16.gguf", "candidate-Q4_K_M.gguf",
            )
            if any(deployed == candidate_dir / name for name in names):
                raise ValueError("Current deployed model path may never be an export output")
    except (OSError, RuntimeError) as exc:
        raise ValueError("export output path cannot be safely resolved") from exc


def build_export_plan(
    snapshot: dict,
    *,
    base_dir: Path,
    merged_candidate_dir: Path,
    converter_path: Path,
    quantizer_path: Path,
    output_dir: Path,
    python_executable: str = "python",
    current_model_path: Path | None = None,
) -> ExportPlan:
    """Build commands only. No subprocess, conversion, quantization, or file write occurs."""
    _require_export_path_inputs(
        base_dir=base_dir,
        merged_candidate_dir=merged_candidate_dir,
        converter_path=converter_path,
        quantizer_path=quantizer_path,
        output_dir=output_dir,
        current_model_path=current_model_path,
    )
    python_executable = _require_python_executable(python_executable)
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="none")
    # Resolve output custody before hashing converter/quantizer input bytes.
    _validate_export_output_path(
        output_dir, base_dir=base_dir,
        merged_candidate_dir=merged_candidate_dir,
        current_model_path=current_model_path,
    )
    revision = snapshot["export"]["llama_cpp_revision"]
    converter = build_tool_identity(
        converter_path,
        git_revision=revision,
        role="hf_to_gguf_converter",
    )
    quantizer = build_tool_identity(
        quantizer_path,
        git_revision=revision,
        role="quantizer",
    )
    if converter["identity_sha256"] != snapshot["export"]["converter_identity"]:
        raise ValueError("converter bytes/revision do not match execution snapshot")
    if quantizer["identity_sha256"] != snapshot["export"]["quantizer_identity"]:
        raise ValueError("quantizer bytes/revision do not match execution snapshot")

    paired_f16 = output_dir / "paired-current-f16.gguf"
    paired_q4 = output_dir / "paired-current-Q4_K_M.gguf"
    candidate_f16 = output_dir / "candidate-f16.gguf"
    candidate_q4 = output_dir / "candidate-Q4_K_M.gguf"
    commands = (
        CommandSpec(
            "paired_current_convert",
            (
                python_executable,
                str(converter_path),
                str(base_dir),
                "--outfile",
                str(paired_f16),
                "--outtype",
                "f16",
            ),
        ),
        CommandSpec(
            "paired_current_quantize",
            (str(quantizer_path), str(paired_f16), str(paired_q4), "Q4_K_M"),
        ),
        CommandSpec(
            "candidate_convert",
            (
                python_executable,
                str(converter_path),
                str(merged_candidate_dir),
                "--outfile",
                str(candidate_f16),
                "--outtype",
                "f16",
            ),
        ),
        CommandSpec(
            "candidate_quantize",
            (str(quantizer_path), str(candidate_f16), str(candidate_q4), "Q4_K_M"),
        ),
    )
    return ExportPlan(
        execution_snapshot_sha256=snapshot_sha,
        output_dir=str(output_dir),
        commands=commands,
        candidate_q4km=str(candidate_q4),
        paired_current_q4km=str(paired_q4),
    )
