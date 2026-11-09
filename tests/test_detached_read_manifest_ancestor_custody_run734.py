"""Detached READ manifests refuse symlinked and lexical ancestor escapes.

Disposable local fixtures only. Preflight does not prove atomic file custody,
real execution, external provenance or automatic replay authorization.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.disconnected_read_input_manifest import (
    ReadInputManifestRejected,
    load_read_input_manifest,
    write_read_input_manifest_once,
)

REQUEST = "req_" + "a" * 32
INPUTS = (("step_" + "1" * 16, "b" * 64),)


def test_regular_nested_absolute_manifest_round_trip(tmp_path: Path):
    target = tmp_path / "real" / "deep" / "expected.json"
    target.parent.mkdir(parents=True)
    saved = write_read_input_manifest_once(target, REQUEST, INPUTS)
    assert load_read_input_manifest(
        str(target), expected_sha256=saved.artifact_sha256,
    ) == saved
    assert saved.backend_dispatched is False
    assert saved.automatic_replay_authorized is False
    assert saved.independent_custody_proven is False


def test_symlinked_grandparent_refused_for_create_and_load(tmp_path: Path):
    real = tmp_path / "real"
    deep = real / "deep"
    deep.mkdir(parents=True)
    original = deep / "original.json"
    saved = write_read_input_manifest_once(original, REQUEST, INPUTS)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    redirected = alias / "deep" / "not_created.json"
    with pytest.raises(ReadInputManifestRejected, match="ancestor"):
        write_read_input_manifest_once(redirected, REQUEST, INPUTS)
    assert not (deep / "not_created.json").exists()
    with pytest.raises(ReadInputManifestRejected, match="ancestor"):
        load_read_input_manifest(
            alias / "deep" / "original.json",
            expected_sha256=saved.artifact_sha256,
        )
    assert load_read_input_manifest(original) == saved


@pytest.mark.parametrize("operation", ("write", "load"))
def test_dotdot_parent_traversal_denied_before_io(tmp_path: Path, operation: str):
    (tmp_path / "local").mkdir()
    target = tmp_path / "local" / ".." / "escaped.json"
    with pytest.raises(ReadInputManifestRejected, match="absolute path"):
        if operation == "write":
            write_read_input_manifest_once(target, REQUEST, INPUTS)
        else:
            load_read_input_manifest(target)
    assert not (tmp_path / "escaped.json").exists()


@pytest.mark.parametrize("operation", ("write", "load"))
def test_relative_path_denied_before_io(operation: str):
    target = Path("synthetic-read-manifest-relative.json")
    with pytest.raises(ReadInputManifestRejected, match="absolute path"):
        if operation == "write":
            write_read_input_manifest_once(target, REQUEST, INPUTS)
        else:
            load_read_input_manifest(target)


@pytest.mark.parametrize("operation", ("write", "load"))
def test_nondirectory_parent_denied_without_file_change(
    tmp_path: Path, operation: str,
):
    parent = tmp_path / "not_a_directory"
    parent.write_bytes(b"not a directory")
    target = parent / "expected.json"
    with pytest.raises(ReadInputManifestRejected, match="ancestor"):
        if operation == "write":
            write_read_input_manifest_once(target, REQUEST, INPUTS)
        else:
            load_read_input_manifest(target)
    assert parent.read_bytes() == b"not a directory"


@pytest.mark.parametrize("operation", ("write", "load"))
def test_custom_fspath_callback_is_not_executed(operation: str):
    calls = []

    class HostilePath:
        def __fspath__(self):
            calls.append("path callback")
            raise AssertionError("untrusted path callback executed")

    with pytest.raises(ReadInputManifestRejected, match="exact local path"):
        if operation == "write":
            write_read_input_manifest_once(HostilePath(), REQUEST, INPUTS)
        else:
            load_read_input_manifest(HostilePath())
    assert calls == []
