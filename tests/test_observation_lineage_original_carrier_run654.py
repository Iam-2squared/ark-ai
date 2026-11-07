"""Observation lineage diagnostics refuse replaced result hooks before reads.

Synthetic content digests are local fixtures, not source authenticity,
permission for capture or access, or a claim of verified external history.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

import ark.observation_lineage_review as lineage
from ark.observations import ObservationEnvelope, ObservationKind

_FIELDS = (
    "privacy_scope", "checked_at_ms", "observation_count", "lineage_digest",
)
_DENIALS = (
    "media_capture_authorized", "disclosure_authorized",
    "dispatch_authorized",
)
_HOOKS = ("__init__", "__getattribute__", "__getattr__")
_ATTACKS = _FIELDS + _DENIALS + _HOOKS


def _fixture():
    return (ObservationEnvelope(
        ObservationKind.TEXT, "synthetic-source", "fixture:local",
        "private-fixture", 100, "a" * 64,
    ),)


def _review():
    return lineage.review_synthetic_observation_lineage(
        _fixture(), privacy_scope="private-fixture", now_ms=110, max_age_ms=20,
    )


def _install(monkeypatch, name, hits):
    def poisoned(*_args, **_kwargs):
        hits.append(name)
        raise AssertionError("untrusted result getter or constructor executed")

    replacement = (
        property(poisoned) if name in _FIELDS + _DENIALS else poisoned
    )
    monkeypatch.setattr(
        lineage.SyntheticObservationLineageWitness,
        name, replacement, raising=False,
    )


@pytest.mark.parametrize("name", _ATTACKS)
def test_preinstalled_lineage_result_hook_never_reads_private_window(
    monkeypatch, name,
):
    hits = []
    _install(monkeypatch, name, hits)

    def forbidden_window(*_args, **_kwargs):
        raise AssertionError("private window accessed before result preflight")

    monkeypatch.setattr(lineage, "ObservationWindowReview", forbidden_window)
    with pytest.raises(
        lineage.SyntheticObservationLineageRejected,
        match="result changed: authority",
    ):
        _review()
    assert hits == []


@pytest.mark.parametrize("name", (
    "privacy_scope", "lineage_digest", "__init__", "dispatch_authorized",
))
def test_digest_guard_blocks_serialization_callback_before_result_code(
    monkeypatch, name,
):
    hits = []
    serialized = []
    original = lineage.json.dumps

    def serialized_then_swap(value, *args, **kwargs):
        payload = original(value, *args, **kwargs)
        if type(value) is tuple and value and value[0] == 1:
            serialized.append(1)
            _install(monkeypatch, name, hits)
        return payload

    monkeypatch.setattr(lineage.json, "dumps", serialized_then_swap)
    # The import-time digest implementation is pinned before private reads;
    # the injected serializer cannot run and cannot install result code.
    with pytest.raises(
        lineage.SyntheticObservationLineageRejected,
        match="digest implementation changed",
    ):
        _review()
    assert serialized == []
    assert hits == []


def test_inherited_allocation_hook_is_checked_in_fresh_interpreter():
    # Modifying inherited __new__ can permanently poison CPython tp_new.
    script = textwrap.dedent("""
        import ark.observation_lineage_review as lineage
        from ark.observations import ObservationEnvelope, ObservationKind

        envelopes = (ObservationEnvelope(
            ObservationKind.TEXT, "synthetic-source", "fixture:local",
            "private-fixture", 100, "a" * 64,
        ),)
        hits = []

        def poisoned(*args, **kwargs):
            hits.append("new")
            raise AssertionError("allocation hook executed")

        lineage.SyntheticObservationLineageWitness.__new__ = staticmethod(poisoned)
        try:
            lineage.review_synthetic_observation_lineage(
                envelopes, privacy_scope="private-fixture",
                now_ms=110, max_age_ms=20,
            )
        except lineage.SyntheticObservationLineageRejected as exc:
            assert "result changed: authority" in str(exc)
        else:
            raise AssertionError("untrusted constructor accepted")
        assert not hits
    """)
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True,
        check=False, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_original_lineage_remains_deterministic_and_denial_only():
    first = _review()
    assert first == _review()
    assert first.observation_count == 1
    assert first.media_capture_authorized is False
    assert first.disclosure_authorized is False
    assert first.dispatch_authorized is False
