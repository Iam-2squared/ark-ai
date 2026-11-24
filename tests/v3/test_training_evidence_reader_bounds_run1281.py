"""Run1281: V3 training evidence reads are bounded and descriptor-checked.

Only synthetic local files are opened. No model, GPU, preflight backend,
Candidate generation, protected V2 evaluation, or paid compute is reachable.
"""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import training_cli as cli


def test_each_training_evidence_kind_has_a_finite_reviewed_budget():
    assert cli._EVIDENCE_FILE_BUDGETS == {
        "provenance manifest": 64 * 1024 * 1024,
        "contamination report": 64 * 1024 * 1024,
        "preflight report": 1_048_576,
    }


def test_stable_regular_evidence_file_is_read_and_hash_verified(tmp_path: Path):
    payload = b'{"synthetic":"evidence"}'
    path = tmp_path / "evidence.json"
    path.write_bytes(payload)

    assert cli._verify_file(
        path,
        cli.digest(payload),
        "preflight report",
    ) == payload


def test_unknown_evidence_label_is_denied_before_path_access(tmp_path: Path):
    path = tmp_path / "missing.json"
    with pytest.raises(RuntimeError, match="unsupported V3 evidence file label"):
        cli._verify_file(path, "0" * 64, "unknown evidence")
    assert not path.exists()


def test_oversized_file_is_rejected_before_open(tmp_path: Path, monkeypatch):
    path = tmp_path / "too-large.json"
    path.write_bytes(b"x" * 17)
    calls = []
    native_open = cli.os.open

    def forbidden_open(file, flags, *args, **kwargs):
        calls.append((file, flags))
        raise AssertionError("oversized evidence must be denied before open")

    monkeypatch.setattr(cli.os, "open", forbidden_open)
    with pytest.raises(RuntimeError, match="path or byte budget denied"):
        cli._read_bounded_evidence(path, max_bytes=16, label="fixture")
    assert calls == []
    monkeypatch.setattr(cli.os, "open", native_open)


def test_read_requests_only_budget_plus_one(tmp_path: Path, monkeypatch):
    path = tmp_path / "bounded.json"
    path.write_bytes(b"bounded")
    native_fdopen = cli.os.fdopen
    requested = []

    class Reader:
        def __init__(self, inner):
            self.inner = inner

        def __enter__(self):
            self.inner.__enter__()
            return self

        def __exit__(self, *args):
            return self.inner.__exit__(*args)

        def fileno(self):
            return self.inner.fileno()

        def read(self, size=-1):
            requested.append(size)
            return self.inner.read(size)

    monkeypatch.setattr(cli.os, "fdopen", lambda fd, mode: Reader(native_fdopen(fd, mode)))
    assert cli._read_bounded_evidence(path, max_bytes=16, label="fixture") == b"bounded"
    assert requested == [17]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_final_symlink_is_denied_before_open(tmp_path: Path, monkeypatch):
    target = tmp_path / "target.json"
    target.write_bytes(b"synthetic")
    path = tmp_path / "alias.json"
    try:
        path.symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is not permitted on this platform")
    calls = []
    monkeypatch.setattr(
        cli.os,
        "open",
        lambda *args, **kwargs: calls.append(args) or (_ for _ in ()).throw(
            AssertionError("symlink must be denied before open")
        ),
    )
    with pytest.raises(RuntimeError, match="path or byte budget denied"):
        cli._read_bounded_evidence(path, max_bytes=64, label="fixture")
    assert calls == []


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_symlinked_parent_is_denied_before_open(tmp_path: Path, monkeypatch):
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    (real_parent / "evidence.json").write_bytes(b"synthetic")
    alias_parent = tmp_path / "alias"
    try:
        alias_parent.symlink_to(real_parent, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlink creation is not permitted on this platform")
    calls = []
    monkeypatch.setattr(
        cli.os,
        "open",
        lambda *args, **kwargs: calls.append(args) or (_ for _ in ()).throw(
            AssertionError("symlinked ancestor must be denied before open")
        ),
    )
    with pytest.raises(RuntimeError, match="path or byte budget denied"):
        cli._read_bounded_evidence(alias_parent / "evidence.json", max_bytes=64, label="fixture")
    assert calls == []


def test_same_byte_inode_replacement_at_open_is_denied_before_read(
    tmp_path: Path,
    monkeypatch,
):
    path = tmp_path / "evidence.json"
    backup = tmp_path / "original.json"
    replacement = tmp_path / "replacement.json"
    payload = b"same synthetic bytes"
    path.write_bytes(payload)
    replacement.write_bytes(payload)
    native_open = cli.os.open
    native_fdopen = cli.os.fdopen
    swapped = []

    class NoRead:
        def __init__(self, inner):
            self.inner = inner

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.inner.__exit__(*args)

        def fileno(self):
            return self.inner.fileno()

        def read(self, *_args, **_kwargs):
            raise AssertionError("unverified replacement inode must not be read")

    def swap_then_open(file, flags, *args, **kwargs):
        if Path(file) == path and not swapped:
            path.rename(backup)
            replacement.rename(path)
            swapped.append(True)
        return native_open(file, flags, *args, **kwargs)

    monkeypatch.setattr(cli.os, "open", swap_then_open)
    monkeypatch.setattr(cli.os, "fdopen", lambda fd, mode: NoRead(native_fdopen(fd, mode)))
    with pytest.raises(RuntimeError, match="changed before its bytes were read"):
        cli._read_bounded_evidence(path, max_bytes=64, label="fixture")
    assert swapped == [True]
    assert backup.read_bytes() == payload
    assert path.read_bytes() == payload


def test_postread_descriptor_epoch_change_is_rejected(tmp_path: Path, monkeypatch):
    path = tmp_path / "evidence.json"
    path.write_bytes(b"stable bytes")
    native_fstat = cli.os.fstat
    calls = []

    def changed_second_fstat(fd):
        info = native_fstat(fd)
        calls.append(fd)
        if len(calls) != 2:
            return info
        values = {
            name: getattr(info, name)
            for name in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        }
        values["st_mtime_ns"] += 1
        return SimpleNamespace(**values)

    monkeypatch.setattr(cli.os, "fstat", changed_second_fstat)
    with pytest.raises(RuntimeError, match="changed during its bounded read"):
        cli._read_bounded_evidence(path, max_bytes=64, label="fixture")
    assert len(calls) == 2


@pytest.mark.skipif(
    os.name != "posix" or not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"),
    reason="POSIX FIFO race fixture unavailable",
)
def test_fifo_swap_at_open_is_nonblocking_and_denied_before_read(
    tmp_path: Path,
    monkeypatch,
):
    path = tmp_path / "evidence.json"
    backup = tmp_path / "original.json"
    path.write_bytes(b"synthetic")
    native_open = cli.os.open
    native_fdopen = cli.os.fdopen
    observed_flags = []
    swapped = []

    class NoRead:
        def __init__(self, inner):
            self.inner = inner

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.inner.__exit__(*args)

        def fileno(self):
            return self.inner.fileno()

        def read(self, *_args, **_kwargs):
            raise AssertionError("nonregular FIFO must be denied before read")

    def replace_with_fifo_then_open(file, flags, *args, **kwargs):
        if Path(file) == path and not swapped:
            observed_flags.append(flags)
            path.rename(backup)
            os.mkfifo(path)
            swapped.append(True)
        return native_open(file, flags, *args, **kwargs)

    monkeypatch.setattr(cli.os, "open", replace_with_fifo_then_open)
    monkeypatch.setattr(cli.os, "fdopen", lambda fd, mode: NoRead(native_fdopen(fd, mode)))
    with pytest.raises(RuntimeError, match="changed before its bytes were read"):
        cli._read_bounded_evidence(path, max_bytes=64, label="fixture")
    assert swapped == [True]
    assert observed_flags[0] & os.O_NONBLOCK
    assert backup.read_bytes() == b"synthetic"
