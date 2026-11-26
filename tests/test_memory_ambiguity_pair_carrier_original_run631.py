"""Manual Memory ambiguity receipts reject class-level executable substitutions.

This suite never retries or attributes a COMMIT. All database handles are local
read-only observations of disposable SQLite fixtures; no external effects.
"""

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as pair


class ForbiddenDescriptor:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("executed")
        raise AssertionError("counterfeit field descriptor must not execute")


def _review(case):
    store, _, _, retained, proposed = case
    return pair.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )


@pytest.mark.parametrize("name", pair._RESULT_FIELDS)
def test_result_field_descriptor_denied_before_sqlite(tmp_path, monkeypatch, name):
    case = make_case(tmp_path)
    store = case[0]
    calls = []

    def forbidden_read(*args, **kwargs):
        raise AssertionError("forged class must be refused before SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(pair.MemoryAmbiguityPair, name, ForbiddenDescriptor(calls))
        patch.setattr(type(store), "_connect_readonly", forbidden_read)
        with pytest.raises(pair.MemoryAmbiguityPairRejected, match="authority changed"):
            _review(case)
    assert calls == []


@pytest.mark.parametrize(
    ("child", "name"),
    (("triage", "report_sha256"), ("outcome", "review_sha256")),
)
def test_child_field_descriptor_denied_before_sqlite(
    tmp_path, monkeypatch, child, name,
):
    case = make_case(tmp_path)
    store = case[0]
    cls = pair._TRIAGE if child == "triage" else pair._OUTCOME
    calls = []

    def forbidden_read(*args, **kwargs):
        raise AssertionError("forged child field must be refused before SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(cls, name, ForbiddenDescriptor(calls))
        patch.setattr(type(store), "_connect_readonly", forbidden_read)
        with pytest.raises(pair.MemoryAmbiguityPairRejected, match="authority changed"):
            _review(case)
    assert calls == []


@pytest.mark.parametrize("name", ("__init__", "__getattribute__", "__getattr__"))
def test_result_hook_denied_without_running_hook(tmp_path, monkeypatch, name):
    case = make_case(tmp_path)
    calls = []

    def injected(*args, **kwargs):
        calls.append("executed")
        raise AssertionError("counterfeit result hook must not execute")

    with monkeypatch.context() as patch:
        patch.setattr(pair.MemoryAmbiguityPair, name, injected, raising=False)
        with pytest.raises(pair.MemoryAmbiguityPairRejected, match="authority changed"):
            _review(case)
    assert calls == []


def test_child_callback_cannot_install_late_result_slot(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = pair._TRIAGE_FN
    calls = []

    with monkeypatch.context() as patch:
        def mutate_after_triage(*args, **kwargs):
            result = original(*args, **kwargs)
            patch.setattr(
                pair.MemoryAmbiguityPair, "reconciliation_sha256",
                ForbiddenDescriptor(calls),
            )
            return result

        patch.setattr(pair, "_TRIAGE_FN", mutate_after_triage)
        patch.setattr(pair.triage_module, "review_uncertain_memory_commit",
                      mutate_after_triage)
        with pytest.raises(pair.MemoryAmbiguityPairRejected, match="authority changed"):
            _review(case)
    assert calls == []


def test_original_dual_review_remains_local_and_non_authorizing(tmp_path):
    result = _review(make_case(tmp_path))
    assert result.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert result.caller_commit_authenticated is False
    assert result.automatic_retry_authorized is False
    assert result.write_authorized is False
    assert result.trusted_clock_verified is False
