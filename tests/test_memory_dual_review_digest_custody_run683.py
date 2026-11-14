"""The Memory dual-review reconciliation digest has independent fixed custody.

A local row and two independent SQLite reviews are still not actor consent,
writer attribution or retry authority. These fixtures never execute actions.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

import ark.memory.ambiguous_commit_pair_review as pair


@pytest.mark.parametrize(
    "replacement",
    (
        "hashlib_module",
        "json_module",
        "sha256",
        "json_dumps",
        "domain",
        "equal_domain_replacement",
    ),
)
def test_substituted_dual_review_digest_rejected_before_private_sqlite(
    tmp_path, monkeypatch, replacement,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    calls: list[str] = []

    def forbidden(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("untrusted digest/SQLite callback was invoked")

    with monkeypatch.context() as patch:
        if replacement == "hashlib_module":
            patch.setattr(pair, "hashlib", object())
        elif replacement == "json_module":
            patch.setattr(pair, "json", object())
        elif replacement == "sha256":
            patch.setattr(pair.hashlib, "sha256", forbidden)
        elif replacement == "json_dumps":
            patch.setattr(pair.json, "dumps", forbidden)
        elif replacement == "domain":
            patch.setattr(pair, "_DOMAIN", b"untrusted-reconciliation-domain")
        else:
            replacement_domain = bytes(bytearray(pair._DOMAIN))
            assert replacement_domain == pair._DOMAIN
            assert replacement_domain is not pair._DOMAIN
            patch.setattr(pair, "_DOMAIN", replacement_domain)
        patch.setattr(type(store), "_connect_readonly", forbidden)
        with pytest.raises(
            pair.MemoryAmbiguityPairRejected,
            match="reconciliation digest implementation or domain changed",
        ):
            pair.review_memory_ambiguous_commit_pair(
                store, proposed, retained=retained,
            )

    assert calls == []
    report = pair.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert report.caller_commit_authenticated is False
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.trusted_clock_verified is False
