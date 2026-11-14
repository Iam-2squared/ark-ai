"""Recovery review output cannot acquire executable slotted carrier hooks.

Only synthetic, disconnected SQLite hashes are used. A reported witness never
authenticates consent, context access, a writer or an external retry.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.personal_context_replay_recovery as recovery
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger

_FIELDS = ("retained_count", "observed_count", "status", "comparison_sha256")
_HOOKS = ("__init__", "__getattribute__", "__getattr__")


@pytest.mark.parametrize("name", _FIELDS + _HOOKS)
def test_preinstalled_report_hook_rejected_before_sqlite_or_execution(
    tmp_path, monkeypatch, name,
):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "report-original.sqlite", create=True,
    )
    retained = ledger.witness()
    called = []

    def poisoned(*_args, **_kwargs):
        called.append(name)
        raise AssertionError("untrusted report hook was executed")

    def no_sqlite(*_args, **_kwargs):
        raise AssertionError("rejected hook must not reopen SQLite")

    replacement = property(poisoned) if name in _FIELDS else poisoned
    with monkeypatch.context() as patch:
        patch.setattr(
            recovery.OfflineContextRecoveryReview, name,
            replacement, raising=False,
        )
        patch.setattr(type(ledger), "_open", no_sqlite)
        with pytest.raises(
            recovery.OfflineContextRecoveryRejected,
            match="review result gained authority",
        ):
            recovery.review_restarted_context_replay(ledger, retained)

    assert called == []


@pytest.mark.parametrize("phase", ("witness", "durable_read", "digest"))
def test_reentrant_report_slot_replacement_rejected_without_getter(
    tmp_path, monkeypatch, phase,
):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "reentrant-report.sqlite", create=True,
    )
    retained = ledger.witness()
    called = []

    def poisoned(_self):
        called.append(phase)
        raise AssertionError("forged report descriptor executed")

    with monkeypatch.context() as patch:
        original = (
            ledger.witness if phase == "witness" else
            recovery._inspect if phase == "durable_read" else
            recovery.json.dumps
        )

        def inject(*args, **kwargs):
            result = original(*args, **kwargs)
            patch.setattr(
                recovery.OfflineContextRecoveryReview,
                "comparison_sha256", property(poisoned),
            )
            return result

        if phase == "witness":
            patch.setattr(ledger, "witness", inject)
        elif phase == "durable_read":
            patch.setattr(recovery, "_inspect", inject)
        else:
            patch.setattr(recovery.json, "dumps", inject)

        with pytest.raises(
            recovery.OfflineContextRecoveryRejected,
            match=(
                "context replay digest implementation changed"
                if phase == "digest" else "review result gained authority"
            ),
        ):
            recovery.review_restarted_context_replay(ledger, retained)

    assert called == []


def test_inherited_allocation_hook_poison_is_process_isolated():
    # Patching an inherited CPython __new__ can poison later allocations
    # even after monkeypatch teardown. Never do so inside shared pytest.
    program = textwrap.dedent("""
        from pathlib import Path
        from tempfile import TemporaryDirectory
        import ark.personal_context_replay_recovery as recovery
        from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger

        with TemporaryDirectory() as directory:
            ledger = DisconnectedContextReplayLedger(
                Path(directory) / "witness.sqlite", create=True,
            )
            retained = ledger.witness()
            called = []

            def poison(*args, **kwargs):
                called.append("new")
                raise AssertionError("poisoned allocation executed")

            recovery.OfflineContextRecoveryReview.__new__ = staticmethod(poison)
            try:
                recovery.review_restarted_context_replay(ledger, retained)
            except recovery.OfflineContextRecoveryRejected as exc:
                assert "review result gained authority" in str(exc)
            else:
                raise AssertionError("poisoned allocation accepted")
            assert called == []
    """)
    completed = subprocess.run(
        [sys.executable, "-c", program],
        check=False, capture_output=True, text=True, timeout=20,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_healthy_restart_review_is_inert(tmp_path):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "clean-report.sqlite", create=True,
    )
    review = recovery.review_restarted_context_replay(ledger, ledger.witness())
    assert review.status == "UNCHANGED_LOCAL_HISTORY"
    assert review.retained_count == review.observed_count == 0
    assert review.historical_prefix_proven is False
    assert review.consent_verified is False
    assert review.context_disclosure_authorized is False
    assert review.tool_dispatch_authorized is False
    assert review.automatic_replay_authorized is False
