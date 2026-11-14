"""Ambiguous Memory COMMIT triage must reject swapped report code before SQLite.

Only disposable SQLite fixture writes; matching row contents are never consent,
caller attribution, permission to replay, or authenticated commit evidence.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

import ark.memory.postcommit_uncertainty_review as triage


@pytest.mark.parametrize(
    "name", triage._REPORT_FIELDS + ("__getattribute__", "__getattr__"),
)
def test_preinstalled_report_slot_or_lookup_never_executes(
    tmp_path, monkeypatch, name,
):
    store, _, saved, retained, proposed = make_case(tmp_path)
    hits = []

    def forbidden(*_args, **_kwargs):
        hits.append(name)
        raise AssertionError("forged Memory report getter executed")

    with monkeypatch.context() as patch:
        patch.setattr(triage.MemoryCommitTriage, name, forbidden, raising=False)

        def forbidden_sqlite():
            raise AssertionError("private SQLite was touched before preflight")

        patch.setattr(store, "_connect_readonly", forbidden_sqlite)
        with pytest.raises(
            triage.MemoryCommitTriageRejected,
            match="Memory triage input or denial changed",
        ):
            triage.review_uncertain_memory_commit(
                store, proposed, retained_before=retained,
            )

    assert hits == []
    assert store.get(saved.memory_id, saved.scope).content == "original"


@pytest.mark.parametrize("phase", ("after_snapshot", "before_report_constructor"))
def test_reentrant_report_slot_change_is_denied_without_executing(
    tmp_path, monkeypatch, phase,
):
    store, _, saved, retained, proposed = make_case(tmp_path)
    hits = []

    def forbidden(*_args, **_kwargs):
        hits.append("forged field")
        raise AssertionError("changed report slot executed")

    with monkeypatch.context() as patch:
        if phase == "after_snapshot":
            original = triage._snapshot

            def poisoned_snapshot(*args, **kwargs):
                observed = original(*args, **kwargs)
                patch.setattr(
                    triage.MemoryCommitTriage, "disposition", forbidden,
                )
                return observed

            patch.setattr(triage, "_snapshot", poisoned_snapshot)
        else:
            original = triage._digest

            def poisoned_digest(domain, payload):
                result = original(domain, payload)
                if domain == triage._DOMAIN:
                    patch.setattr(
                        triage.MemoryCommitTriage, "report_sha256", forbidden,
                    )
                return result

            patch.setattr(triage, "_digest", poisoned_digest)

        with pytest.raises(triage.MemoryCommitTriageRejected):
            triage.review_uncertain_memory_commit(
                store, proposed, retained_before=retained,
            )

    assert hits == []
    assert store.get(saved.memory_id, saved.scope).revision == 1


def test_original_report_still_reports_manual_only_unchanged(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    report = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED"
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
    assert report.trusted_clock_proven is False
