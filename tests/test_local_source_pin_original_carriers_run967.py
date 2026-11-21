"""Run967: local metadata pins must not trust substituted in-process carriers.

Synthetic temp files only. A pin is not file content verification, approval,
authenticated provenance, or permission to access private data.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from ark import disconnected_local_source_pin as mod


def _fixture(tmp_path):
    path = tmp_path / "synthetic-local-metadata.db"
    path.write_bytes(b"synthetic metadata fixture")
    return path


def _deny_before_scan(monkeypatch, path, retained, name, replacement):
    def forbidden(*_args, **_kwargs):
        pytest.fail("mutated diagnostic boundary reached filesystem scan")

    with monkeypatch.context() as patch:
        patch.setattr(mod, name, replacement)
        patch.setattr(mod.os, "lstat", forbidden)
        with pytest.raises(mod.DisconnectedSourceRejected, match="boundary changed"):
            mod.capture_disconnected_source(path)
        with pytest.raises(mod.DisconnectedSourceRejected, match="boundary changed"):
            mod.review_disconnected_source(path, retained)


@pytest.mark.parametrize(("name", "replacement"), [
    ("_PIN_FIELDS", ("file_size",)),
    ("_DENIALS", ("file_mutation_authorized",)),
    ("_ORIGINAL_DENIALS", ()),
    ("_PIN_HOOK_NAMES", ("__init__",)),
    ("_DOMAIN", b"forged-path-pin-domain"),
    ("_MAX_PATH", 1_000_000),
    ("fields", lambda *_args: ()),
])
def test_replaced_vector_codec_or_reflection_denied_before_scan(
    tmp_path, monkeypatch, name, replacement,
):
    path = _fixture(tmp_path)
    retained = mod.capture_disconnected_source(path)
    _deny_before_scan(monkeypatch, path, retained, name, replacement)


@pytest.mark.parametrize("name", [
    "path_sha256",
    "parent_chain_sha256",
    "file_device",
    "file_inode",
    "file_size",
    "file_mtime_ns",
    "parent_device",
    "parent_inode",
    "independently_attested",
    "contents_verified",
    "memory_release_authorized",
    "file_mutation_authorized",
    "__init__",
    "__new__",
    "__getattribute__",
    "__getattr__",
])
def test_substituted_dataclass_slot_or_hook_denied_without_invocation(
    tmp_path, monkeypatch, name,
):
    # Reassigning built-in tp_new on a Python dataclass can leave the type's
    # allocation slot changed after monkeypatch undo. Isolate that same
    # negative case in a child interpreter; keep all denial checks intact.
    if name == "__new__":
        script = """
from pathlib import Path
from tempfile import TemporaryDirectory
from ark import disconnected_local_source_pin as mod
with TemporaryDirectory() as directory:
    path = Path(directory) / "synthetic-local-metadata.db"
    path.write_bytes(b"synthetic metadata fixture")
    retained = mod.capture_disconnected_source(path)
    calls = []
    def poisoned(*args, **kwargs):
        calls.append(True)
        raise AssertionError("substituted allocator invoked")
    mod.DisconnectedSourcePin.__new__ = poisoned
    for action in (
        lambda: mod.capture_disconnected_source(path),
        lambda: mod.review_disconnected_source(path, retained),
    ):
        try:
            action()
        except mod.DisconnectedSourceRejected as exc:
            assert "boundary changed" in str(exc), str(exc)
        else:
            raise AssertionError("modified allocator was admitted")
    assert calls == []
"""
        result = subprocess.run(
            [sys.executable, "-c", script], text=True, capture_output=True,
            check=False, timeout=30,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        return
    path = _fixture(tmp_path)
    retained = mod.capture_disconnected_source(path)
    calls = []

    def poisoned(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("substituted callback executed")

    replacement = poisoned if name.startswith("__") else property(poisoned)

    with monkeypatch.context() as patch:
        patch.setattr(mod.DisconnectedSourcePin, name, replacement, raising=False)
        with pytest.raises(mod.DisconnectedSourceRejected, match="boundary changed"):
            mod.capture_disconnected_source(path)
        with pytest.raises(mod.DisconnectedSourceRejected, match="boundary changed"):
            mod.review_disconnected_source(path, retained)
    assert not calls


def test_reentrant_ancestor_scan_guard_denies_post_scan_descriptor_poison(
    tmp_path, monkeypatch,
):
    path = _fixture(tmp_path)
    retained = mod.capture_disconnected_source(path)
    original_lstat = os.lstat
    calls = []

    def altered_lstat(candidate):
        if not calls:
            calls.append("injected")
            monkeypatch.setattr(mod, "_DENIALS", ())
        return original_lstat(candidate)

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "lstat", altered_lstat)
        with pytest.raises(mod.DisconnectedSourceRejected, match="boundary changed"):
            mod.review_disconnected_source(path, retained)
    assert calls == ["injected"]


def test_normal_fixture_still_produces_inert_pin(tmp_path):
    path = _fixture(tmp_path)
    captured = mod.capture_disconnected_source(path)
    reread = mod.review_disconnected_source(path, captured)
    assert reread == captured
    assert captured.independently_attested is False
    assert captured.contents_verified is False
    assert captured.memory_release_authorized is False
    assert captured.file_mutation_authorized is False
