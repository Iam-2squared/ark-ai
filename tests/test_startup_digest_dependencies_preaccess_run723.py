"""Disconnected startup must reject changed hash/JSON code before input reads.

The supplied inputs deliberately raise if accessed; no SQLite connection,
registered backend, actual file, real clock, or private context is opened.
"""

from __future__ import annotations

import pytest

import ark.disconnected_local_readiness as readiness


class _MustNotRead:
    def __getattribute__(self, _name):
        raise AssertionError("startup read private input before dependency check")


@pytest.mark.parametrize(
    "dependency", ("sha256", "json.dumps", "domain"),
)
def test_preinstalled_dependency_change_is_refused_before_private_inputs(
    monkeypatch: pytest.MonkeyPatch, dependency: str,
) -> None:
    attempted: list[str] = []

    def hostile(*_args, **_kwargs):
        attempted.append(dependency)
        raise AssertionError("substituted callback executed")

    with monkeypatch.context() as patch:
        if dependency == "sha256":
            patch.setattr(readiness.hashlib, "sha256", hostile)
        elif dependency == "json.dumps":
            patch.setattr(readiness.json, "dumps", hostile)
        else:
            patch.setattr(
                readiness, "_DOMAIN", bytes(bytearray(readiness._DOMAIN)),
            )
        sentinel = _MustNotRead()
        with pytest.raises(
            readiness.DisconnectedLocalReadinessRejected,
            match="startup digest dependencies changed",
        ):
            readiness.review_disconnected_local_readiness(
                sentinel, sentinel, sentinel, sentinel, sentinel, (sentinel,),
                observed_at_ms=0,
            )
    assert attempted == []


def test_original_digest_dependency_guard_is_inert() -> None:
    readiness._require_original_denials()
