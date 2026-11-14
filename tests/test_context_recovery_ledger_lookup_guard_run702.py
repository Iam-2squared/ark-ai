"""Personal Context restart refuses replaced SQLite ledger lookup hooks.

Synthetic hash-only identity fixtures; no real context access or dispatch.
Class-slot mutations run in child Python processes to avoid CPython cache
contamination of unrelated tests.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger
from ark.personal_context_replay_recovery import review_restarted_context_replay


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
@pytest.mark.parametrize("phase", ("before", "after_witness"))
def test_replaced_ledger_lookup_hook_is_refused_before_private_path_read(
    hook, phase,
):
    script = textwrap.dedent(
        """
        from pathlib import Path
        from tempfile import TemporaryDirectory
        import sys

        import ark.personal_context_replay_recovery as recovery
        from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger

        hook, phase = sys.argv[1:]
        with TemporaryDirectory() as directory:
            ledger = DisconnectedContextReplayLedger(
                Path(directory) / "synthetic-context.db", create=True,
            )
            retained = ledger.witness()
            hits = []

            def rogue(*_args, **_kwargs):
                hits.append(hook)
                raise AssertionError("untrusted ledger lookup executed")

            if phase == "before":
                setattr(DisconnectedContextReplayLedger, hook, rogue)
            else:
                original = ledger.witness

                def replace_during_witness():
                    observed = original()
                    setattr(DisconnectedContextReplayLedger, hook, rogue)
                    return observed

                ledger.witness = replace_during_witness

            try:
                recovery.review_restarted_context_replay(ledger, retained)
            except recovery.OfflineContextRecoveryRejected as exc:
                assert "ledger access hook changed" in str(exc), str(exc)
            else:
                raise AssertionError("mutated ledger hook accepted")
            assert hits == []
        """
    )
    process = subprocess.run(
        [sys.executable, "-c", script, hook, phase],
        capture_output=True, text=True, check=False, timeout=25,
    )
    assert process.returncode == 0, process.stdout + process.stderr


def test_unmodified_recovery_remains_content_free_and_denial_only(tmp_path):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "synthetic-context.db", create=True,
    )
    result = review_restarted_context_replay(ledger, ledger.witness())
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.retained_count == result.observed_count == 0
    assert result.context_disclosure_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
