"""Native SQLite path admission for offline expired-slot quarantine journals.

No paid service, execution or scheduler authority; malformed paths never reach
SQLite or filesystem lookup. The valid fixture is disposable local SQLite.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import ark.disconnected_schedule_quarantine_ledger as module
from ark.disconnected_schedule_quarantine_ledger import (
    DisconnectedScheduleQuarantineLedger,
    QuarantinePolicy,
    ScheduleQuarantineRejected,
    genesis_quarantine_witness,
)


def _policy() -> QuarantinePolicy:
    return QuarantinePolicy("a" * 64, 10_000, 5_000, 3, 500)


@pytest.mark.parametrize("kind", ("basename", "ancestor"))
@pytest.mark.parametrize("create", (False, True))
def test_nul_in_path_rejected_before_any_file_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str, create: bool,
) -> None:
    if kind == "basename":
        path = tmp_path / "quar\x00antine.sqlite"
    else:
        path = tmp_path / "unsafe\x00ancestor" / "quarantine.sqlite"
    calls = []

    def forbidden_lstat(self: Path):
        calls.append(self)
        raise AssertionError("malformed path reached lstat")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(ScheduleQuarantineRejected, match="absolute exact fixture path"):
            DisconnectedScheduleQuarantineLedger(path, policy=_policy(), create=create)
    assert calls == []


@pytest.mark.parametrize("create", (False, True))
def test_multibyte_filename_overflow_rejected_before_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, create: bool,
) -> None:
    path = tmp_path / ("界" * 1400 + ".sqlite")
    assert len(str(path)) < 4096
    assert len(os.fsencode(path)) + len(b"-journal") > 4096
    calls = []

    def forbidden_lstat(self: Path):
        calls.append(self)
        raise AssertionError("oversize path reached lstat")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(ScheduleQuarantineRejected, match="path byte budget"):
            DisconnectedScheduleQuarantineLedger(path, policy=_policy(), create=create)
    assert calls == []


def test_journal_sibling_overflow_rejected_even_if_main_fits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    prefix = tmp_path
    while len(os.fsencode(prefix)) + 202 <= 4091:
        prefix = prefix / ("d" * 200)
    remaining = 4092 - len(os.fsencode(prefix)) - 1
    assert 1 <= remaining <= 201
    path = prefix / ("q" * remaining)
    assert len(os.fsencode(path)) == 4092

    def forbidden_lstat(self: Path):
        raise AssertionError("journal overflow reached lstat")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(ScheduleQuarantineRejected, match="path byte budget"):
            DisconnectedScheduleQuarantineLedger(path, policy=_policy(), create=True)


def test_replaced_native_encoder_refused_before_its_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def injected_encoder(value: object) -> bytes:
        calls.append(value)
        return b"fake"

    with monkeypatch.context() as patch:
        patch.setattr(module.os, "fsencode", injected_encoder)
        with pytest.raises(ScheduleQuarantineRejected, match="protocol changed"):
            DisconnectedScheduleQuarantineLedger(
                tmp_path / "quarantine.sqlite", policy=_policy(), create=True,
            )
    assert calls == []


def test_normal_disconnected_quarantine_restart_is_still_read_only(
    tmp_path: Path,
) -> None:
    path = tmp_path / "quarantine.sqlite"
    policy = _policy()
    DisconnectedScheduleQuarantineLedger(path, policy=policy, create=True)
    restarted = DisconnectedScheduleQuarantineLedger(path, policy=policy)
    witness = genesis_quarantine_witness(policy)
    assert restarted.inspect(retained=witness) == witness
    assert witness.independently_authenticated is False
