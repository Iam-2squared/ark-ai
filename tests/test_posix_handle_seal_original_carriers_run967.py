"""Run967 POSIX descriptor synthetic seal original carrier and codec checks.

Checks are disconnected/local only; neither capture nor review grants consent,
independent content provenance, durable authorization, or tool execution.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

from ark import disconnected_posix_handle_seal as mod


@pytest.fixture(autouse=True)
def _posix():
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        pytest.skip("descriptor-anchored POSIX fixtures only")


def _fixture(tmp_path):
    path = tmp_path / "synthetic-descriptor-source.bin"
    path.write_bytes(b"local synthetic bytes only")
    return path


@pytest.mark.parametrize(("name", "replacement"), [
    ("_SEAL_FIELD_NAMES", ("inode",)),
    ("_SEAL_DENIAL_NAMES", ("tool_execution_authorized",)),
    ("_SEAL_HOOK_NAMES", ("__init__",)),
    ("_DOMAIN", b"forged-domain"),
    ("_CHUNK", 1_000_000),
    ("_MAX_BYTES", 999_999_999),
    ("_MAX_PATH", 999_999),
    ("fields", lambda *_args: ()),
])
def test_vector_or_budget_replacement_denied_before_descriptor_open(
    tmp_path, monkeypatch, name, replacement,
):
    path = _fixture(tmp_path)
    prior = mod.capture_posix_handle_seal(path)
    with monkeypatch.context() as patch:
        patch.setattr(mod, name, replacement)
        patch.setattr(mod.os, "open", lambda *_a, **_k: pytest.fail("unexpected open"))
        with pytest.raises(mod.PosixHandleSealRejected, match="carrier boundary changed"):
            mod.capture_posix_handle_seal(path)
        with pytest.raises(mod.PosixHandleSealRejected, match="carrier boundary changed"):
            mod.review_posix_handle_seal(path, prior)


@pytest.mark.parametrize("name", [
    "path_sha256", "directories_sha256", "content_sha256",
    "size_bytes", "device", "inode", "mtime_ns", "ctime_ns",
    "independent_custody_proven", "source_authenticated",
    "durable_snapshot_proven", "file_mutation_authorized",
    "tool_execution_authorized",
    "__init__", "__new__", "__getattribute__", "__getattr__", "__eq__",
])
def test_descriptor_or_callback_swap_cannot_read_fixture(
    tmp_path, monkeypatch, name,
):
    # Rebinding dataclass tp_new may persist in the interpreter despite
    # monkeypatch cleanup. Use a child process for the same allocator attack.
    if name == "__new__":
        script = """
from pathlib import Path
from tempfile import TemporaryDirectory
from ark import disconnected_posix_handle_seal as mod
with TemporaryDirectory() as directory:
    path = Path(directory) / "synthetic-descriptor-source.bin"
    path.write_bytes(b"local synthetic bytes only")
    prior = mod.capture_posix_handle_seal(path)
    calls = []
    def poisoned(*args, **kwargs):
        calls.append(True)
        raise AssertionError("substituted seal allocator invoked")
    mod.PosixHandleSeal.__new__ = poisoned
    for action in (
        lambda: mod.capture_posix_handle_seal(path),
        lambda: mod.review_posix_handle_seal(path, prior),
    ):
        try:
            action()
        except mod.PosixHandleSealRejected as exc:
            assert "carrier boundary changed" in str(exc), str(exc)
        else:
            raise AssertionError("substituted seal allocator was admitted")
    assert calls == []
"""
        result = subprocess.run(
            [sys.executable, "-c", script], text=True, capture_output=True,
            check=False, timeout=30,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        return
    path = _fixture(tmp_path)
    prior = mod.capture_posix_handle_seal(path)
    called = []

    def poisoned(*args, **kwargs):
        called.append((args, kwargs))
        pytest.fail("injected getter or class callback invoked")

    replacement = poisoned if name.startswith("__") else property(poisoned)
    with monkeypatch.context() as patch:
        patch.setattr(mod.PosixHandleSeal, name, replacement, raising=False)
        patch.setattr(mod.os, "open", lambda *_a, **_k: pytest.fail("unexpected open"))
        with pytest.raises(mod.PosixHandleSealRejected, match="carrier boundary changed"):
            mod.capture_posix_handle_seal(path)
        with pytest.raises(mod.PosixHandleSealRejected, match="carrier boundary changed"):
            mod.review_posix_handle_seal(path, prior)
    assert called == []


def test_poststat_reentrant_seal_descriptor_swap_is_rejected(
    tmp_path, monkeypatch,
):
    path = _fixture(tmp_path)
    real_stat = mod.os.stat
    touched = []

    def changed_after_stat(name, *args, **kwargs):
        info = real_stat(name, *args, **kwargs)
        if name == path.name and kwargs.get("dir_fd") is not None and not touched:
            touched.append(True)
            monkeypatch.setattr(
                mod.PosixHandleSeal,
                "source_authenticated",
                property(lambda self: False),
            )
        return info

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "stat", changed_after_stat)
        with pytest.raises(mod.PosixHandleSealRejected, match="carrier boundary changed"):
            mod.capture_posix_handle_seal(path)
    assert touched == [True]


def test_valid_fixture_still_returns_no_derived_authority(tmp_path):
    path = _fixture(tmp_path)
    prior = mod.capture_posix_handle_seal(path)
    current = mod.review_posix_handle_seal(path, prior)
    assert current == prior
    assert current.independent_custody_proven is False
    assert current.source_authenticated is False
    assert current.durable_snapshot_proven is False
    assert current.file_mutation_authorized is False
    assert current.tool_execution_authorized is False
