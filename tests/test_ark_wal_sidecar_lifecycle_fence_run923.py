"""Disposable ARK WAL diagnostics must not declare a mismatched sidecar OK.

These are synthetic TemporaryDirectory probes only. An anomaly never grants
auto-retry, real actions, private pathname disclosure or alias relaxation.
"""

from __future__ import annotations

import argparse
import runpy
from pathlib import Path

import pytest

_DIAG = runpy.run_path(
    str(
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "diagnose_ark_store_wal_last_close.py"
    )
)


@pytest.mark.parametrize("keeper", (False, True))
@pytest.mark.parametrize("kind", ("memory", "audit", "revocation"))
@pytest.mark.parametrize("corrupt_call", (3, 4))
def test_incoherent_sidecar_close_blocks_cold_reopen(
    monkeypatch, kind: str, keeper: bool, corrupt_call: int,
) -> None:
    namespace = _DIAG["probe_ark_store"].__globals__
    original_category = namespace["_category"]
    calls = 0

    def synthetic_sidecar_drift(info) -> str:
        nonlocal calls
        calls += 1
        observed = original_category(info)
        if calls == corrupt_call:
            if corrupt_call == 4:
                return "SINGLE_LINK"  # final close failed to unlink
            return "UNLINKED" if keeper else "SINGLE_LINK"
        return observed

    with monkeypatch.context() as patch:
        patch.setitem(namespace, "_category", synthetic_sidecar_drift)
        report = _DIAG["probe_ark_store"](kind=kind, keeper=keeper)

    if report["status"] in ("UNSUPPORTED", "NO_WAL", "NO_SHM"):
        pytest.skip("disposable WAL held descriptor unavailable")
    assert calls == 4
    assert report == {
        "status": "SIDECAR_LIFECYCLE_MISMATCH",
        "kind": kind,
        "keeper": keeper,
        "phase": "after_final_close",
        "auto_retry_authorized": False,
        "real_tool_dispatched": False,
        "alias_checks_relaxed": False,
        "user_paths_exported": False,
    }
    assert "fixture.sqlite" not in repr(report)
    assert "ark-disposable-wal-" not in repr(report)


@pytest.mark.parametrize("raw", ("1" * 10000, "9" * 10000, " " * 10000))
def test_disposable_iteration_parser_fails_before_unbounded_int(raw: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError, match="1..4"):
        _DIAG["bounded_count"](raw)
