"""Disconnected closed observation lineage is deterministic and never authority."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.observation_fixture_chain_review as review
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationKind


def _item(content: str, at: int, *, parent=None, scope="local:private",
          source="fixture"):
    return fixture_text_observation(
        content, kind=ObservationKind.TRANSCRIPT, source_id=source,
        privacy_scope=scope, ingested_at_ms=at, parent_sha256=parent,
    )


def _chain():
    first = _item("private synthetic text", 10)
    second = _item("derived synthetic text", 11, parent=first.content_sha256)
    return first, second


def _inspect(items):
    return review.review_disconnected_fixture_chain(
        tuple(items), source_id="fixture", privacy_scope="local:private",
    )


def test_closed_chain_has_deterministic_scope_bound_digest_and_no_authority():
    first, second = _chain()
    checked = _inspect((first, second))
    assert checked == _inspect(_chain())
    assert checked.envelope_count == 2
    assert checked.first_observation_id == first.observation_id
    assert checked.last_observation_id == second.observation_id
    assert len(checked.chain_sha256) == 64
    assert checked.source_authenticated is False
    assert checked.consent_verified is False
    assert checked.dispatch_authorized is False
    assert "private synthetic text" not in repr(checked)
    assert not hasattr(checked, "raw_media")


@pytest.mark.parametrize("change", ["parent", "source", "scope", "time"])
def test_parent_source_scope_and_time_mismatch_fail_closed(change):
    first, second = _chain()
    changes = {
        "parent": {"parent_sha256": "f" * 64},
        "source": {"source_id": "other"},
        "scope": {"privacy_scope": "local:other"},
        "time": {"ingested_at_ms": 10},
    }
    with pytest.raises(
        review.ObservationFixtureChainRejected, match="mismatch",
    ):
        _inspect((first, replace(second, **changes[change])))


def test_open_chain_and_reversed_chain_are_not_claimed_closed():
    first, second = _chain()
    with pytest.raises(review.ObservationFixtureChainRejected, match="mismatch"):
        _inspect((second,))
    with pytest.raises(review.ObservationFixtureChainRejected, match="mismatch"):
        _inspect((second, first))


def test_batch_rejects_non_exact_or_unbounded_input():
    first, _ = _chain()
    for rows in ([], [first], (), (first,) * 257):
        with pytest.raises(
            review.ObservationFixtureChainRejected, match="exact bounded",
        ):
            review.review_disconnected_fixture_chain(
                rows, source_id="fixture", privacy_scope="local:private",
            )


def test_reflective_field_change_during_chain_digest_fails(monkeypatch):
    first, second = _chain()
    calls = []

    def modify(data):
        calls.append(data)
        object.__setattr__(first, "privacy_scope", "local:other")
        raise AssertionError("substituted chain digest must not execute")

    monkeypatch.setattr(review.hashlib, "sha256", modify)
    with pytest.raises(
        review.ObservationFixtureChainRejected,
        match="digest implementation changed",
    ):
        _inspect((first, second))
    assert calls == []


@pytest.mark.parametrize("name", review._DENIALS)
def test_premonkeypatched_authority_descriptor_fails_before_hash(
    monkeypatch, name,
):
    fixtures = _chain()
    monkeypatch.setattr(
        review.DisconnectedObservationChainReview,
        name, property(lambda _: False),
    )

    def impossible(*_args, **_kwargs):
        pytest.fail("hashing executed after result authority definition changed")

    monkeypatch.setattr(review.hashlib, "sha256", impossible)
    with pytest.raises(
        review.ObservationFixtureChainRejected, match="implementation changed",
    ):
        _inspect(fixtures)


def test_result_denial_callback_cannot_retarget_digest(monkeypatch):
    original = review.DisconnectedObservationChainReview.__getattribute__

    def retarget(self, name):
        if name == "consent_verified":
            object.__setattr__(self, "chain_sha256", "f" * 64)
            return False
        return original(self, name)

    monkeypatch.setattr(
        review.DisconnectedObservationChainReview,
        "__getattribute__", retarget,
    )
    # A changed result lookup hook is rejected before constructing output.
    with pytest.raises(
        review.ObservationFixtureChainRejected, match="implementation changed",
    ):
        _inspect(_chain())
