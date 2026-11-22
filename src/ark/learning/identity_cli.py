"""Offline-only identity capture for V3 execution-snapshot closure."""

from __future__ import annotations

import argparse
import os
import stat
from pathlib import Path

from .execution import canonical_json, sha256_bytes
from .identity import build_code_tree_identity, build_hf_snapshot_identity, build_tool_identity

_MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
_REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_ORIGINAL_REPARSE_POINT_ATTRIBUTE = _REPARSE_POINT_ATTRIBUTE
_ORIGINAL_STAT = stat
_ORIGINAL_S_ISDIR = stat.S_ISDIR
_ORIGINAL_S_ISREG = stat.S_ISREG
_ORIGINAL_S_ISLNK = stat.S_ISLNK
_ORIGINAL_FSTAT = os.fstat


def _require_original_stat_policy() -> None:
    if (
        stat is not _ORIGINAL_STAT
        or _ORIGINAL_STAT.S_ISDIR is not _ORIGINAL_S_ISDIR
        or _ORIGINAL_STAT.S_ISREG is not _ORIGINAL_S_ISREG
        or _ORIGINAL_STAT.S_ISLNK is not _ORIGINAL_S_ISLNK
        or os.fstat is not _ORIGINAL_FSTAT
        or type(_REPARSE_POINT_ATTRIBUTE) is not int
        or _REPARSE_POINT_ATTRIBUTE != _ORIGINAL_REPARSE_POINT_ATTRIBUTE
    ):
        raise ValueError("identity output stat policy changed")


def _is_directory(info: object) -> bool:
    _require_original_stat_policy()
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise ValueError("identity parent mode is malformed")
    return _ORIGINAL_S_ISDIR(mode)


def _is_regular_file(info: object) -> bool:
    _require_original_stat_policy()
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise ValueError("identity output mode is malformed")
    return _ORIGINAL_S_ISREG(mode)


def _is_reparse_point(info: object) -> bool:
    _require_original_stat_policy()
    attributes = getattr(info, "st_file_attributes", 0)
    _require_original_stat_policy()
    if type(attributes) is not int:
        raise ValueError("identity output reparse metadata is malformed")
    mode = info.st_mode
    _require_original_stat_policy()
    if type(mode) is not int:
        raise ValueError("identity output mode is malformed")
    return _ORIGINAL_S_ISLNK(mode) or bool(
        attributes & _REPARSE_POINT_ATTRIBUTE
    )


def _path_lstat(path: Path):
    _require_original_stat_policy()
    info = path.lstat()
    _require_original_stat_policy()
    return info


def _file_identity(info: object) -> tuple[int, int, int]:
    values = (info.st_dev, info.st_ino, info.st_size, info.st_nlink)
    if any(type(value) is not int or value < 0 for value in values):
        raise ValueError("identity output file identity is malformed")
    if values[3] != 1:
        raise ValueError("identity output must not be hard-linked")
    return values[:3]


def _require_nonreparse_ancestors(path: Path) -> None:
    for parent in path.parents:
        info = _path_lstat(parent)
        if not _is_directory(info) or _is_reparse_point(info):
            raise ValueError("identity output parent must not be a symlink or reparse point")


def _write_new_json(path: Path, payload: dict) -> str:
    _require_original_stat_policy()
    path = Path(path)
    _require_original_stat_policy()
    # Exclusive creation protects the final file, but not a parent path
    # replaced after inspection. Recheck every ancestor and the open handle.
    if (
        ".." in path.parts
        or len(str(path)) > 4096
        or path.name in ("", ".", "..")
    ):
        raise ValueError("identity output must be a new file under an existing directory")
    _require_nonreparse_ancestors(path)
    try:
        _path_lstat(path)
    except FileNotFoundError:
        pass
    else:
        raise ValueError("identity output must be a new file under an existing directory")
    data = canonical_json(payload)
    _require_original_stat_policy()
    try:
        with path.open("xb") as handle:
            # A reentrant open callback must not change file classification
            # before the first identity-artifact byte is written.
            _require_original_stat_policy()
            opened = _ORIGINAL_FSTAT(handle.fileno())
            if not _is_regular_file(opened) or _is_reparse_point(opened):
                raise ValueError("identity output handle is not a regular file")
            opened_identity = _file_identity(opened)
            written = handle.write(data)
            _require_original_stat_policy()
            if type(written) is not int or written != len(data):
                raise ValueError("identity output write was incomplete")
    except FileExistsError as exc:
        raise ValueError(
            "identity output must be a new file under an existing directory"
        ) from exc
    after = _path_lstat(path)
    if (
        not _is_regular_file(after)
        or _is_reparse_point(after)
        or _file_identity(after) != opened_identity
    ):
        raise ValueError("identity output path changed after write")
    with path.open("rb") as handle:
        _require_original_stat_policy()
        read_handle = _ORIGINAL_FSTAT(handle.fileno())
        if (
            not _is_regular_file(read_handle)
            or _is_reparse_point(read_handle)
            or _file_identity(read_handle) != opened_identity
        ):
            raise ValueError("identity output changed before readback")
        observed = handle.read(len(data) + 1)
        _require_original_stat_policy()
    after_read = _path_lstat(path)
    if (
        observed != data
        or not _is_regular_file(after_read)
        or _is_reparse_point(after_read)
        or _file_identity(after_read) != opened_identity
    ):
        raise ValueError("identity output bytes changed after write")
    return sha256_bytes(data)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ARK V3 offline identity capture")
    sub = parser.add_subparsers(dest="command", required=True)

    hf = sub.add_parser("hf-snapshot", help="hash an already-materialized HF snapshot")
    hf.add_argument("--root", type=Path, required=True)
    hf.add_argument("--revision", required=True)
    hf.add_argument("--chat-template-probe", type=Path, required=True)
    hf.add_argument("--output", type=Path, required=True)

    tool = sub.add_parser("tool", help="hash a pinned export tool file")
    tool.add_argument("--path", type=Path, required=True)
    tool.add_argument("--revision", required=True)
    tool.add_argument(
        "--role",
        choices=("hf_to_gguf_converter", "quantizer"),
        required=True,
    )
    tool.add_argument("--output", type=Path, required=True)

    code = sub.add_parser("code", help="hash the V3 runtime source tree")
    code.add_argument("--root", type=Path, required=True)
    code.add_argument("--output", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "hf-snapshot":
        payload = build_hf_snapshot_identity(
            args.root,
            model_id=_MODEL_ID,
            revision=args.revision,
            chat_template_probe=args.chat_template_probe,
        )
    elif args.command == "tool":
        payload = build_tool_identity(
            args.path,
            git_revision=args.revision,
            role=args.role,
        )
    else:
        payload = build_code_tree_identity(args.root)

    artifact_sha = _write_new_json(args.output, payload)
    print(f"identity_artifact_sha256={artifact_sha}")
    if args.command == "hf-snapshot":
        print(f"base_file_manifest_sha256={payload['base_file_manifest_sha256']}")
        print(f"tokenizer_file_manifest_sha256={payload['tokenizer_file_manifest_sha256']}")
        print(f"chat_template_probe_sha256={payload['chat_template_probe_sha256']}")
    elif args.command == "tool":
        print(f"tool_identity_sha256={payload['identity_sha256']}")
    else:
        print(f"code_manifest_sha256={payload['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
