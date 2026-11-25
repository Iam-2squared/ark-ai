"""Run1376: retain packet path-policy guard identity across file callbacks."""

from pathlib import Path

import pytest
from test_authorization_packet_file_review_run529 import _saved_packet

from ark.learning import authorization_packet_file_review as mod


def test_preinstalled_path_guard_and_alias_replacement_fails_before_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, path, digest = _saved_packet(tmp_path)
    calls: list[str] = []

    def substituted_guard() -> None:
        calls.append("guard")

    def forbidden_read(*_args: object, **_kwargs: object) -> None:
        calls.append("read")
        raise AssertionError("packet read must not start after guard replacement")

    monkeypatch.setattr(mod, "_require_original_path_policy", substituted_guard)
    monkeypatch.setattr(mod, "_ORIGINAL_PATH_POLICY_GUARD", substituted_guard)
    monkeypatch.setattr(mod, "_read_exact_local_packet", forbidden_read)

    with pytest.raises(
        mod.LocalPacketBindingRejected,
        match="review packet path-policy guard changed",
    ):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )

    assert calls == []


def test_reentrant_path_guard_replacement_fails_before_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, path, digest = _saved_packet(tmp_path)
    original_lstat = Path.lstat
    rebound: list[bool] = []
    opened: list[object] = []

    def substituted_guard() -> None:
        return None

    def rebind_after_lstat(target: Path):
        result = original_lstat(target)
        if target == path:
            monkeypatch.setattr(mod, "_require_original_path_policy", substituted_guard)
            monkeypatch.setattr(mod, "_ORIGINAL_PATH_POLICY_GUARD", substituted_guard)
            rebound.append(True)
        return result

    def forbidden_open(file: object, *_args: object, **_kwargs: object) -> None:
        opened.append(file)
        raise AssertionError("open must not follow reentrant path guard replacement")

    monkeypatch.setattr(Path, "lstat", rebind_after_lstat)
    monkeypatch.setattr(mod.os, "open", forbidden_open)

    with pytest.raises(
        mod.LocalPacketBindingRejected,
        match="review packet path-policy guard changed",
    ):
        mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )

    assert rebound == [True]
    assert opened == []
