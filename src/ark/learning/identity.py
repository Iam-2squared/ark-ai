"""Local byte-identity manifests for V3 base/tokenizer/export/code evidence.

No downloads or network access occur here. These helpers only hash already-present files.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from .execution import canonical_json, sha256_bytes


_MAX_SNAPSHOT_ENTRIES = 16_384
_MAX_SNAPSHOT_PATH_BYTES = 4_096


@dataclass(frozen=True)
class FileIdentity:
    path: str
    sha256: str
    bytes: int
    symlink: bool


def _hash_file(path: Path) -> tuple[str, int]:
    """Reject a redirected open and metadata changes to the opened file."""
    before = path.lstat()

    def epoch(info: os.stat_result) -> tuple[int, ...]:
        return (
            info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns,
        )

    h = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        # Windows path-stat and descriptor-stat can describe the *same* file
        # with different ctime semantics (creation vs change time). Compare
        # the actual file ID and portable content metadata across sources;
        # compare each source's complete epoch only against itself.
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or before.st_ino == 0
            or opened.st_ino == 0
            or not os.path.samestat(before, opened)
            or before.st_size != opened.st_size
            or before.st_mtime_ns != opened.st_mtime_ns
            or (
                os.name != "nt"
                and (before.st_mode != opened.st_mode
                     or before.st_ctime_ns != opened.st_ctime_ns)
            )
        ):
            raise ValueError("identity file changed during hashing")
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
        if epoch(os.fstat(handle.fileno())) != epoch(opened):
            raise ValueError("identity file changed during hashing")
    if epoch(path.lstat()) != epoch(before):
        raise ValueError("identity file changed during hashing")
    return h.hexdigest(), size


def _identity_label(label: object) -> str:
    """Canonical relative label; metadata aliases cannot escape a manifest."""
    if (
        type(label) is not str
        or not 1 <= len(label) <= 4096
        or label.startswith("/")
        or "\\" in label
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in label)
        or any(part in ("", ".", "..") for part in label.split("/"))
        or re.fullmatch(r"[A-Za-z]:", label.split("/")[0]) is not None
    ):
        raise ValueError("identity label must be an exact relative POSIX path")
    try:
        raw = label.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ValueError("identity label must be valid UTF-8") from exc
    if len(raw) > 4096:
        raise ValueError("identity label byte budget exceeded")
    return label


def file_identity(path: Path, *, label: str | None = None) -> FileIdentity:
    """Hash one existing regular file, checking its path and byte epoch.

    These before/after checks detect ordinary replacement or mutation during
    local manifest generation. They are NOT an atomic descriptor-based open,
    security boundary against a hostile writer, or future file immutability.
    """
    path = Path(path)
    safe_label = _identity_label(path.name if label is None else label)
    if ".." in path.parts:
        raise ValueError("identity path may not traverse parent aliases")
    try:
        if any(parent.is_symlink() for parent in path.parents):
            raise ValueError("symlinked identity file ancestors are forbidden")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"identity path must be one regular non-symlink file: {path}")
        before = path.stat(follow_symlinks=False)
        if not path.is_file() or before.st_nlink != 1:
            raise ValueError("identity file must have one regular-file link")
        sha, size = _hash_file(path)
        after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise ValueError("identity file became unavailable during hashing") from exc
    # Include mode, link count and inode as well as the size/timestamps.
    # Never return a digest from a file known to have changed mid-read.
    def epoch(info: object) -> tuple[int, ...]:
        return (
            info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, info.st_nlink,
        )

    if (
        path.is_symlink()
        or not path.is_file()
        or size != before.st_size
        or epoch(before) != epoch(after)
    ):
        raise ValueError("identity file changed during hashing")
    return FileIdentity(safe_label, sha, size, False)


def _entry_epoch(path: Path, *, is_dir: bool) -> tuple[int, ...]:
    """Retain directory/file identity, not only a reusable relative name."""
    try:
        info = path.lstat()
    except OSError as exc:
        raise ValueError("snapshot entry disappeared during enumeration") from exc
    if (
        (is_dir and not stat.S_ISDIR(info.st_mode))
        or (not is_dir and not stat.S_ISREG(info.st_mode))
    ):
        raise ValueError("snapshot entry type changed during enumeration")
    return (
        info.st_dev, info.st_ino, info.st_mode, info.st_size,
        info.st_mtime_ns, info.st_ctime_ns, info.st_nlink,
    )


def _snapshot_entries(root: Path) -> tuple[tuple[str, Path, bool, tuple[int, ...]], ...]:
    """Bound local manifest to names AND file/directory metadata epochs.

    Root is included explicitly, so replacing a tree with a same-name copy
    cannot pass merely because the directory listing looks identical. This
    remains a best-effort local check, NOT a hostile-writer-safe snapshot.
    """
    root = Path(root)
    if (
        not root.is_dir()
        or root.is_symlink()
        or any(parent.is_symlink() for parent in root.parents)
        or ".." in root.parts
    ):
        raise ValueError("snapshot root must be a non-aliased local directory")
    entries = [("", root, True, _entry_epoch(root, is_dir=True))]
    # Bound enumeration before sorting: sorted(rglob("*")) alone can consume
    # unbounded memory on a malformed materialized model snapshot.
    paths = []
    path_bytes = 0
    for path in root.rglob("*"):
        if len(paths) >= _MAX_SNAPSHOT_ENTRIES:
            raise ValueError("snapshot entry count exceeds local budget")
        relative = path.relative_to(root).as_posix()
        try:
            encoded = relative.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise ValueError("snapshot has an invalid UTF-8 path") from exc
        if len(encoded) > _MAX_SNAPSHOT_PATH_BYTES:
            raise ValueError("snapshot relative path exceeds local budget")
        path_bytes += len(encoded)
        if path_bytes > _MAX_SNAPSHOT_PATH_BYTES * _MAX_SNAPSHOT_ENTRIES:
            raise ValueError("snapshot path inventory exceeds local budget")
        paths.append(path)
    for path in sorted(paths, key=lambda p: p.as_posix()):
        if path.is_symlink():
            raise ValueError("snapshot contains a symlink entry")
        if path.is_dir():
            is_dir = True
        elif path.is_file():
            is_dir = False
        else:
            raise ValueError(f"unsupported snapshot entry: {path}")
        entries.append((
            path.relative_to(root).as_posix(), path, is_dir,
            _entry_epoch(path, is_dir=is_dir),
        ))
    return tuple(entries)


def _assert_snapshot_entries(
    root: Path, original: tuple[tuple[str, Path, bool, tuple[int, ...]], ...],
) -> None:
    now = _snapshot_entries(root)
    if tuple((rel, is_dir, epoch) for rel, _, is_dir, epoch in now) != tuple(
        (rel, is_dir, epoch) for rel, _, is_dir, epoch in original
    ):
        raise ValueError("snapshot entries changed during hashing")


def directory_file_identities(root: Path) -> tuple[FileIdentity, ...]:
    """Produce a local manifest without accepting a changing file listing."""
    root = Path(root)
    entries = _snapshot_entries(root)
    rows = [
        file_identity(path, label=relative)
        for relative, path, is_dir, _ in entries if not is_dir
    ]
    _assert_snapshot_entries(root, entries)
    if not rows:
        raise ValueError("snapshot directory contains no files")
    return tuple(rows)


def build_code_tree_identity(root: Path) -> dict:
    """Hash all V3 learning runtime Python sources plus packaging metadata.

    This prevents an authorized GPU command from trusting only a user-supplied git SHA.
    Tests/docs are intentionally excluded; every importable V3 learning module is included.
    """
    root = Path(root)
    learning_root = root / "src" / "ark" / "learning"
    if not learning_root.is_dir() or learning_root.is_symlink():
        raise ValueError("runtime code root is missing src/ark/learning")
    entries = _snapshot_entries(learning_root)
    paths = [root / "pyproject.toml"] + [
        path for _, path, is_dir, _ in entries if not is_dir and path.suffix == ".py"
    ]
    if len(paths) < 2:
        raise ValueError("runtime code manifest requires learning Python sources")
    rows = [file_identity(path, label=path.relative_to(root).as_posix()) for path in paths]
    _assert_snapshot_entries(learning_root, entries)
    # The learning subtree has its own enumeration epoch, but pyproject.toml
    # lives outside it. Rehash packaging after all Python files so a build
    # metadata change during code capture cannot silently keep the old hash.
    # This is a best-effort local check, not a hostile-writer atomic snapshot.
    if file_identity(paths[0], label="pyproject.toml") != rows[0]:
        raise ValueError("runtime packaging metadata changed during code capture")
    manifest = {
        "schema_version": 1,
        "scope": "pyproject.toml+src/ark/learning/**/*.py",
        "files": [row.__dict__ for row in rows],
    }
    return {
        "manifest": manifest,
        "manifest_sha256": sha256_bytes(canonical_json(manifest)),
    }


def build_hf_snapshot_identity(
    root: Path,
    *,
    model_id: str,
    revision: str,
    chat_template_probe: Path,
) -> dict:
    """Hash a materialized HF snapshot and derive base/tokenizer snapshot digests."""
    if type(model_id) is not str or model_id != "Qwen/Qwen3-4B-Instruct-2507":
        raise ValueError("unexpected experiment-001 model ID")
    if type(revision) is not str or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("immutable 40-hex HF revision required")
    files = directory_file_identities(root)
    by_path = {row.path: row for row in files}
    required_files = ("config.json", "tokenizer_config.json", "tokenizer.json")
    missing = [name for name in required_files if name not in by_path]
    if missing:
        raise ValueError(f"snapshot missing required identity files: {', '.join(missing)}")
    empty_required = [name for name in required_files if by_path[name].bytes <= 0]
    if empty_required:
        raise ValueError(f"snapshot has empty required identity files: {', '.join(empty_required)}")

    weight_rows = [row for row in files if row.path.endswith(".safetensors")]
    if not weight_rows:
        raise ValueError("snapshot requires safetensors model weights")
    if any(row.bytes <= 0 for row in weight_rows):
        raise ValueError("snapshot contains empty safetensors model weights")

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
    if probe.bytes <= 0:
        raise ValueError("chat-template probe must be non-empty")
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
    if type(git_revision) is not str or re.fullmatch(r"[0-9a-f]{40}", git_revision) is None:
        raise ValueError("exact 40-hex tool revision required")
    if type(role) is not str or role not in {"hf_to_gguf_converter", "quantizer"}:
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
