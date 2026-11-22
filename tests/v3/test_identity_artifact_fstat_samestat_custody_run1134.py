"""Run1134: local identity artifacts pin descriptor and same-file primitives."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ark.learning import identity_artifact_verify as mod
from ark.learning.execution import canonical_json


def _artifact(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "identity.json"
    raw = canonical_json({"revision": "synthetic-fixture"})
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "target",
    (
        "live fstat",
        "captured fstat",
        "live samestat",
        "captured samestat",
    ),
)
def test_stat_dependency_substitution_is_denied_before_file_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    path, digest = _artifact(tmp_path)
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted stat dependency must not execute")

    if target == "live fstat":
        monkeypatch.setattr(mod.os, "fstat", forbidden)
    elif target == "captured fstat":
        monkeypatch.setattr(mod, "_ORIGINAL_FSTAT", forbidden)
    elif target == "live samestat":
        monkeypatch.setattr(mod.os.path, "samestat", forbidden)
    else:
        monkeypatch.setattr(mod, "_ORIGINAL_SAMESTAT", forbidden)

    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="identity artifact stat policy changed",
    ):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)

    assert calls == []


def test_reentrant_open_cannot_replace_fstat_before_descriptor_inspection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, digest = _artifact(tmp_path)
    original_open = Path.open
    calls: list[int] = []

    def forbidden(fd: int):
        calls.append(fd)
        raise AssertionError("substituted fstat must not execute")

    def switched_open(self: Path, *args, **kwargs):
        handle = original_open(self, *args, **kwargs)
        if self == path:
            monkeypatch.setattr(mod.os, "fstat", forbidden)
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="identity artifact stat policy changed",
    ):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)

    assert calls == []
