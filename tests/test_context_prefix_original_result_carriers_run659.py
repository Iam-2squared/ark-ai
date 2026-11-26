"""Retained-prefix reports reject executable exact-class slots before access.

Only disconnected synthetic Context request IDs and SQLite fixture hashes
are involved. No consent, private text disclosure or replay authority exists.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest
from test_personal_context_retained_replay_prefix_run511 import _first

import ark.personal_context_replay_prefix_review as prefix

_FIELDS = (
    "retained_count", "current_count", "status",
    "current_chain_sha256", "review_sha256",
)
_HOOKS = ("__init__", "__getattribute__", "__getattr__")


@pytest.mark.parametrize("name", _FIELDS + _HOOKS)
def test_replaced_report_slot_is_rejected_before_sqlite_and_execution(
    tmp_path, monkeypatch, name,
):
    ledger, retained = _first(tmp_path)
    invoked = []

    def untrusted(*_args, **_kwargs):
        invoked.append(name)
        raise AssertionError("counterfeit prefix result executed")

    replacement = property(untrusted) if name in _FIELDS else untrusted

    def forbidden_db(*_args, **_kwargs):
        raise AssertionError("unsafe output definition reached SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(prefix.OfflineContextPrefixReview, name, replacement, raising=False)
        patch.setattr(type(ledger), "_open", forbidden_db)
        with pytest.raises(prefix.OfflineContextPrefixRejected, match="authority"):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    assert invoked == []


@pytest.mark.parametrize("phase", ("before_hash", "after_hash"))
def test_hashing_reentry_must_not_execute_substituted_result_slot(
    tmp_path, monkeypatch, phase,
):
    ledger, retained = _first(tmp_path)
    invoked = []
    original = prefix.json.dumps
    original_hash = prefix.hashlib.sha256

    def poison(_self):
        invoked.append("read")
        raise AssertionError("result field access executed injected property")

    def inject_dumps(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(
            prefix.OfflineContextPrefixReview, "review_sha256", property(poison),
        )
        return result

    def inject_hash(*args, **kwargs):
        monkeypatch.setattr(
            prefix.OfflineContextPrefixReview, "review_sha256", property(poison),
        )
        return original_hash(*args, **kwargs)

    with monkeypatch.context() as patch:
        if phase == "before_hash":
            patch.setattr(prefix.json, "dumps", inject_dumps)
        else:
            patch.setattr(prefix.hashlib, "sha256", inject_hash)
        with pytest.raises(
            prefix.OfflineContextPrefixRejected, match="digest implementation changed",
        ):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    assert invoked == []


def test_inherited_result_allocation_is_isolated_in_child_python():
    # Never patch inherited __new__ in the shared pytest interpreter.
    script = textwrap.dedent("""
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger
        import ark.personal_context_replay_prefix_review as prefix

        with TemporaryDirectory() as temp:
            ledger = DisconnectedContextReplayLedger(
                Path(temp) / "prefix.sqlite", create=True,
            )
            retained = ledger.witness()
            calls = []

            def poison(*args, **kwargs):
                calls.append("executed")
                raise AssertionError("injected allocation was called")

            prefix.OfflineContextPrefixReview.__new__ = staticmethod(poison)
            try:
                prefix.review_retained_context_replay_prefix(ledger, retained)
            except prefix.OfflineContextPrefixRejected as exc:
                assert "authority" in str(exc)
            else:
                raise AssertionError("injected allocation accepted")
            assert calls == []
    """)
    process = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_original_report_without_mutation_still_denies_all_authorities(tmp_path):
    ledger, retained = _first(tmp_path)
    result = prefix.review_retained_context_replay_prefix(ledger, retained)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.retained_count == result.current_count == 1
    for name in prefix._DENIAL_NAMES:
        assert getattr(result, name) is False
