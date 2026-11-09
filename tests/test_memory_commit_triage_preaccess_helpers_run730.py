"""COMMIT-UNKNOWN manual triage never delegates private Memory to forged helpers.

All effects are disposable local SQLite fixture operations, never external tools
or an implicit retry after an uncertain COMMIT.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as generation
from ark.memory import postcommit_uncertainty_review as triage


def _fixture(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "triage.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("private-owner", "private-namespace")
    store.put(MemoryWrite(scope, "source", "secret original data"))
    token = generation.observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(scope, "source", "secret proposed data")
    return store, scope, token, proposed


@pytest.mark.parametrize("surface", (
    "sqlite_module", "identity_helper", "token_helper",
    "input_validator", "token_validator",
))
def test_private_triage_never_enters_forged_helper(
    tmp_path, monkeypatch, surface,
):
    store, scope, token, proposed = _fixture(tmp_path)
    called = []

    def hostile(*_args, **_kwargs):
        called.append(surface)
        raise AssertionError("forged triage helper accessed private Memory")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", hostile)
        if surface == "sqlite_module":
            patch.setattr(triage, "sqlite3", SimpleNamespace(Error=RuntimeError))
        elif surface == "identity_helper":
            patch.setattr(triage, "deterministic_memory_id", hostile)
        elif surface == "token_helper":
            patch.setattr(triage, "_token_fields", hostile)
        elif surface == "input_validator":
            patch.setattr(triage, "_require_original_generation_inputs", hostile)
        else:
            patch.setattr(triage, "_require_original_token_denials", hostile)
        with pytest.raises(
            triage.MemoryCommitTriageRejected,
            match="Memory triage input or denial changed",
        ):
            triage.review_uncertain_memory_commit(
                store, proposed, retained_before=token,
            )
    assert called == []
    # The hostile hook is gone. The original row and audit prefix remain intact.
    saved = store.get(generation.deterministic_memory_id(scope, "source"), scope)
    assert saved.content == "secret original data"
    assert saved.revision == 1
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_original_manual_triage_remains_non_authorizing(tmp_path):
    store, scope, token, proposed = _fixture(tmp_path)
    triaged = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=token,
    )
    assert triaged.disposition == "LOCAL_UNCHANGED"
    assert triaged.automatic_retry_authorized is False
    assert triaged.write_authorized is False
    assert triaged.caller_attribution_proven is False
    assert triaged.trusted_clock_proven is False
