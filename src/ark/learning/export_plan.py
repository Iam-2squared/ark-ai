"""Deterministic, non-executing paired-Q4 export plan for V3 experiment 001."""

from __future__ import annotations

import os
import stat
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


_FILE_ATTRIBUTE_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_reparse_point(info: os.stat_result) -> bool:
    attributes = getattr(info, "st_file_attributes", 0)
    return (
        type(attributes) is int
        and bool(attributes & _FILE_ATTRIBUTE_REPARSE_POINT)
    )


def _has_symlink_or_reparse_ancestor(path: Path) -> bool:
    """Inspect path ancestors without following symlinks or Windows junctions."""
    for parent in path.parents:
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError("export path ancestor cannot be safely inspected") from exc
        if stat.S_ISLNK(info.st_mode) or _is_reparse_point(info):
            return True
    return False


def _canonical_input_directory(path: Path, *, label: str) -> Path:
    """Return one existing local input root without lexical or reparse aliases."""
    value = Path(path)
    if (
        ".." in value.parts
        or len(str(value)) > 4096
        or _has_symlink_or_reparse_ancestor(value)
    ):
        raise ValueError(f"{label} input must be a non-aliased local directory")
    try:
        info = value.lstat()
        if not stat.S_ISDIR(info.st_mode) or _is_reparse_point(info):
            raise ValueError(f"{label} input must be a non-aliased local directory")
        resolved = value.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{label} input directory cannot be safely resolved") from exc
    if not resolved.is_dir():
        raise ValueError(f"{label} input must resolve to a directory")
    return resolved


def _validate_export_output_path(
    output_dir: Path,
    *,
    base_dir: Path,
    merged_candidate_dir: Path,
    current_model_path: Path | None,
) -> None:
    """Validate paired source/destination separation; never creates or executes.

    This is local path admission, not atomic directory-handle custody or a
    guarantee against a hostile concurrent filesystem writer.
    """
    output = Path(output_dir)
    if (
        ".." in output.parts
        or len(str(output)) > 4096
        or output.name in ("", ".", "..")
        or output.exists()
        or output.is_symlink()
        or not output.parent.is_dir()
        or _has_symlink_or_reparse_ancestor(output)
    ):
        raise ValueError("export output requires a new directory under safe parents")
    try:
        base_root = _canonical_input_directory(base_dir, label="base")
        candidate_root = _canonical_input_directory(
            merged_candidate_dir, label="merged Candidate",
        )
        if (
            base_root == candidate_root
            or base_root.is_relative_to(candidate_root)
            or candidate_root.is_relative_to(base_root)
        ):
            raise ValueError(
                "base and merged Candidate input trees must be distinct and non-overlapping"
            )

        resolved_parent = output.parent.resolve(strict=True)
        if resolved_parent != output.parent.absolute():
            raise ValueError("export output parent resolves through an alias")
        candidate_dir = resolved_parent / output.name
        if any(
            candidate_dir.is_relative_to(root)
            for root in (base_root, candidate_root)
        ):
            raise ValueError("export output overlaps protected input tree")
        if current_model_path is not None:
            deployed = Path(current_model_path).resolve(strict=False)
            if (
                deployed == candidate_root
                or deployed.is_relative_to(candidate_root)
                or (
                    deployed.exists()
                    and deployed.is_dir()
                    and candidate_root.is_relative_to(deployed)
                )
            ):
                raise ValueError(
                    "merged Candidate source overlaps Current deployed model"
                )
            names = (
                "paired-current-f16.gguf", "paired-current-Q4_K_M.gguf",
                "candidate-f16.gguf", "candidate-Q4_K_M.gguf",
            )
            if any(deployed == candidate_dir / name for name in names):
                raise ValueError("Current deployed model path may never be an export output")
    except (OSError, RuntimeError) as exc:
        raise ValueError("export path cannot be safely resolved") from exc


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
