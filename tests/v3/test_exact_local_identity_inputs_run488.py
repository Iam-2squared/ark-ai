"""Local V3 manifest identifiers require exact built-in string carriers.

Offline only: invalid identifiers are denied before file enumeration or hashing.
This test grants no GPU, Candidate, approval, or model access.
"""

from __future__ import annotations

import pytest

import ark.learning.identity as identity


class StringAlias(str):
    """Untrusted string subclass with an otherwise valid identifier."""


@pytest.mark.parametrize(
    ("field", "bad", "expected"),
    [
        ("model_id", StringAlias("Qwen/Qwen3-4B-Instruct-2507"), "model ID"),
        ("model_id", b"Qwen/Qwen3-4B-Instruct-2507", "model ID"),
        ("revision", StringAlias("a" * 40), "40-hex"),
        ("revision", 123, "40-hex"),
    ],
)
def test_hf_snapshot_rejects_nonexact_identity_before_file_reads(
    tmp_path, monkeypatch, field, bad, expected,
):
    def unexpected_scan(*args, **kwargs):
        raise AssertionError("invalid identifier reached file enumeration")

    monkeypatch.setattr(identity, "directory_file_identities", unexpected_scan)
    values = {
        "model_id": "Qwen/Qwen3-4B-Instruct-2507",
        "revision": "a" * 40,
    }
    values[field] = bad
    with pytest.raises(ValueError, match=expected):
        identity.build_hf_snapshot_identity(
            tmp_path / "unmaterialized",
            model_id=values["model_id"],
            revision=values["revision"],
            chat_template_probe=tmp_path / "unmaterialized-probe",
        )


@pytest.mark.parametrize(
    ("field", "bad", "expected"),
    [
        ("git_revision", StringAlias("b" * 40), "40-hex"),
        ("git_revision", 123, "40-hex"),
        ("role", StringAlias("quantizer"), "tool role"),
        ("role", 123, "tool role"),
    ],
)
def test_tool_identity_rejects_nonexact_identity_before_file_reads(
    tmp_path, monkeypatch, field, bad, expected,
):
    def unexpected_hash(*args, **kwargs):
        raise AssertionError("invalid identifier reached file hashing")

    monkeypatch.setattr(identity, "file_identity", unexpected_hash)
    values = {"git_revision": "b" * 40, "role": "quantizer"}
    values[field] = bad
    with pytest.raises(ValueError, match=expected):
        identity.build_tool_identity(
            tmp_path / "unmaterialized-tool",
            git_revision=values["git_revision"],
            role=values["role"],
        )
