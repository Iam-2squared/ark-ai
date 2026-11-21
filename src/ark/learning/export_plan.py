"""Deterministic, non-executing paired-Q4 export plan for V3 experiment 001."""

from __future__ import annotations

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


_NATIVE_PATH_TYPE = type(Path("."))
_MAX_PYTHON_EXECUTABLE_BYTES = 4096
_ORIGINAL_MAX_PYTHON_EXECUTABLE_BYTES = _MAX_PYTHON_EXECUTABLE_BYTES
_MAX_EXPORT_PATH_BYTES = 4096
_ORIGINAL_MAX_EXPORT_PATH_BYTES = _MAX_EXPORT_PATH_BYTES
_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_REPARSE_POINT_ATTRIBUTE = _REPARSE_POINT_ATTRIBUTE
_SOURCE_TREE_ROOT = Path(__file__).resolve().parents[3]
_ORIGINAL_SOURCE_TREE_ROOT = _SOURCE_TREE_ROOT


def _require_export_path_constants() -> None:
    if (
        type(_MAX_EXPORT_PATH_BYTES) is not int
        or _MAX_EXPORT_PATH_BYTES is not _ORIGINAL_MAX_EXPORT_PATH_BYTES
        or type(_REPARSE_POINT_ATTRIBUTE) is not int
        or _REPARSE_POINT_ATTRIBUTE is not _ORIGINAL_REPARSE_POINT_ATTRIBUTE
        or _SOURCE_TREE_ROOT is not _ORIGINAL_SOURCE_TREE_ROOT
    ):
        raise ValueError("export path policy constants changed")


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
    if "\x00" in value:
        raise ValueError("python executable contains a NUL separator")
    if not value.strip() or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise ValueError("python executable contains blank or control text")
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


def _path_text_budget(path: Path, name: str) -> None:
    _require_export_path_constants()
    value = str(path)
    if "\x00" in value:
        raise ValueError(f"{name} contains a NUL separator")
    try:
        encoded = value.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8") from exc
    if len(encoded) > _MAX_EXPORT_PATH_BYTES:
        raise ValueError(f"{name} exceeds the bounded path budget")


def _is_reparse_point(info: object) -> bool:
    _require_export_path_constants()
    attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISLNK(info.st_mode) or (
        type(attributes) is int
        and bool(attributes & _REPARSE_POINT_ATTRIBUTE)
    )


def _reject_reparse_ancestors(path: Path, name: str) -> None:
    """Reject symlink and Windows reparse-point ancestors without following them."""
    for parent in path.parents:
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValueError(f"{name} ancestry cannot be verified") from exc
        if _is_reparse_point(info):
            raise ValueError(f"{name} has a symlink or reparse-point ancestor")


def _canonical_existing_directory(path: Path, name: str) -> Path:
    _require_native_path(path, name)
    _path_text_budget(path, name)
    if ".." in path.parts:
        raise ValueError(f"{name} may not contain parent traversal")
    _reject_reparse_ancestors(path, name)
    try:
        info = path.lstat()
        if not stat.S_ISDIR(info.st_mode) or _is_reparse_point(info):
            raise ValueError(f"{name} must be a real non-reparse directory")
        absolute = path.absolute()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{name} must be an existing canonical directory") from exc
    if resolved != absolute:
        raise ValueError(f"{name} resolves through a path alias")
    return resolved


def _canonical_existing_file(path: Path, name: str) -> Path:
    _require_native_path(path, name)
    _path_text_budget(path, name)
    if ".." in path.parts:
        raise ValueError(f"{name} may not contain parent traversal")
    _reject_reparse_ancestors(path, name)
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or _is_reparse_point(info)
            or info.st_nlink != 1
        ):
            raise ValueError(f"{name} must be one regular non-reparse file")
        absolute = path.absolute()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"{name} must be an existing canonical file") from exc
    if resolved != absolute:
        raise ValueError(f"{name} resolves through a path alias")
    return resolved


def _canonical_current_model_path(
    path: Path,
    *,
    require_existing: bool,
) -> Path:
    """Resolve a Current-model locator while refusing symlink/reparse aliases.

    The optional non-strict mode exists only for the private validation helper's
    lexical-collision tests. build_export_plan always requires an existing file.
    """
    _require_native_path(path, "current_model_path")
    _path_text_budget(path, "current_model_path")
    _reject_reparse_ancestors(path, "current_model_path")
    try:
        try:
            info = path.lstat()
        except FileNotFoundError:
            if require_existing:
                raise ValueError("Current deployed model must be an existing regular file") from None
        else:
            if not stat.S_ISREG(info.st_mode) or _is_reparse_point(info) or info.st_nlink != 1:
                raise ValueError("Current deployed model must be one regular non-reparse file")
        resolved = path.resolve(strict=require_existing)
    except (OSError, RuntimeError) as exc:
        raise ValueError("Current deployed model path cannot be safely resolved") from exc
    return resolved


def _canonical_output_path(path: Path) -> Path:
    _require_native_path(path, "output_dir")
    _path_text_budget(path, "export output")
    if (
        ".." in path.parts
        or path.name in ("", ".", "..")
    ):
        raise ValueError("export output may not contain traversal or an empty leaf")
    try:
        path.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ValueError("export output path cannot be inspected") from exc
    else:
        raise ValueError("export output requires a new directory under safe parents")
    parent = _canonical_existing_directory(path.parent, "export output parent")
    return parent / path.name


def _paths_overlap(left: Path, right: Path) -> bool:
    return (
        left == right
        or left.is_relative_to(right)
        or right.is_relative_to(left)
    )


def _canonicalize_export_paths(
    *,
    base_dir: Path,
    merged_candidate_dir: Path,
    output_dir: Path,
    converter_path: Path | None = None,
    quantizer_path: Path | None = None,
    current_model_path: Path | None = None,
    require_existing_model: bool = False,
) -> tuple[Path, Path, Path, Path | None, Path | None, Path | None]:
    """Return canonical, pairwise-separated paths without creating or executing anything."""
    _require_export_path_constants()
    base = _canonical_existing_directory(base_dir, "base_dir")
    merged = _canonical_existing_directory(merged_candidate_dir, "merged_candidate_dir")
    if _paths_overlap(base, merged):
        raise ValueError("base and merged Candidate directories must be canonically separated")

    output = _canonical_output_path(output_dir)
    source_root = _canonical_existing_directory(_SOURCE_TREE_ROOT, "repository source tree")
    protected_directories = (base, merged, source_root)
    if any(_paths_overlap(output, root) for root in protected_directories):
        raise ValueError(
            "export output overlaps a protected input tree "
            "(source tree or model source)"
        )

    current_model = None
    if current_model_path is not None:
        current_model = _canonical_current_model_path(
            current_model_path,
            require_existing=require_existing_model,
        )
        if current_model.is_relative_to(base) or current_model.is_relative_to(merged):
            raise ValueError("Current deployed model aliases a protected model source tree")
        planned_names = (
            "paired-current-f16.gguf",
            "paired-current-Q4_K_M.gguf",
            "candidate-f16.gguf",
            "candidate-Q4_K_M.gguf",
        )
        if any(current_model == output / name for name in planned_names):
            raise ValueError("Current deployed model path may never be an export output")
        if current_model.is_relative_to(output):
            raise ValueError("Current deployed model path overlaps the export output directory")

    converter = None
    quantizer = None
    if converter_path is not None:
        converter = _canonical_existing_file(converter_path, "converter_path")
    if quantizer_path is not None:
        quantizer = _canonical_existing_file(quantizer_path, "quantizer_path")
    if converter is not None and quantizer is not None and converter == quantizer:
        raise ValueError("converter and quantizer must be distinct canonical files")
    for name, tool in (("converter_path", converter), ("quantizer_path", quantizer)):
        if tool is None:
            continue
        if tool.is_relative_to(base) or tool.is_relative_to(merged):
            raise ValueError(f"{name} must be separate from model source trees")
        if current_model is not None and tool == current_model:
            raise ValueError(f"{name} must be separate from the Current deployed model")

    return base, merged, output, converter, quantizer, current_model


def _validate_export_output_path(
    output_dir: Path,
    *,
    base_dir: Path,
    merged_candidate_dir: Path,
    current_model_path: Path | None,
) -> None:
    """Validation-only export destination check; never creates or executes it.

    Reject input-tree overlap, path aliases, reparse-point ancestry and deployed
    model collisions. This is not an atomic dirfd traversal or hostile-writer defense.
    """
    _require_native_path(output_dir, "output_dir")
    _require_native_path(base_dir, "base_dir")
    _require_native_path(merged_candidate_dir, "merged_candidate_dir")
    if current_model_path is not None:
        _require_native_path(current_model_path, "current_model_path")
    _canonicalize_export_paths(
        base_dir=base_dir,
        merged_candidate_dir=merged_candidate_dir,
        output_dir=output_dir,
        current_model_path=current_model_path,
        require_existing_model=False,
    )


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
    base, merged, output, converter_path, quantizer_path, _ = _canonicalize_export_paths(
        base_dir=base_dir,
        merged_candidate_dir=merged_candidate_dir,
        output_dir=output_dir,
        converter_path=converter_path,
        quantizer_path=quantizer_path,
        current_model_path=current_model_path,
        require_existing_model=current_model_path is not None,
    )
    assert converter_path is not None and quantizer_path is not None
    snapshot_sha = validate_experiment_001(snapshot, authorization_scope="none")
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

    paired_f16 = output / "paired-current-f16.gguf"
    paired_q4 = output / "paired-current-Q4_K_M.gguf"
    candidate_f16 = output / "candidate-f16.gguf"
    candidate_q4 = output / "candidate-Q4_K_M.gguf"
    commands = (
        CommandSpec(
            "paired_current_convert",
            (
                python_executable,
                str(converter_path),
                str(base),
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
                str(merged),
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
        output_dir=str(output),
        commands=commands,
        candidate_q4km=str(candidate_q4),
        paired_current_q4km=str(paired_q4),
    )
