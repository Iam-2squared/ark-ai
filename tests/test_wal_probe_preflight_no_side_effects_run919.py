"""Disposable WAL diagnostic rejects hostile arguments before any filesystem I/O.

This is a static preflight proof only, not a successful last-close diagnosis,
WAL repair, custody attestation or permission to retry an unknown operation.
"""

from __future__ import annotations

import argparse
import runpy
from pathlib import Path

import pytest

_DIAG = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts"
        / "diagnose_ark_store_wal_last_close.py")
)


class _HostileIdentity:
    def __eq__(self, _other):
        raise AssertionError("untrusted equality must not run")

    def __hash__(self):
        raise AssertionError("untrusted hash must not run")


class _StrAlias(str):
    def __eq__(self, _other):
        raise AssertionError("str subclass comparison must not run")


@pytest.mark.parametrize(
    ("kind", "keeper"),
    (
        (_HostileIdentity(), False),
        (_StrAlias("memory"), False),
        ("unknown", False),
        ("memory", 1),
        ("audit", "false"),
    ),
)
def test_invalid_probe_arguments_never_touch_temp_store_or_subprocess(
    monkeypatch, kind, keeper,
):
    globals_ = _DIAG["probe_ark_store"].__globals__

    def forbidden(*_args, **_kwargs):
        pytest.fail("invalid diagnostic arguments must not create processes/files")

    with monkeypatch.context() as patch:
        patch.setattr(globals_["tempfile"], "TemporaryDirectory", forbidden)
        patch.setattr(globals_["subprocess"], "Popen", forbidden)
        with pytest.raises(ValueError):
            _DIAG["probe_ark_store"](kind=kind, keeper=keeper)


@pytest.mark.parametrize("raw", ("0", "5", "1.0", "x", "9" * 10000))
def test_cli_iterations_reject_out_of_budget_values(raw):
    with pytest.raises(argparse.ArgumentTypeError):
        _DIAG["bounded_count"](raw)


@pytest.mark.parametrize("raw, expected", (("1", 1), ("4", 4)))
def test_cli_iterations_accept_only_bounded_disposable_runs(raw, expected):
    assert _DIAG["bounded_count"](raw) == expected
