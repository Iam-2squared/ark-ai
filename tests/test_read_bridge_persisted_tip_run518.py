"""A detached READ bridge must bind its claimed tip to persisted local bytes.

All operations are SQLite-only mock fixtures. An invalid post-COMMIT witness
does not roll back a row or license any automatic retry or external READ.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from test_disconnected_read_receipt_bridge_run478 import STEP, _case

import ark.agency.disconnected_read_journal as journal_module
import ark.agency.disconnected_read_receipt_bridge as bridge


def _expected(request, result, binding):
    return bridge.prepare_disconnected_read_receipt(STEP, request, result, binding)


def test_real_append_retains_exact_tip_and_is_still_inert(tmp_path: Path) -> None:
    request, result, binding = _case()
    original = journal_module.genesis_witness()
    expected_tip = journal_module._chain(
        original.tip_sha256, 1, _expected(request, result, binding),
    )
    with journal_module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        saved = bridge.append_disconnected_fixture_read(
            journal, original, STEP, request, result, binding,
        )
        assert saved.count == 1
        assert saved.tip_sha256 == expected_tip
        assert journal.verify(saved) == saved
        assert saved.effect_proven is False
        assert saved.replay_authorized is False


@pytest.mark.parametrize("mode", ("wrong_tip", "claimed_commit", "different_row"))
def test_forged_post_append_success_does_not_pass_persisted_receipt_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str,
) -> None:
    request, result, binding = _case()
    original = journal_module.genesis_witness()
    expected = _expected(request, result, binding)
    expected_tip = journal_module._chain(original.tip_sha256, 1, expected)
    actual_append = journal_module.DisconnectedReadJournal.append

    def forged(self, receipt, retained):
        if mode == "wrong_tip":
            return journal_module.ReadJournalWitness(1, "e" * 64)
        if mode == "claimed_commit":
            return journal_module.ReadJournalWitness(1, expected_tip)
        alternate = replace(receipt, input_digest="f" * 64)
        assert alternate != receipt
        return actual_append(self, alternate, retained)

    with journal_module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        with monkeypatch.context() as patch:
            patch.setattr(journal_module.DisconnectedReadJournal, "append", forged)
            with pytest.raises(
                bridge.DisconnectedReadBridgeRejected,
                match="untrusted|post-append",
            ):
                bridge.append_disconnected_fixture_read(
                    journal, original, STEP, request, result, binding,
                )
        if mode == "different_row":
            # A different row may have committed: inspect, never retry.
            actual = journal._scan()
            assert actual.count == 1
            assert actual.tip_sha256 != expected_tip
        else:
            assert journal.verify(original).count == 0


def test_witness_equal_value_replacement_during_post_append_verify_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, result, binding = _case()
    original = journal_module.genesis_witness()
    expected_tip = journal_module._chain(
        original.tip_sha256, 1, _expected(request, result, binding),
    )
    real_verify = journal_module.DisconnectedReadJournal.verify

    def mutate_after_verify(self, retained):
        verified = real_verify(self, retained)
        old = retained.tip_sha256
        replacement = ("_" + old)[1:]
        assert replacement == old and replacement is not old
        object.__setattr__(retained, "tip_sha256", replacement)
        return verified

    with journal_module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        with monkeypatch.context() as patch:
            patch.setattr(
                journal_module.DisconnectedReadJournal, "verify", mutate_after_verify,
            )
            with pytest.raises(
                bridge.DisconnectedReadBridgeRejected,
                match="untrusted READ post-append evidence",
            ):
                bridge.append_disconnected_fixture_read(
                    journal, original, STEP, request, result, binding,
                )
        assert journal.verify(journal_module.ReadJournalWitness(1, expected_tip)).count == 1


def test_untrusted_post_append_verify_result_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, result, binding = _case()
    original = journal_module.genesis_witness()
    with journal_module.DisconnectedReadJournal.create(tmp_path / "read.db") as journal:
        with monkeypatch.context() as patch:
            patch.setattr(
                journal_module.DisconnectedReadJournal,
                "verify", lambda self, retained: original,
            )
            with pytest.raises(
                bridge.DisconnectedReadBridgeRejected,
                match="untrusted READ post-append evidence",
            ):
                bridge.append_disconnected_fixture_read(
                    journal, original, STEP, request, result, binding,
                )
        expected_tip = journal_module._chain(
            original.tip_sha256, 1, _expected(request, result, binding),
        )
        assert journal.verify(journal_module.ReadJournalWitness(1, expected_tip)).count == 1
