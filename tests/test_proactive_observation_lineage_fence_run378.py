"""Observation lineage and prepared triggers are correlated without capture."""

import hashlib
import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.observation_lineage_review import SyntheticObservationLineageRejected
from ark.observations import ObservationEnvelope, ObservationKind
from ark.proactive_observation_lineage_fence_review import (
    SyntheticObservationTriggerRejected,
    review_synthetic_observation_trigger,
    synthetic_observation_source_digest,
)
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _envelope(payload: bytes, *, parent=None, source="SENSITIVE-SOURCE", at=90):
    return ObservationEnvelope(
        ObservationKind.TEXT, source, "fixture:text", "local:private",
        at, _digest(payload), parent,
    )


def _fixture(tmp_path: Path):
    root = _envelope(b"private-root")
    child = _envelope(b"private-child", parent=root.content_sha256, at=95)
    policy = SyntheticTriggerPolicy(
        "owner", "private", "event", 1, "policy-v1", 5, 50, 3,
    )
    ledger = SyntheticProactiveLedger(tmp_path / "trigger #1 %.sqlite")
    receipt = ledger.prepare(
        policy, source_digest=synthetic_observation_source_digest(child.source_id),
        observation_digest=child.content_sha256, observed_at_ms=95, now_ms=100,
    )
    return (root, child), child.observation_id, ledger, receipt, policy


def _review(state, **changes):
    envelopes, selected_id, ledger, receipt, policy = state
    kwargs = {
        "privacy_scope": "local:private", "ledger": ledger, "receipt": receipt,
        "policy": policy, "now_ms": 100, "max_age_ms": 10,
    }
    kwargs.update(changes)
    return review_synthetic_observation_trigger(envelopes, selected_id, **kwargs)


def test_parent_chain_and_persisted_trigger_are_diagnostic_only(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state)
    assert result.observation_id == state[1]
    assert result.trigger_id == state[3].trigger_id
    assert result.lineage_digest.startswith("olineage_")
    assert result.trigger_history_digest.startswith("synthetic_triggers_")
    assert result.capture_authorized is False
    assert result.disclosure_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert "SENSITIVE-SOURCE" not in repr(result)


def test_source_identity_hash_is_domain_separated():
    source = synthetic_observation_source_digest("source")
    assert len(source) == 64
    assert source != _digest(b"source")
    assert source == synthetic_observation_source_digest("source")


@pytest.mark.parametrize("bad", ["", "   ", None, 42, True])
def test_source_digest_requires_exact_nonempty_text(bad):
    with pytest.raises(SyntheticObservationTriggerRejected, match="source"):
        synthetic_observation_source_digest(bad)


def test_wrong_selected_observation_id_fails(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[1] = "ob_" + "f" * 64
    with pytest.raises(SyntheticObservationTriggerRejected, match="unique"):
        _review(state)


def test_duplicate_selected_envelopes_denied(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[0] = (state[0][0], state[0][1], state[0][1])
    with pytest.raises(SyntheticObservationTriggerRejected, match="unique"):
        _review(state)


def test_forged_unresolved_parent_is_rejected(tmp_path: Path):
    state = list(_fixture(tmp_path))
    rogue = _envelope(b"private-child", parent="f" * 64, at=95)
    state[0] = (state[0][0], rogue)
    state[1] = rogue.observation_id
    with pytest.raises(SyntheticObservationLineageRejected, match="unresolved"):
        _review(state)


def test_wrong_privacy_scope_rejected(tmp_path: Path):
    with pytest.raises(ValueError, match="scope"):
        _review(_fixture(tmp_path), privacy_scope="local:other")


def test_observation_age_expiry_does_not_allow_trigger(tmp_path: Path):
    with pytest.raises(ValueError, match="age budget"):
        _review(_fixture(tmp_path), now_ms=101)


def test_policy_drift_invalidates_prepared_trigger(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[4] = replace(state[4], policy_revision="policy-v2")
    with pytest.raises(SyntheticTriggerRejected, match="mismatched"):
        _review(state)


def test_source_mismatch_cannot_relabel_trigger(tmp_path: Path):
    state = list(_fixture(tmp_path))
    altered = _envelope(b"private-child", parent=state[0][0].content_sha256, source="other", at=95)
    state[0] = (state[0][0], altered)
    state[1] = altered.observation_id
    with pytest.raises((SyntheticTriggerRejected, SyntheticObservationLineageRejected)):
        _review(state)


def test_retained_trigger_witness_permits_exact_recheck(tmp_path: Path):
    state = _fixture(tmp_path)
    witness = read_proactive_witness(state[2])
    assert _review(state, retained=witness).notification_authorized is False


def test_appended_unrelated_trigger_mid_review_is_denied(tmp_path: Path, monkeypatch):
    import ark.proactive_observation_lineage_fence_review as module

    state = _fixture(tmp_path)
    original = module.review_prepared_trigger_freshness
    count = 0

    def append_after_first(*args, **kwargs):
        nonlocal count
        result = original(*args, **kwargs)
        count += 1
        if count == 1:
            state[2].prepare(
                replace(state[4], definition_id="different"),
                source_digest="c" * 64, observation_digest="d" * 64,
                observed_at_ms=95, now_ms=100,
            )
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", append_after_first)
    with pytest.raises(SyntheticObservationTriggerRejected, match="changed"):
        _review(state)


def test_reflective_envelope_mutation_during_review_denied(tmp_path: Path, monkeypatch):
    import ark.proactive_observation_lineage_fence_review as module

    state = _fixture(tmp_path)
    original = module.review_prepared_trigger_freshness

    def mutate_after_first(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(state[0][1], "content_sha256", "f" * 64)
        return result

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", mutate_after_first)
    with pytest.raises((SyntheticObservationTriggerRejected, SyntheticTriggerRejected)):
        _review(state)


def test_missing_trigger_file_is_never_recreated(tmp_path: Path):
    state = _fixture(tmp_path)
    absent = tmp_path / "absent.sqlite"
    state[2].path = absent
    with pytest.raises(sqlite3.OperationalError):
        _review(state)
    assert not absent.exists()


def test_non_tuple_envelopes_or_non_string_id_denied(tmp_path: Path):
    state = list(_fixture(tmp_path))
    state[0] = list(state[0])
    with pytest.raises(SyntheticObservationTriggerRejected, match="exact"):
        _review(state)
    state[0] = tuple(state[0])
    state[1] = True
    with pytest.raises(SyntheticObservationTriggerRejected, match="exact"):
        _review(state)
