"""Bounded, read-only local fixture inventory for reproducibility diagnostics.

No training, artifact generation, model loading, network, grants, or tool calls.
Hashes check independently retained bytes for drift, not origin authenticity.
Only explicitly named plain fixture files are read; there is no discovery.
Filesystem replacement races are not a trusted storage/identity guarantee.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path

_MAX_FILES = 64
_MAX_FILE_BYTES = 8 * 1024 * 1024
_MAX_TOTAL_BYTES = 16 * 1024 * 1024
_MAX_PATH_BYTES = 512
_SUFFIXES = frozenset((".txt", ".json", ".fixture"))
_DIGEST = re.compile(r"fixtureinventory_[0-9a-f]{64}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_DEVICE = re.compile(r"(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?\Z")
_DOMAIN = b"ARK-disconnected-local-fixture-inventory-v1\0"


class SyntheticFixtureInventoryRejected(RuntimeError):
    """A bounded local fixture inspection could not be trusted."""


@dataclass(frozen=True, slots=True)
class SyntheticFixtureFile:
    relative_path: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SyntheticFixtureInventory:
    files: tuple[SyntheticFixtureFile, ...]
    digest: str

    @property
    def training_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def external_provenance_verified(self) -> bool:
        return False


def _validate_path(path: object) -> tuple[str, ...]:
    if type(path) is not str:
        raise SyntheticFixtureInventoryRejected("exact fixture path required")
    try:
        encoded = path.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise SyntheticFixtureInventoryRejected("fixture path encoding invalid") from exc
    if (
        not encoded or len(encoded) > _MAX_PATH_BYTES
        or unicodedata.normalize("NFC", path) != path
        or "\" in path or ":" in path or "\x00" in path
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
    ):
        raise SyntheticFixtureInventoryRejected("unsafe fixture path")
    parts = path.split("/")
    if any(
        part in ("", ".", "..") or part.startswith(".")
        or part != part.strip() or part.endswith(".")
        or _DEVICE.fullmatch(part) is not None
        for part in parts
    ) or Path(parts[-1]).suffix not in _SUFFIXES:
        raise SyntheticFixtureInventoryRejected("unsafe fixture path component")
    return tuple(parts)


def _canonical(files: tuple[SyntheticFixtureFile, ...]) -> bytes:
    if type(files) is not tuple or not 1 <= len(files) <= _MAX_FILES:
        raise SyntheticFixtureInventoryRejected("invalid fixture inventory size")
    previous = ""
    seen_folded: set[str] = set()
    rows = []
    for item in files:
        if type(item) is not SyntheticFixtureFile:
            raise SyntheticFixtureInventoryRejected("noncanonical fixture inventory row")
        name = item.relative_path
        _validate_path(name)
        folded = name.casefold()
        if name <= previous or folded in seen_folded:
            raise SyntheticFixtureInventoryRejected("duplicate or unordered fixture path")
        previous = name
        seen_folded.add(folded)
        if (
            type(item.size_bytes) is not int
            or not 0 <= item.size_bytes <= _MAX_FILE_BYTES
            or type(item.sha256) is not str
            or _HEX.fullmatch(item.sha256) is None
        ):
            raise SyntheticFixtureInventoryRejected("invalid fixture row content")
        rows.append([name, item.size_bytes, item.sha256])
    if sum(item.size_bytes for item in files) > _MAX_TOTAL_BYTES:
        raise SyntheticFixtureInventoryRejected("fixture inventory budget exceeded")
    return json.dumps(rows, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def _digest(payload: bytes) -> str:
    return "fixtureinventory_" + hashlib.sha256(_DOMAIN + payload).hexdigest()


def assert_fixture_inventory_integrity(witness: SyntheticFixtureInventory) -> None:
    """Check local canonical content digest; never assert authentic provenance."""
    if type(witness) is not SyntheticFixtureInventory:
        raise SyntheticFixtureInventoryRejected("exact inventory witness required")
    original_files, original_digest = witness.files, witness.digest
    payload = _canonical(original_files)
    if (
        witness.files is not original_files
        or witness.digest is not original_digest
        or type(original_digest) is not str
        or _DIGEST.fullmatch(original_digest) is None
        or original_digest != _digest(payload)
    ):
        raise SyntheticFixtureInventoryRejected("fixture inventory witness changed")


def _file_fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_mode,
            value.st_size, value.st_mtime_ns)


def review_local_fixture_inventory(
    root: Path,
    relative_paths: tuple[str, ...],
    *,
    retained: SyntheticFixtureInventory | None = None,
) -> SyntheticFixtureInventory:
    """Hash explicit, size-bounded synthetic fixtures only, with no writes.

    Symlinks are refused at checked path components. This is not a defense
    against malicious same-inode edits, file-swap races, or forged hashes.
    """
    if not isinstance(root, Path) or type(relative_paths) is not tuple:
        raise SyntheticFixtureInventoryRejected("exact local root and paths required")
    if not 1 <= len(relative_paths) <= _MAX_FILES:
        raise SyntheticFixtureInventoryRejected("invalid fixture path count")
    for name in relative_paths:
        _validate_path(name)
    if (
        tuple(sorted(relative_paths)) != relative_paths
        or len({name.casefold() for name in relative_paths}) != len(relative_paths)
    ):
        raise SyntheticFixtureInventoryRejected("fixture paths must be sorted and unique")
    if retained is not None:
        assert_fixture_inventory_integrity(retained)
    try:
        root_stat = root.lstat()
        if not stat.S_ISDIR(root_stat.st_mode) or root.is_symlink():
            raise SyntheticFixtureInventoryRejected("unsafe fixture root")
        base = root.resolve(strict=True)
        if not base.is_dir():
            raise SyntheticFixtureInventoryRejected("fixture root missing")
        rows = []
        total = 0
        for name in relative_paths:
            current = root
            parts = _validate_path(name)
            for part in parts[:-1]:
                current = current / part
                parent_state = current.lstat()
                if not stat.S_ISDIR(parent_state.st_mode):
                    raise SyntheticFixtureInventoryRejected("non-directory fixture parent")
            path = current / parts[-1]
            before = path.lstat()
            if not stat.S_ISREG(before.st_mode) or before.st_size > _MAX_FILE_BYTES:
                raise SyntheticFixtureInventoryRejected("unsafe fixture file or size")
            total += before.st_size
            if total > _MAX_TOTAL_BYTES:
                raise SyntheticFixtureInventoryRejected("fixture inventory budget exceeded")
            hashed = hashlib.sha256()
            count = 0
            with path.open("rb") as handle:
                if _file_fingerprint(os.fstat(handle.fileno())) != _file_fingerprint(before):
                    raise SyntheticFixtureInventoryRejected("fixture changed before read")
                while True:
                    chunk = handle.read(64 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > _MAX_FILE_BYTES:
                        raise SyntheticFixtureInventoryRejected("fixture read budget exceeded")
                    hashed.update(chunk)
                if _file_fingerprint(os.fstat(handle.fileno())) != _file_fingerprint(before):
                    raise SyntheticFixtureInventoryRejected("fixture changed during read")
            if (
                count != before.st_size
                or _file_fingerprint(path.lstat()) != _file_fingerprint(before)
            ):
                raise SyntheticFixtureInventoryRejected("fixture changed after read")
            rows.append(SyntheticFixtureFile(name, count, hashed.hexdigest()))
        if _file_fingerprint(root.lstat()) != _file_fingerprint(root_stat):
            raise SyntheticFixtureInventoryRejected("fixture root changed")
        rows_tuple = tuple(rows)
        witness = SyntheticFixtureInventory(rows_tuple, _digest(_canonical(rows_tuple)))
        assert_fixture_inventory_integrity(witness)
        if retained is not None and witness != retained:
            raise SyntheticFixtureInventoryRejected("retained fixture inventory differs")
        return witness
    except (OSError, UnicodeError) as exc:
        raise SyntheticFixtureInventoryRejected("fixture inventory read unavailable") from exc
