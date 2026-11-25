"""Run1398: PlannerJournal digest dependencies retain their import-time epoch.

Only synthetic local serializer callbacks are used. These checks do not grant
dispatch, replay, trusted-time, consent or external-effect authority.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.agency.planner_journal as journal_module


def _install_joint_digest_replacement(
    patch: pytest.MonkeyPatch,
    calls: list[str],
) -> None:
    def hostile(name: str):
        def reject(*_args: object, **_kwargs: object):
            calls.append(name)
            raise AssertionError("substituted PlannerJournal digest callback executed")

        return reject

    fake_sha256 = hostile("sha256")
    fake_dumps = hostile("dumps")
    fake_hashlib = SimpleNamespace(sha256=fake_sha256)
    fake_json = SimpleNamespace(dumps=fake_dumps)
    forged_epoch = (fake_hashlib, fake_sha256, fake_json, fake_dumps)

    patch.setattr(journal_module, "hashlib", fake_hashlib)
    patch.setattr(journal_module, "_ORIGINAL_HASHLIB", fake_hashlib)
    patch.setattr(journal_module, "_ORIGINAL_SHA256", fake_sha256)
    patch.setattr(journal_module, "json", fake_json)
    patch.setattr(journal_module, "_ORIGINAL_JSON", fake_json)
    patch.setattr(journal_module, "_ORIGINAL_DUMPS", fake_dumps)
    patch.setattr(journal_module, "_ORIGINAL_PLANNER_DIGEST_EPOCH", forged_epoch)


def test_joint_digest_module_alias_and_epoch_replacement_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    with monkeypatch.context() as patch:
        _install_joint_digest_replacement(patch, calls)

        with pytest.raises(
            journal_module.PlannerJournalError,
            match="digest dependencies changed",
        ):
            journal_module._canonical({"synthetic": "payload"})

    assert calls == []


def test_reentrant_digest_alias_replacement_is_denied_before_hash_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class ReentrantPayload(dict):
        def items(self):
            _install_joint_digest_replacement(patch, calls)
            return super().items()

    with monkeypatch.context() as patch:
        payload = ReentrantPayload({"synthetic": "payload"})
        with pytest.raises(
            journal_module.PlannerJournalError,
            match="digest dependencies changed",
        ):
            journal_module._digest(payload)

    assert calls == []
