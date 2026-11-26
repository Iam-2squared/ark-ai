"""Synthetic POSIX descriptor recheck after a reentrant named-path stat.

Fixture bytes only. No SQLite connection, private user file, or execution.
"""

from __future__ import annotations

import os

import pytest

from ark import disconnected_posix_handle_seal as module
from ark.disconnected_posix_handle_seal import PosixHandleSealRejected


@pytest.fixture(autouse=True)
def _only_posix():
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        pytest.skip("POSIX descriptor-relative synthetic file review only")


@pytest.mark.parametrize(
    ("before", "after"),
    (
        (b"old-byte-seq", b"new-byte-seq"),
        (b"fixture", b"fixture-appended"),
        (b"ABCDE12345", b"ZZZZZ12345"),
    ),
)
def test_final_named_stat_callback_mutation_rejected(
    tmp_path, monkeypatch, before, after,
):
    path = tmp_path / "synthetic-fixture.bin"
    path.write_bytes(before)
    true_stat = module.os.stat
    touched = False

    def mutate_after_stat(name, *args, **kwargs):
        nonlocal touched
        observation = true_stat(name, *args, **kwargs)
        if name == path.name and kwargs.get("dir_fd") is not None and not touched:
            touched = True
            # The caller has already received a valid old stat result.
            # Only a final fstat on the held file can catch this mutation.
            path.write_bytes(after)
        return observation

    monkeypatch.setattr(module.os, "stat", mutate_after_stat)
    with pytest.raises(PosixHandleSealRejected, match="descriptor changed"):
        module._once(path)
    assert touched is True
    assert path.read_bytes() == after


def test_clean_named_stat_callback_remains_allowed(tmp_path, monkeypatch):
    path = tmp_path / "synthetic-fixture.bin"
    path.write_bytes(b"stable fixture")
    true_stat = module.os.stat
    callbacks = []

    def observe(name, *args, **kwargs):
        if name == path.name and kwargs.get("dir_fd") is not None:
            callbacks.append(name)
        return true_stat(name, *args, **kwargs)

    monkeypatch.setattr(module.os, "stat", observe)
    first = module._once(path)
    assert callbacks == [path.name]
    assert first.size_bytes == len(b"stable fixture")
