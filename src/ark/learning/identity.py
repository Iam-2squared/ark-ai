"""Local byte-identity manifests for V3 base/tokenizer/export evidence.

No downloads or network access occur here. These helpers only hash already-present files.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from .execution import canonical_json, sha256_bytes


@dataclass(frozen=True)
class FileIdentity:
    path: str
    sha256: str
    bytes: int
    symlink: bool


def _hash_file(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def file_identity(path: Path, *, label: str | None = None) -> FileIdentity:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"identity path is not a file: {path}")
    sha, size = _hash_file(path)
    return FileIdentity(label or path.name, sha, size, path.is_symlink())


def directory_file_identities(root: Path) -> tuple[FileIdentity, ...]:
    root = Path(root)
    if not root.is_dir():
        raise ValueError("snapshot root must be an existing directory")
    rows: list[FileIdentity] = []
    for path in sorted(root.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_dir():
            if path.is_symlink():
                raise ValueError("symlinked directories are not allowed in identity snapshots")
            continue
        if not path.is_file():
            raise ValueError(f"unsupported snapshot entry: {path}")
        relative = path.relative_to(root).as_posix()
        rows.append(file_identity(path, label=relative))
    if not rows:
        raise ValueError("snapshot directory contains no files")
    return tuple(rows)


def build_hf_snapshot_identity(
    root: Path,
    *,
    model_id: str,
    revision: str,
    chat_template_probe: Path,
) -> dict:
    """Hash a materialized HF snapshot and derive base/tokenizer snapshot digests."""
    if model_id != "Qwen/Qwen3-4B-Instruct-2507":
        raise ValueError("unexpected experiment-001 model ID")
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("immutable 40-hex HF revision required")
    files = directory_file_identities(root)
    names = {row.path for row in files}
    if "config.json" not in names or "tokenizer_config.json" not in names:
        raise ValueError("snapshot requires config.json and tokenizer_config.json")
    if not any(name.endswith(".safetensors") for name in names):
        raise ValueError("snapshot requires safetensors model weights")

    file_rows = [row.__dict__ for row in files]
    base_manifest = {
        "schema_version": 1,
        "model_id": model_id,
        "revision": revision,
        "files": file_rows,
    }
    tokenizer_names = {
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "added_tokens.json",
        "merges.txt",
        "vocab.json",
    }
    tokenizer_rows = [row.__dict__ for row in files if Path(row.path).name in tokenizer_names]
    if not tokenizer_rows:
        raise ValueError("no tokenizer identity files found")
    tokenizer_manifest = {
        "schema_version": 1,
        "model_id": model_id,
        "revision": revision,
        "files": tokenizer_rows,
    }
    probe = file_identity(Path(chat_template_probe), label="chat-template-probe.txt")
    return {
        "model_id": model_id,
        "revision": revision,
        "base_file_manifest": base_manifest,
        "base_file_manifest_sha256": sha256_bytes(canonical_json(base_manifest)),
        "tokenizer_file_manifest": tokenizer_manifest,
        "tokenizer_file_manifest_sha256": sha256_bytes(canonical_json(tokenizer_manifest)),
        "chat_template_probe": probe.__dict__,
        "chat_template_probe_sha256": probe.sha256,
    }


def build_tool_identity(path: Path, *, git_revision: str, role: str) -> dict:
    if re.fullmatch(r"[0-9a-f]{40}", git_revision) is None:
        raise ValueError("exact 40-hex tool revision required")
    if role not in {"hf_to_gguf_converter", "quantizer"}:
        raise ValueError("unsupported export tool role")
    identity = file_identity(path)
    return {
        "schema_version": 1,
        "role": role,
        "git_revision": git_revision,
        "file": identity.__dict__,
        "identity_sha256": sha256_bytes(
            canonical_json(
                {
                    "role": role,
                    "git_revision": git_revision,
                    "file": identity.__dict__,
                }
            )
        ),
    }
