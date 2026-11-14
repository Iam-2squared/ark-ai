"""Synthetic authority claims must never reach substituted digest/parser code.

These are disconnected, non-authorizing local fixtures only.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest

from ark.agency import synthetic_authority_boundary_review as mod


def _claims():
    return mod.SyntheticAuthorityClaims(
        "private-issuer", "private-subject", "tools_" + "a" * 64,
        "bound_" + "b" * 64, "c" * 64, 100, 200,
    )


def _observations():
    return mod.SyntheticAuthorityObservations(*(["unknown"] * 6))


@pytest.mark.parametrize("surface", (
    "hash_module", "hash_callback", "json_module", "json_callback",
    "hex_regex", "issuer_regex", "bound_regex", "registry_regex",
    "states", "domain", "max_ms",
))
def test_private_authority_evidence_never_reaches_substituted_helpers(
    monkeypatch, surface,
):
    claims, observations = _claims(), _observations()
    called = []

    def hostile(*_args, **_kwargs):
        called.append(surface)
        raise AssertionError("hostile code must never observe claim data")

    with monkeypatch.context() as patch:
        if surface == "hash_module":
            patch.setattr(mod, "hashlib", SimpleNamespace(sha256=hostile))
        elif surface == "hash_callback":
            patch.setattr(mod.hashlib, "sha256", hostile)
        elif surface == "json_module":
            patch.setattr(mod, "json", SimpleNamespace(dumps=hostile))
        elif surface == "json_callback":
            patch.setattr(mod.json, "dumps", hostile)
        elif surface == "hex_regex":
            patch.setattr(mod, "_HEX", re.compile(".*"))
        elif surface == "issuer_regex":
            patch.setattr(mod, "_ID", re.compile(".*"))
        elif surface == "bound_regex":
            patch.setattr(mod, "_BOUND", re.compile(".*"))
        elif surface == "registry_regex":
            patch.setattr(mod, "_REGISTRY", re.compile(".*"))
        elif surface == "states":
            patch.setattr(mod, "_STATES", frozenset(("caller_claimed",)))
        elif surface == "domain":
            patch.setattr(mod, "_DOMAIN", bytes(bytearray(mod._DOMAIN)))
        else:
            patch.setattr(mod, "_MAX_MS", mod._MAX_MS - 1)
        with pytest.raises(
            mod.SyntheticAuthorityRejected,
            match="digest or parser dependencies changed",
        ):
            mod.review_synthetic_authority_gaps(claims, observations)
    assert called == []
    assert claims.issuer_claim == "private-issuer"
    assert observations.human_consent == "unknown"


def test_original_authority_review_still_denies_all_execution():
    result = mod.review_synthetic_authority_gaps(_claims(), _observations())
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert result.human_consent_verified is False
    assert len(result.blockers) == 6
