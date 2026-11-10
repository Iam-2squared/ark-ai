"""Proactive fixture SQLite never invokes executable Path subclass hooks.

No notification, scheduler service, external compute or real tool backend.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


class ExecutablePath(type(Path("."))):
    def __fspath__(self) -> str:
        raise AssertionError("untrusted path __fspath__ executed")


@pytest.mark.parametrize("ingress", ("initialize", "prepare"))
def test_proactive_path_subclass_refused_before_sqlite(
    tmp_path: Path, ingress: str,
) -> None:
    target = tmp_path / "synthetic-proactive.sqlite"
    untrusted = ExecutablePath(str(target))
    if ingress == "initialize":
        with pytest.raises(TypeError, match="exact local Path"):
            SyntheticProactiveLedger(untrusted)
        assert not target.exists()
    else:
        ledger = SyntheticProactiveLedger(target)
        policy = SyntheticTriggerPolicy(
            "synthetic-owner", "synthetic", "fixture-due",
            1, "v1", 5, 100, 3,
        )
        ledger.path = untrusted
        with pytest.raises(
            SyntheticTriggerRejected, match="ledger path changed",
        ):
            ledger.prepare(
                policy,
                source_digest="a" * 64,
                observation_digest="b" * 64,
                observed_at_ms=10,
                now_ms=10,
            )
        assert target.is_file()


def test_normal_exact_path_still_bootstraps_offline_fixture(
    tmp_path: Path,
) -> None:
    target = tmp_path / "offline-trigger.sqlite"
    ledger = SyntheticProactiveLedger(target)
    assert ledger.path is target
    assert target.is_file()
