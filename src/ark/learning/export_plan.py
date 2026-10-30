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
    output = Path(output_dir)
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
            Path(base_dir).resolve(strict=False),
            Path(merged_candidate_dir).resolve(strict=False),
        )
        if any(candidate_dir.is_relative_to(root) for root in protected_dirs):
            raise ValueError("export output overlaps protected input tree")
        if current_model_path is not None:
            deployed = Path(current_model_path).resolve(strict=False)
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
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="none")
    # Resolve output custody before hashing converter/quantizer input bytes.
    output_dir = Path(output_dir)
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
