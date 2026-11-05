"""Manual-only uncertain Memory COMMIT review never runs a replaced initializer.

These checks use only disposable local SQLite fixture data. A matched row
is not caller attribution, durable consent, or automatic WRITE retry.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

import ark.memory.postcommit_uncertainty_review as triage


@pytest.mark.parametrize(
    "phase",
    ("preinstalled", "during_snapshot", "during_close", "during_report_digest"),
)
def test_uncertain_commit_receipt_constructor_cannot_be_substituted(
    tmp_path, monkeypatch, phase,
):
    store, scope, saved, retained, proposed = make_case(tmp_path)
    attempted = []

    def forbidden(*_args, **_kwargs):
        attempted.append("forged constructor ran")
        raise AssertionError("forged triage initializer must not execute")

    with monkeypatch.context() as patch:
        if phase == "preinstalled":
            patch.setattr(triage.MemoryCommitTriage, "__init__", forbidden)

            def no_sqlite():
                raise AssertionError("preinstalled forged initializer must fail before SQLite")

            patch.setattr(store, "_connect_readonly", no_sqlite)
        elif phase == "during_snapshot":
            native = triage._snapshot

            def after_snapshot(*args, **kwargs):
                result = native(*args, **kwargs)
                patch.setattr(triage.MemoryCommitTriage, "__init__", forbidden)
                return result

            patch.setattr(triage, "_snapshot", after_snapshot)
        elif phase == "during_close":
            native_closing = triage.closing

            def after_close(conn):
                wrapped = native_closing(conn)

                class AfterClose:
                    def __enter__(self):
                        return wrapped.__enter__()

                    def __exit__(self, *args):
                        result = wrapped.__exit__(*args)
                        patch.setattr(triage.MemoryCommitTriage, "__init__", forbidden)
                        return result

                return AfterClose()

            patch.setattr(triage, "closing", after_close)
        else:
            native_digest = triage._digest

            def after_report_digest(domain, payload):
                digest = native_digest(domain, payload)
                if domain == triage._DOMAIN:
                    patch.setattr(triage.MemoryCommitTriage, "__init__", forbidden)
                return digest

            patch.setattr(triage, "_digest", after_report_digest)

        with pytest.raises(triage.MemoryCommitTriageRejected):
            triage.review_uncertain_memory_commit(
                store, proposed, retained_before=retained,
            )

    assert attempted == []
    assert store.get(saved.memory_id, scope).content == "original"
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_unchanged_local_commit_triage_remains_manual_only(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    receipt = triage.review_uncertain_memory_commit(
        store, proposed, retained_before=retained,
    )
    assert receipt.disposition == "LOCAL_UNCHANGED"
    assert receipt.automatic_retry_authorized is False
    assert receipt.write_authorized is False
    assert receipt.caller_attribution_proven is False
    assert receipt.trusted_clock_proven is False
