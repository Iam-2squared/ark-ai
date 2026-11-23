"""Run1134: local identity artifacts pin descriptor and same-file primitives."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import identity_artifact_verify as mod
from ark.learning.execution import canonical_json


def _artifact(tmp_path: Path) -> tuple[Path, str]:
    path = tmp_path / "identity.json"
    raw = canonical_json({"revision": "synthetic-fixture"})
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest()


def test_os_module_binding_substitution_is_denied_by_policy_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted stat dependency must not execute")

    proxy = SimpleNamespace(
        fstat=forbidden,
        path=SimpleNamespace(samestat=forbidden),
    )
    monkeypatch.setattr(mod, "os", proxy)
    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="identity artifact stat policy changed",
    ):
        mod._require_original_stat_policy()

    assert calls == []


@pytest.mark.parametrize("target", ("captured fstat", "captured samestat"))
def test_captured_stat_dependency_substitution_is_denied_before_file_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    path, digest = _artifact(tmp_path)
    calls: list[object] = []
    open_calls: list[Path] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted stat dependency must not execute")

    def forbidden_open(self: Path, *args, **kwargs):
        open_calls.append(self)
        raise AssertionError("identity artifact must be rejected before file open")

    if target == "captured fstat":
        monkeypatch.setattr(mod, "_ORIGINAL_FSTAT", forbidden)
    else:
        monkeypatch.setattr(mod, "_ORIGINAL_SAMESTAT", forbidden)
    monkeypatch.setattr(Path, "open", forbidden_open)

    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="identity artifact stat policy changed",
    ):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)

    assert calls == []
    assert open_calls == []


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
            monkeypatch.setattr(mod, "_ORIGINAL_FSTAT", forbidden)
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(
        mod.LocalIdentityArtifactRejected,
        match="identity artifact stat policy changed",
    ):
        mod.verify_local_identity_artifact(path, retained_sha256=digest)

    assert calls == []
