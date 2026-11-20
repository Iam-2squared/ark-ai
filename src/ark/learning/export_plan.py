"""Deterministic, non-executing paired-Q4 export plan for V3 experiment 001."""

from __future__ import annotations

import os
import stat
from dataclasses import asdict, dataclass
from pathlib import Path

from .execution import canonical_json, sha256_bytes, validate_experiment_001
from .identity import build_tool_identity

_PATH_MAX_BYTES = 4096
_ORIGINAL_PATH_FACTORY = Path
_ORIGINAL_PATH_TYPE = type(Path("."))
_ORIGINAL_PATH_FSPATH = _ORIGINAL_PATH_TYPE.__fspath__
_ORIGINAL_FSENCODE = os.fsencode
_ORIGINAL_OS_FSPATH = os.fspath
_ORIGINAL_OS_LSTAT = os.lstat
_ORIGINAL_OS_STAT = os.stat
_ORIGINAL_OS_GETCWD = os.getcwd
_ORIGINAL_OS_PATH = os.path
_PATH_OS_PATH_NAMES = ("abspath", "join", "realpath")
_ORIGINAL_PATH_OS_PATH_NAMES = _PATH_OS_PATH_NAMES
_ORIGINAL_PATH_OS_PATH_FUNCTIONS = tuple(
    getattr(_ORIGINAL_OS_PATH, name) for name in _PATH_OS_PATH_NAMES
)
_PATH_METHOD_NAMES = (
    "__fspath__", "absolute", "exists", "is_dir", "is_relative_to",
    "lstat", "resolve", "name", "parent", "parents", "parts",
)
_ORIGINAL_PATH_METHOD_NAMES = _PATH_METHOD_NAMES
_ORIGINAL_PATH_METHODS = tuple(
    getattr(_ORIGINAL_PATH_TYPE, name) for name in _PATH_METHOD_NAMES
)
_ORIGINAL_PATH_MAX_BYTES = _PATH_MAX_BYTES


def _require_original_path_codec(label: str) -> None:
    """Pin the filesystem-path codec before os.fsencode invokes __fspath__."""
    if (
        Path is not _ORIGINAL_PATH_FACTORY
        or _ORIGINAL_PATH_TYPE.__fspath__ is not _ORIGINAL_PATH_FSPATH
        or os.fsencode is not _ORIGINAL_FSENCODE
        or os.fspath is not _ORIGINAL_OS_FSPATH
    ):
        raise ValueError(f"{label} path inspection dependencies changed")


def _require_original_path_contract(label: str) -> None:
    """Pin filesystem inspection methods before any path I/O."""
    if (
        Path is not _ORIGINAL_PATH_FACTORY
        or _PATH_METHOD_NAMES is not _ORIGINAL_PATH_METHOD_NAMES
        or _PATH_OS_PATH_NAMES is not _ORIGINAL_PATH_OS_PATH_NAMES
        or any(
            getattr(_ORIGINAL_PATH_TYPE, name) is not original
            for name, original in zip(
                _PATH_METHOD_NAMES, _ORIGINAL_PATH_METHODS, strict=True,
            )
        )
        or os.fsencode is not _ORIGINAL_FSENCODE
        or os.fspath is not _ORIGINAL_OS_FSPATH
        or os.lstat is not _ORIGINAL_OS_LSTAT
        or os.stat is not _ORIGINAL_OS_STAT
        or os.getcwd is not _ORIGINAL_OS_GETCWD
        or os.path is not _ORIGINAL_OS_PATH
        or any(
            getattr(_ORIGINAL_OS_PATH, name) is not original
            for name, original in zip(
                _PATH_OS_PATH_NAMES, _ORIGINAL_PATH_OS_PATH_FUNCTIONS, strict=True,
            )
        )
        or type(_PATH_MAX_BYTES) is not int
        or _PATH_MAX_BYTES != _ORIGINAL_PATH_MAX_BYTES
    ):
        raise ValueError(f"{label} path inspection dependencies changed")


def _exact_local_path(value: object, *, label: str) -> Path:
    """Reject path subclasses and oversized native encodings before path I/O."""
    _require_original_path_codec(label)
    if type(value) is not _ORIGINAL_PATH_TYPE:
        raise ValueError(f"{label} must be an exact local pathlib.Path")
    try:
        encoded = os.fsencode(value)
    except (OSError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError(f"{label} path cannot be safely encoded") from exc
    if (
        type(encoded) is not bytes
        or not encoded
        or b"\x00" in encoded
        or len(encoded) > _PATH_MAX_BYTES
    ):
        raise ValueError(f"{label} path exceeds native byte budget")
    _require_original_path_contract(label)
    return value


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
    value = _exact_local_path(path, label=f"{label} input")
    if (
        ".." in value.parts
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
    output = _exact_local_path(output_dir, label="export output")
    base_dir = _exact_local_path(base_dir, label="base input")
    merged_candidate_dir = _exact_local_path(
        merged_candidate_dir, label="merged Candidate input",
    )
    if current_model_path is not None:
        current_model_path = _exact_local_path(
            current_model_path, label="Current deployed model",
        )
    if (
        ".." in output.parts
        or output.name in ("", ".", "..")
        or _has_symlink_or_reparse_ancestor(output)
    ):
        raise ValueError("export output requires a new directory under safe parents")
    # lstat the leaf only after every ancestor has passed no-follow inspection.
    # Unlike exists(), this also detects a dangling final symlink without
    # following it through an otherwise safe parent chain.
    try:
        output.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise ValueError("export output leaf cannot be safely inspected") from exc
    else:
        raise ValueError("export output requires a new directory under safe parents")
    if not output.parent.is_dir():
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
    # Reject path subclasses and over-budget native encodings before snapshot
    # callbacks, filesystem probes, or converter/quantizer identity reads.
    base_dir = _exact_local_path(base_dir, label="base input")
    merged_candidate_dir = _exact_local_path(
        merged_candidate_dir, label="merged Candidate input",
    )
    converter_path = _exact_local_path(converter_path, label="converter")
    quantizer_path = _exact_local_path(quantizer_path, label="quantizer")
    output_dir = _exact_local_path(output_dir, label="export output")
    if current_model_path is not None:
        current_model_path = _exact_local_path(
            current_model_path, label="Current deployed model",
        )
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
