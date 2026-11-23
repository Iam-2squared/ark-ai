"""Run1136: V3 identity file hashing pins descriptor-stat dependencies."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import identity


def _payload(tmp_path: Path) -> Path:
    path = tmp_path / "identity-payload.bin"
    path.write_bytes(b"synthetic local identity payload")
    return path


def test_os_module_binding_substitution_is_denied_before_file_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _payload(tmp_path)
    calls: list[object] = []
    open_calls: list[Path] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted descriptor stat must not execute")

    def forbidden_open(self: Path, *args, **kwargs):
        open_calls.append(self)
        raise AssertionError("identity file must be rejected before open")

    proxy = SimpleNamespace(
        name=identity._ORIGINAL_OS_NAME,
        scandir=identity._ORIGINAL_SCANDIR,
        fstat=forbidden,
        path=SimpleNamespace(samestat=identity._ORIGINAL_SAMESTAT),
    )
    monkeypatch.setattr(identity, "os", proxy)
    monkeypatch.setattr(Path, "open", forbidden_open)

    with pytest.raises(ValueError, match="identity reparse-point policy changed"):
        identity.file_identity(path)

    assert calls == []
    assert open_calls == []


@pytest.mark.parametrize("target", ("captured fstat", "captured samestat"))
def test_captured_descriptor_dependency_substitution_is_denied_before_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    path = _payload(tmp_path)
    calls: list[object] = []
    open_calls: list[Path] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted descriptor dependency must not execute")

    def forbidden_open(self: Path, *args, **kwargs):
        open_calls.append(self)
        raise AssertionError("identity file must be rejected before open")

    if target == "captured fstat":
        monkeypatch.setattr(identity, "_ORIGINAL_FSTAT", forbidden)
    else:
        monkeypatch.setattr(identity, "_ORIGINAL_SAMESTAT", forbidden)
    monkeypatch.setattr(Path, "open", forbidden_open)

    with pytest.raises(ValueError, match="identity reparse-point policy changed"):
        identity.file_identity(path)

    assert calls == []
    assert open_calls == []


@pytest.mark.parametrize("target", ("captured fstat", "captured samestat"))
def test_reentrant_path_open_cannot_replace_descriptor_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    path = _payload(tmp_path)
    original_open = Path.open
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted descriptor dependency must not execute")

    def switched_open(self: Path, *args, **kwargs):
        handle = original_open(self, *args, **kwargs)
        if self == path:
            name = "_ORIGINAL_FSTAT" if target == "captured fstat" else "_ORIGINAL_SAMESTAT"
            monkeypatch.setattr(identity, name, forbidden)
        return handle

    monkeypatch.setattr(Path, "open", switched_open)
    with pytest.raises(ValueError, match="identity reparse-point policy changed"):
        identity.file_identity(path)

    assert calls == []


def test_identity_file_hash_still_matches_opened_local_bytes(tmp_path: Path) -> None:
    path = _payload(tmp_path)
    result = identity.file_identity(path)
    assert result.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result.bytes == path.stat().st_size


@pytest.mark.parametrize("target", ("live fstat", "live samestat"))
def test_live_stat_attribute_substitution_is_denied_by_policy_guard(
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    calls: list[object] = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("substituted live stat dependency must not execute")

    original_fstat = identity._ORIGINAL_FSTAT
    original_samestat = identity._ORIGINAL_SAMESTAT
    proxy_path = SimpleNamespace(
        samestat=forbidden if target == "live samestat" else original_samestat,
    )
    proxy_os = SimpleNamespace(
        name=identity._ORIGINAL_OS_NAME,
        scandir=identity._ORIGINAL_SCANDIR,
        fstat=forbidden if target == "live fstat" else original_fstat,
        path=proxy_path,
    )
    monkeypatch.setattr(identity, "os", proxy_os)
    monkeypatch.setattr(identity, "_ORIGINAL_OS", proxy_os)
    monkeypatch.setattr(identity, "_ORIGINAL_OS_PATH", proxy_path)

    with pytest.raises(ValueError, match="identity reparse-point policy changed"):
        identity._require_original_reparse_point_policy(
            _original_os=proxy_os,
            _original_os_path=proxy_path,
            _original_scandir=identity._ORIGINAL_SCANDIR,
            _original_fstat=original_fstat,
            _original_samestat=original_samestat,
            _original_os_name=identity._ORIGINAL_OS_NAME,
        )

    assert calls == []
