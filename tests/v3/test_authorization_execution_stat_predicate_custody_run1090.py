"""Run1090: V3 authorization and snapshot readers pin stat classification.

Synthetic temporary files only. No model, GPU, network, Candidate or
protected evaluation is opened.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.learning.authorization as authorization
import ark.learning.execution as execution


@pytest.mark.parametrize("predicate", ("S_ISREG", "S_ISLNK"))
def test_authorization_stat_predicate_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch, predicate,
):
    target = tmp_path / "packet.json"
    monkeypatch.setattr(authorization.stat, predicate, lambda mode: False)

    def forbidden_lstat(_path):
        raise AssertionError("authorization path inspected after stat substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._write_new_authorization_packet(
            target, {"candidate_created": False},
        )


def test_authorization_stat_module_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch,
):
    target = tmp_path / "packet.json"
    monkeypatch.setattr(authorization, "stat", SimpleNamespace())

    def forbidden_lstat(_path):
        raise AssertionError("authorization path inspected after stat module replacement")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._write_new_authorization_packet(
            target, {"candidate_created": False},
        )


def test_authorization_reparse_metadata_callback_cannot_replace_predicate(
    monkeypatch,
):
    class MutatingMetadata:
        @property
        def st_file_attributes(self):
            monkeypatch.setattr(
                authorization.stat, "S_ISLNK", lambda mode: False,
            )
            return 0

        @property
        def st_mode(self):
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._is_reparse_point(MutatingMetadata())


def test_authorization_mode_callback_cannot_replace_regular_predicate(monkeypatch):
    class MutatingMetadata:
        @property
        def st_mode(self):
            monkeypatch.setattr(
                authorization.stat, "S_ISREG", lambda mode: True,
            )
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._is_regular_file(MutatingMetadata())


def test_authorization_open_callback_is_rechecked_before_packet_write(
    tmp_path, monkeypatch,
):
    target = tmp_path / "packet.json"
    original_open = Path.open

    def switched_open(self, *args, **kwargs):
        handle = original_open(self, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        if self == target and mode == "xb":
            monkeypatch.setattr(
                authorization.stat, "S_ISREG", lambda value: False,
            )
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._write_new_authorization_packet(
            target, {"candidate_created": False},
        )
    assert target.read_bytes() == b""


@pytest.mark.parametrize("predicate", ("S_ISREG", "S_ISLNK"))
def test_execution_stat_predicate_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch, predicate,
):
    source = tmp_path / "snapshot.json"
    source.write_bytes(b'{"synthetic": true}')
    monkeypatch.setattr(execution.stat, predicate, lambda mode: False)

    def forbidden_lstat(_path):
        raise AssertionError("snapshot path inspected after stat substitution")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="snapshot stat policy changed"):
        execution.load_snapshot(source)


def test_execution_stat_module_rebinding_is_rejected_before_lstat(
    tmp_path, monkeypatch,
):
    source = tmp_path / "snapshot.json"
    source.write_bytes(b'{"synthetic": true}')
    monkeypatch.setattr(execution, "stat", SimpleNamespace())

    def forbidden_lstat(_path):
        raise AssertionError("snapshot path inspected after stat module replacement")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(ValueError, match="snapshot stat policy changed"):
        execution.load_snapshot(source)


def test_execution_mode_callback_cannot_replace_regular_predicate(monkeypatch):
    class MutatingMetadata:
        @property
        def st_mode(self):
            monkeypatch.setattr(execution.stat, "S_ISREG", lambda mode: True)
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="snapshot stat policy changed"):
        execution._is_regular_file(MutatingMetadata())


def test_execution_reparse_metadata_callback_cannot_replace_symlink_predicate(
    monkeypatch,
):
    class MutatingMetadata:
        @property
        def st_file_attributes(self):
            monkeypatch.setattr(execution.stat, "S_ISLNK", lambda mode: False)
            return 0

        @property
        def st_mode(self):
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="snapshot stat policy changed"):
        execution._is_reparse_point(MutatingMetadata())


def test_execution_open_callback_is_rechecked_before_private_read(
    tmp_path, monkeypatch,
):
    source = tmp_path / "snapshot.json"
    source.write_bytes(b'{"synthetic": true}')
    original_open = Path.open
    reads = []

    class ReadSpy:
        def __init__(self, handle):
            self._handle = handle

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self._handle.__exit__(*args)

        def fileno(self):
            return self._handle.fileno()

        def read(self, *args, **kwargs):
            reads.append(True)
            return self._handle.read(*args, **kwargs)

    def switched_open(self, *args, **kwargs):
        handle = original_open(self, *args, **kwargs)
        mode = args[0] if args else kwargs.get("mode", "r")
        if self == source and mode == "rb":
            monkeypatch.setattr(
                execution.stat, "S_ISREG", lambda value: False,
            )
            return ReadSpy(handle)
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(ValueError, match="snapshot stat policy changed"):
        execution.load_snapshot(source)
    assert reads == []


def test_execution_decoder_callback_cannot_replace_stat_policy(
    tmp_path, monkeypatch,
):
    source = tmp_path / "snapshot.json"
    source.write_bytes(b'{"synthetic": true}')
    original_loads = execution.json.loads

    def switched_loads(*args, **kwargs):
        parsed = original_loads(*args, **kwargs)
        monkeypatch.setattr(
            execution.stat, "S_ISREG", lambda mode: False,
        )
        return parsed

    monkeypatch.setattr(execution.json, "loads", switched_loads)
    with pytest.raises(ValueError, match="snapshot stat policy changed"):
        execution.load_snapshot(source)
